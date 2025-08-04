#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import numpy as np
from scipy.integrate import trapezoid as trapz

if len(sys.argv) < 2:
    print(json.dumps({"error": "No BIN file path provided"}))
    sys.exit(1)

file = sys.argv[1]
if not os.path.exists(file):
    print(json.dumps({"error": f"File not found: {file}"}))
    sys.exit(1)

filesize = os.path.getsize(file)
f = open(file, 'rb')
f.seek(2)

record_length = 0.48
n_samps = int(record_length * 1000 / 4)
sizes = np.array([2, 2, 8, 2, 2, 4, 1, 4, 2])
shapes = np.array([1, 1, 1, 1, 1, 1, 1, 1, n_samps])
col_ind = np.pad(np.cumsum(sizes * shapes), (1, 0))

event_size = np.sum(sizes * shapes)
n_events = int((filesize - 2) / event_size)
chunk_size = 50000
n_loops = int(n_events / chunk_size)

energy_list = []
timestamp_list = []
waveform_list = []

max_pulses = 5000  # limit number of returned waveforms
pulse_count = 0

for loop in range(n_loops + 1):
    if f.tell() < filesize - 2:
        if loop < n_loops:
            a = np.fromfile(f, dtype='uint8', count=chunk_size * event_size)
            blocked_a = a.reshape(int(len(a) / event_size), event_size)
        else:
            a = np.fromfile(f, dtype='uint8')
            blocked_a = a.reshape(int(len(a) / event_size), event_size)

        event_dtype = [
            ('board', np.int16),
            ('channel', np.int16),
            ('time_stamp', np.int64),
            ('energy', np.int16),
            ('energy_short', np.int16),
            ('flags', np.int32),
            ('wavefrom_code', np.int8),
            ('n_samps', np.int32),
            ('waveform', np.int16, n_samps)
        ]

        events = np.zeros(int(len(a) / event_size), dtype=event_dtype)

        for i in range(len(event_dtype)):
            arr = blocked_a[:, col_ind[i]:col_ind[i+1]].astype(event_dtype[i][1])

            if sizes[i] * shapes[i] == 1:
                arr = arr.flatten()
            elif sizes[i] * shapes[i] < 9:
                buffer = np.zeros(len(events), dtype=event_dtype[i][1])
                for b in range(sizes[i]):
                    buffer += (arr[:, b] << (8 * b))
                arr = buffer
            else:
                buffer = np.zeros((len(events), event_dtype[i][2]), dtype=event_dtype[i][1])
                for b in range(event_dtype[i][2]):
                    buffer[:, b] = (arr[:, b * 2] << 0) + (arr[:, b * 2 + 1] << 8)
                arr = buffer

            events[event_dtype[i][0]] = arr

        for i in range(len(events)):
            wf = events['waveform'][i]
            baseline_corrected = np.mean(wf[0:20]) - wf
            energy_list.append(float(trapz(baseline_corrected, dx=0.004)))
            timestamp_list.append(int(events['time_stamp'][i]))

            if pulse_count < max_pulses:
                waveform_list.append(baseline_corrected.tolist())
                pulse_count += 1

output = {
    "energyCH2": energy_list,
    "time_stampCH2": timestamp_list,
    "waveformsCH2": waveform_list
}

print(json.dumps(output))

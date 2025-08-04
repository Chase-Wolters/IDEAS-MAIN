# -*- coding: utf-8 -*-
"""
Created on Wed Apr 10 13:50:26 2024

@author: kjoshi4
"""

### Pacakges ###
import numpy as np
import matplotlib.pyplot as plt
import os
import sys
from scipy.integrate import trapezoid
import time
import json
from scipy.signal import find_peaks
from scipy.signal import savgol_filter



### Variables ###

## Chase Added## Step 1: Get File Path from MATLAB Argument
if len(sys.argv) < 2:
    print(json.dumps({"error": "No file path provided"}))
    sys.exit(1)

file = sys.argv[1]  # Get file path from MATLAB
if not os.path.isfile(file):
    print(json.dumps({"error": "File not found"}))
    sys.exit(1)

# Extract channel number from filename
base_filename = os.path.basename(file)
try:
    channel_number = "CH" + base_filename.split("CH")[1][0]
except Exception:
    print(json.dumps({"error": "Unable to parse channel number from filename"}))
    sys.exit(1)


timeStart=time.perf_counter()

filesize = os.path.getsize(file)
f = open(file)
f.seek(2)

record_length = 0.992
n_samps = int(record_length*1000/4)     #time in us multiplied by frequency in MHz (9.984*250)
sizes = np.array([2, 2, 8, 2, 2, 4, 1, 4, 2])
shapes = np.array([1, 1, 1, 1, 1, 1, 1, 1, n_samps])
col_ind = np.pad(np.cumsum(sizes*shapes), (1,0))

event_size = np.sum(sizes*shapes)
n_events = int(filesize-2)/event_size
chunk_size = int(5000)
n_loops = int(n_events/chunk_size)

energy = np.zeros(int(n_events))
energy_uncorrected = np.zeros(int(n_events))
time_stamp = np.zeros(int(n_events))

## Chase Added ## print('looping') comment out print statement because of interference with json output

for loop in range(n_loops+1):
    # print(loop)
    if (f.tell()<filesize-2):
        # plt.figure()
        if (loop<n_loops):
            a = np.fromfile(f, dtype = 'uint8', count=chunk_size*event_size)
            blocked_a = a.reshape(int(len(a)/event_size), event_size)
        elif (loop==n_loops):
            a = np.fromfile(f, dtype = 'uint8')
            blocked_a = a.reshape(int(len(a)/event_size), event_size)
            
        event_dtype = [('board', np.int16),
                        ('channel', np.int16),
                        ('time_stamp', np.int64),
                        ('energy', np.int16),
                        ('energy_short', np.int16),
                        ('flags', np.int32),
                        ('wavefrom_code', np.int8),
                        ('n_samps', np.int32),
                        ('waveform', np.int16, n_samps)]
        
        events = np.zeros(int(len(a)/event_size), dtype = event_dtype)
        for i in range(len(event_dtype)):
            arr = blocked_a[:, col_ind[i]:col_ind[i+1]].astype(event_dtype[i][1])
            if (sizes[i]*shapes[i] == 1):
                arr = arr.flatten()
            
            if (sizes[i]*shapes[i]>1 and sizes[i]*shapes[i]<9):
                buffer = np.zeros(len(events), dtype = event_dtype[i][1])
                for b in range(sizes[i]):
                    buffer+= (arr[:, b]<<(8*b))            
                arr = buffer
                    
            if (sizes[i]*shapes[i]>9):
                buffer = np.zeros((len(events),event_dtype[i][2]), dtype = event_dtype[i][1])
                for b in range(event_dtype[i][2]):
                    buffer[:,b]= (arr[:, b*2]<<(8*0))+(arr[:, (b*2)+1]<<(8*1))
                arr = buffer
            
            events[event_dtype[i][0]] = arr
                
        mean = np.mean(events['waveform'][:,:10], axis=1)
        mean_matrix = np.tile(mean, (events['waveform'].shape[1], 1)).transpose()
        corrected_waveform = mean_matrix-events['waveform']
        smooth = savgol_filter(corrected_waveform[:,:], 15, 2, deriv=1)
        
        for i in range(len(events)):
            # time_stamp[i+loop*chunk_size] = events['time_stamp'][i]
            peaks = find_peaks(smooth[i], height = 2.0, distance = 10)
            
            if (len(peaks[0])==1 and peaks[0]<=100):
                energy[i+loop*chunk_size] = trapezoid(corrected_waveform[i], dx=0.004)
                time_stamp[i+loop*chunk_size] = events['time_stamp'][i]
                # plt.plot(corrected_waveform[i])
                
            # else:
            #     plt.plot(corrected_waveform[i])
            #     plt.plot(smooth[i])       
            
            energy_uncorrected[i+loop*chunk_size] = trapezoid(corrected_waveform[i], dx=0.004)

LLD = 0.01
ULD = 800

energy = np.array(energy)
cut_energy = energy[energy>=LLD]
cut_energy = cut_energy[cut_energy<=ULD]
n,bins,flags = plt.hist(cut_energy, bins=3000)
bincenters = 0.5*(bins[1:]+bins[:-1])


# plt.figure()
# energy_uncorrected = np.array(energy_uncorrected)
# cut_energy_uncorrected = energy_uncorrected[energy_uncorrected>=LLD]
# cut_energy_uncorrected = cut_energy_uncorrected[cut_energy_uncorrected<=ULD]
# n_uncorrected,bins_uncorrected,flags = plt.hist(cut_energy_uncorrected, bins=4000)
# bincenters_uncorrected = 0.5*(bins_uncorrected[1:]+bins_uncorrected[:-1])

# Max = np.max(n)
# mean = bincenters[np.argmax(n)]
# print("mean = ", mean)


try:
    output_data = {
        f"energy{channel_number}": energy.tolist(),
        f"time_stamp{channel_number}": time_stamp.tolist(),
    }
    print(json.dumps(output_data))
    
except Exception as e:
    print(json.dumps({"error": f"Failed to generate JSON output: {str(e)}"}))
    sys.exit(1)


# Step 2: Return JSON Output for MATLAB
#output_data = {
 #   "energyCH2": energy.tolist(),
  #  "time_stampCH2": time_stamp.tolist(),
#}

#print(json.dumps(output_data))  # MATLAB will capture this output

timeStop=time.perf_counter()
# print(timeStop-timeStart)

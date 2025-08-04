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
# from scipy.integrate import trapz
import sys
# from scipy.integrate import trapz
import time
# from scipy.signal import find_peaks
# from scipy.signal import savgol_filter
import json # allow variables to be passed to MATLAB


### Variables ###

## Chase Added ## Step 1: Get File Path from MATLAB Argument
if len(sys.argv) < 2:
    print(json.dumps({"error": "No file path provided"}))
    sys.exit(1)

file = sys.argv[1]  # Get file path from MATLAB
if not os.path.isfile(file):
    print(json.dumps({"error": "File not found"}))
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
chunk_size = int(10)
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
                
        # mean = np.mean(events['waveform'][:,:10], axis=1)
        # mean_matrix = np.tile(mean, (events['waveform'].shape[1], 1)).transpose()
        # corrected_waveform = mean_matrix-events['waveform']
        # smooth = savgol_filter(corrected_waveform[:,:], 15, 2, deriv=1)
        
        for i in range(len(events)):
            time_stamp[i+loop*chunk_size] = events['time_stamp'][i]
            # peaks = find_peaks(smooth[i], height = 2.0, distance = 10)
            
            # if (len(peaks[0])==1 and peaks[0]<=50):
            #     energy[i+loop*chunk_size] = trapz(corrected_waveform[i], dx=0.004)
            #     time_stamp[i+loop*chunk_size] = events['time_stamp'][i]
            #     # plt.plot(corrected_waveform[i])
                
            # # if (len(peaks[0])!=1):
            # #     plt.plot(corrected_waveform[i])
            # #     plt.plot(smooth[i])       
            
            # energy_uncorrected[i+loop*chunk_size] = trapz(corrected_waveform[i], dx=0.004)

LLD = 0.2
ULD = 400

energy = np.array(energy)
cut_energy = energy[energy>=LLD]
cut_energy = cut_energy[cut_energy<=ULD]
n,bins,flags = plt.hist(cut_energy, bins=4000)
bincenters = 0.5*(bins[1:]+bins[:-1])

## Chase Added ## Step 2: Return JSON Output for MATLAB
output_data = {
    "time_stampCH0": time_stamp.tolist()
}

print(json.dumps(output_data))  # MATLAB will capture this output


#outt = [time_stamp, energy]
#np.savetxt('C:/Users/kjoshi4/Documents/3x8 NaI outside box heavy shield/Ch2_active_bkg.csv',np.transpose(outt),delimiter = ',',fmt='%s')
#np.savetxt('C:/Users/kjoshi4/Documents/3x8 NaI outside box heavy shield/Ch0_active_bkg.csv',np.transpose(time_stamp),delimiter = ',',fmt='%s')
#np.savetxt('C:/Users/kjoshi4/Documents/3x8 NaI outside box heavy shield/Ch0_active_bkg.csv',np.transpose(time_stamp),delimiter = ',',fmt='%s')


timeStop=time.perf_counter()
# print(timeStop-timeStart)
# print(timeStop-timeStart)

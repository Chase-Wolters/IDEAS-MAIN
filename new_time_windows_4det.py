# -*- coding: utf-8 -*-
"""
Created on Mon Mar 31 20:45:38 2025

@author: kjoshi4
"""

"""
Created on Tue Mar  4 11:28:36 2025

@author: kjoshi4
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import os
import sys
import json

def time_windows(NG_time, detector1):
    detector1_energy = np.array(detector1[:,1])
    detector1_time = np.array(detector1[:,0])

    detector1_time = detector1_time[detector1_energy>0]
    detector1_energy = detector1_energy[detector1_energy>0]

    NG_time_400 = NG_time+400*1e6
    NG_time_1000 = NG_time+1000*1e6
    NG_time_2000 = NG_time+2000*1e6
    NG_time_3000 = NG_time+3000*1e6

    bin_boundaries = np.concatenate((NG_time.transpose(), NG_time_400.transpose(), NG_time_1000.transpose(), NG_time_2000.transpose(), NG_time_3000.transpose()))
    bin_boundaries = bin_boundaries.reshape((5, len(NG_time))).transpose()
    bin_boundaries = bin_boundaries.flatten()

    bins_0_400 = []
    bins_400_1000 = []
    bins_1000_2000 = []
    bins_2000_3000 = []
    bins_3000_5000 = []

    for i in range(len(NG_time)+1):
        bins_0_400.append((i*5)+1)
        bins_400_1000.append((i*5)+2)
        bins_1000_2000.append((i*5)+3)
        bins_2000_3000.append((i*5)+4)
        bins_3000_5000.append(i*5)
            
    if detector1_time[0]<NG_time[0]: 
        bins_0_400.pop(-1)
        bins_400_1000.pop(-1)
        bins_1000_2000.pop(-1)
        bins_2000_3000.pop(-1)
        bins_3000_5000.pop(0)

    set_0_400 = set(bins_0_400)
    set_400_1000 = set(bins_400_1000)
    set_1000_2000 = set(bins_1000_2000)
    set_2000_3000 = set(bins_2000_3000)
    set_3000_5000 = set(bins_3000_5000)

    det_bins = np.digitize(detector1_time, bin_boundaries)
    
    index_0_400 = [i for i,e in enumerate(det_bins) if e in set_0_400]
    index_400_1000 = [i for i,e in enumerate(det_bins) if e in set_400_1000]
    index_1000_2000 = [i for i,e in enumerate(det_bins) if e in set_1000_2000]
    index_2000_3000 = [i for i,e in enumerate(det_bins) if e in set_2000_3000]
    index_3000_5000 = [i for i,e in enumerate(det_bins) if e in set_3000_5000]
    
    # index_thermal = np.concatenate((index_400_1000, index_1000_2000, index_2000_3000, index_3000_5000))

    return(detector1_energy, detector1_time, [index_0_400, index_400_1000, index_1000_2000, index_2000_3000, index_3000_5000])

def calibration(energy, channel):
    poly = np.polyfit(channel, energy, 2)
    return np.poly1d(poly)

# NG = np.genfromtxt('C:/Users/kjoshi4/Documents/3x8 NaI outside box heavy shield 4 detector paper cargo/Ch0_active_bkg_surround.csv', delimiter = ',')
# det1 = np.genfromtxt('C:/Users/kjoshi4/Documents/3x8 NaI outside box heavy shield 4 detector paper cargo/Ch1_active_bkg_surround.csv', delimiter = ',')
# det2 = np.genfromtxt('C:/Users/kjoshi4/Documents/3x8 NaI outside box heavy shield 4 detector paper cargo/Ch2_active_bkg_surround.csv', delimiter = ',')
# det3 = np.genfromtxt('C:/Users/kjoshi4/Documents/3x8 NaI outside box heavy shield 4 detector paper cargo/Ch3_active_bkg_surround.csv', delimiter = ',')
# det4 = np.genfromtxt('C:/Users/kjoshi4/Documents/3x8 NaI outside box heavy shield 4 detector paper cargo/Ch4_active_bkg_surround.csv', delimiter = ',')

## Chase adjusted to pass variables from matlab
# ensure JSON file is passed from MATLAB
if len(sys.argv) < 2:
    print(json.dumps({"error": "No JSON file provided"}))
    sys.exit(1)

json_file = sys.argv[1]

# open and load JSON file
try:
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    # extracts the NG timestamp used in time_windows function
    if "time_stampCH0" not in data:
        raise KeyError("Missing time_stampCH0 from input JSON")
    NG_time = np.array(data["time_stampCH0"]) # assign NG_time

    # Calibration file and settings
    cal_file = 'C:\\Users\\cwolt\\Shared with me\\IDEAS\\3x8 NaI outside box heavy shield 4 detector paper cargo\\calibration detector side paper.csv'
    cal_option = 'contraband'  # Change to 'contraband' for melamine data
    col = 1
    energies = np.genfromtxt(cal_file, usecols=0, skip_header=2, delimiter=',')
    col = int(col)

    if cal_option == 'active_bkg':
        ch1 = np.genfromtxt(cal_file, usecols=col, skip_header=2, delimiter=',')
        ch2 = np.genfromtxt(cal_file, usecols=col+1, skip_header=2, delimiter=',')
        ch3 = np.genfromtxt(cal_file, usecols=col+2, skip_header=2, delimiter=',')
        ch4 = np.genfromtxt(cal_file, usecols=col+3, skip_header=2, delimiter=',')
    elif cal_option == 'contraband':
        ch1 = np.genfromtxt(cal_file, usecols=col+6, skip_header=2, delimiter=',')
        ch2 = np.genfromtxt(cal_file, usecols=col+7, skip_header=2, delimiter=',')
        ch3 = np.genfromtxt(cal_file, usecols=col+8, skip_header=2, delimiter=',')
        ch4 = np.genfromtxt(cal_file, usecols=col+9, skip_header=2, delimiter=',')

    # store channel calibration in a list
    ch_cal = [ch1, ch2, ch3, ch4]

    # Final output dictionary
    output_data = {}

    # loops over all energy and time_stamp channels CH1-CH4
    for ch in range(1, 5):
        energy_key = f"energyCH{ch}"
        time_key = f"time_stampCH{ch}"

        if energy_key in data and time_key in data: # ensures energy and time_stamp are in JSON file
            det = np.column_stack((data[time_key], data[energy_key])) # combines time & energy
            energy, _, indices = time_windows(NG_time, det) # calls time_windows function outputs energy, time_stamp, and a list of time windows
            thermal = energy  # Use all energy values temporarily

            cal_func = calibration(energies, ch_cal[ch - 1]) # calls calibration function and returns energy, ch_cal[ch - 1] assigns corresponding calibration index
            calibrated = cal_func(thermal) 

            output_data[f"energyCH{ch}_cal"] = calibrated.tolist()
            output_data[f"coeffCH{ch}_cal"] = cal_func.coefficients.tolist()

    print(json.dumps(output_data))

except Exception as e:
    print(json.dumps({"error": f"Processing failed: {str(e)}"}))
    sys.exit(1)

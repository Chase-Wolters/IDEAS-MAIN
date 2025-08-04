import numpy as np
import json
import sys
from scipy.io import loadmat

def time_windows(NG_time, detector1):
    detector1_energy = np.array(detector1[:, 1])
    detector1_time = np.array(detector1[:, 0])

    detector1_time = detector1_time[detector1_energy > 0]
    detector1_energy = detector1_energy[detector1_energy > 0]

    NG_time_400 = NG_time + 400 * 1e6
    NG_time_1000 = NG_time + 1000 * 1e6
    NG_time_2000 = NG_time + 2000 * 1e6
    NG_time_3000 = NG_time + 3000 * 1e6

    bin_boundaries = np.concatenate((NG_time.T, NG_time_400.T, NG_time_1000.T, NG_time_2000.T, NG_time_3000.T))
    bin_boundaries = bin_boundaries.reshape((5, len(NG_time))).T.flatten()

    bins = {k: [] for k in ["0_400", "400_1000", "1000_2000", "2000_3000", "3000_5000"]}

    for i in range(len(NG_time) + 1):
        bins["3000_5000"].append(i * 5)
        bins["0_400"].append(i * 5 + 1)
        bins["400_1000"].append(i * 5 + 2)
        bins["1000_2000"].append(i * 5 + 3)
        bins["2000_3000"].append(i * 5 + 4)

    if detector1_time[0] < NG_time[0]:
        for k in ["0_400", "400_1000", "1000_2000", "2000_3000"]:
            bins[k].pop(-1)
        bins["3000_5000"].pop(0)

    sets = {k: set(v) for k, v in bins.items()}
    det_bins = np.digitize(detector1_time, bin_boundaries)
    indices = {k: [i for i, e in enumerate(det_bins) if e in sets[k]] for k in sets}

    indices["thermal"] = np.concatenate((
        indices["400_1000"], indices["1000_2000"],
        indices["2000_3000"], indices["3000_5000"]
    ))

    return detector1_energy, detector1_time, indices

def calibration(energy, channel):
    # Remove NaNs and match lengths
    energy = np.array(energy)
    channel = np.array(channel)

    # Match shape
    min_len = min(len(energy), len(channel))
    energy = energy[:min_len]
    channel = channel[:min_len]

    # Remove pairs with NaNs
    mask = ~np.isnan(energy) & ~np.isnan(channel)
    energy = energy[mask]
    channel = channel[mask]

    if len(energy) < 3:
        raise ValueError("Too few valid calibration points after cleaning.")

    poly = np.polyfit(channel, energy, 2)
    return np.poly1d(poly)

def concatenate_params(e1, e2, i1, i2, w):
    return np.concatenate((e1[i1[w]], e2[i2[w]]))

def main():
    if len(sys.argv) < 2: # checks for mat file passed from MATLAB
        print(json.dumps({"error": "No .mat file path provided"}))
        sys.exit(1)

    mat_path = sys.argv[1] # assigns mat file path
    try:
        data = loadmat(mat_path) # loads in data
    except Exception as e:
        print(json.dumps({"error": f"Could not load .mat file: {str(e)}"}))
        sys.exit(1)

    NG = np.squeeze(data["time_stampCH0"]) # assigns TimestampCH0 to NG for comparison across detectors
    ch_keys = [(f"energyCH{i}", f"time_stampCH{i}") for i in range(1, 5)] # creates a list of tuples for channel keys 

    cal_file = "C:\\Users\\cwolt\\SynologyDrive\\ContrabandANFO_FrontOfNaI\\calibration Contraband ANFO Front Of NaI.csv" # update for different calibration files
    
    try:
        # Use genfromtxt to handle blank or non-numeric cells safely
        cal_data = np.genfromtxt(cal_file, delimiter=',', skip_header=2, filling_values=np.nan, invalid_raise=False) # reads in calibration valeus 
        cal_data = cal_data[~np.isnan(cal_data).any(axis=1)]  # Remove rows with NaNs - was causing errors

        cal_end = np.genfromtxt(cal_file, delimiter=',', skip_header=13, filling_values=np.nan, invalid_raise=False)
        cal_end = cal_end[~np.isnan(cal_end).any(axis=1)]

    except Exception as e: # catches error if calibration file is incorrect
        print(json.dumps({"error": f"Failed to load calibration CSV: {str(e)}"}))
        sys.exit(1)

    energies = cal_data[:, 0] # initializes dictionary of output values for JSON
    output = {}

    for i, (e_key, t_key) in enumerate(ch_keys): # loop through each channel to 
        if e_key not in data or t_key not in data:
            continue

        E = np.squeeze(data[e_key]) # extracts and flattens the energy and timestamp arrays 
        T = np.squeeze(data[t_key])
        det_30 = np.column_stack((T[T < 1.8e15], E[T < 1.8e15])) # creates 2 column array for 30-60 minute interval
        det_30_60 = np.column_stack((T[(T > 1.8e15) & (T < 3.6e15)], E[(T > 1.8e15) & (T < 3.6e15)]))
        
        # Chase added: lines 111-116 
        e1, _, idx1 = time_windows(NG[NG < 1.8e15], det_30) # calling time windows function for 30-60 minute window
        e2, _, idx2 = time_windows(NG[(NG > 1.8e15) & (NG < 3.6e15)], det_30_60)

        coeff_start = calibration(energies, cal_data[:, i + 1]) # computes calibration functions for the current channel
        coeff_end = calibration(energies, cal_end[:, i + 1])

        e1_cal = coeff_start(e1) # applies to 0–30 min
        e2_cal = coeff_end(e2) # applies to 30–60 min

        e_combined = concatenate_params(e1_cal, e2_cal, idx1, idx2, 'thermal') # combines thermal values from both 30 & 60 minute time windows 

        output[f"energyCH{i+1}_cal"] = e_combined.tolist()
        output[f"coeffCH{i+1}_cal"] = coeff_start.coefficients.tolist()

    print(json.dumps(output))

if __name__ == "__main__":
    main()

% MATLAB Script to load BIN file path and pass it to Python
clc; clear; close all;

%% Step 1: Add BIN Folder Path
binFolder = "C:\Users\cwolt\PycharmProjects\Research\Digitizer\BIN"; % Update with Folder path

% Get list of all BIN files in the folder
binFiles = dir(fullfile(binFolder, '*.BIN'));

% Ensure files exist
if isempty(binFiles)
    error("Error: No BIN files found in the specified folder.");
end

% Initialize output variables
time_stampCH0_act = [];
energyCH2_act = [];
time_stampCH2_act = [];
time_stampCH0_mel = [];
energyCH2_mel = [];
time_stampCH2_mel = [];

% Initialize struct to store data dynamically
dataStruct = struct();

% Define Python executable path
pythonExe = "C:\Users\cwolt\AppData\Local\Programs\Python\Python310\python.exe";

% Define Python script paths for CH0 and CH2
pythonScriptCH0 = "C:\Users\cwolt\PycharmProjects\Research\Digitizer\new_digitizer_data_NG.py";
pythonScriptCH2 = "C:\Users\cwolt\PycharmProjects\Research\Digitizer\new_digitizer_data.py";

%% Step 2: Loop through each BIN file, determine channel type, and execute Python script
for i = 1:length(binFiles)
    binFile = fullfile(binFiles(i).folder, binFiles(i).name);
    fprintf("Processing file: %s\n", binFile);
    
    % Determine whether the file corresponds to CH0 or CH2
    if contains(binFiles(i).name, "CH0", "IgnoreCase", true)
        channel = "CH0";
        pythonScript = pythonScriptCH0;
        fprintf("Detected CH0: %s\n", binFiles(i).name);
    elseif contains(binFiles(i).name, "CH2", "IgnoreCase", true)
        channel = "CH2";
        pythonScript = pythonScriptCH2;
        fprintf("Detected CH2: %s\n", binFiles(i).name);
    else
        warning("Skipping file (does not contain CH0 or CH2): %s", binFiles(i).name);
        continue; % Skip files that don't match
    end

    % Determine whether the file corresponds to active_background or melamine
    if contains(binFiles(i).name, "active_background", "IgnoreCase", true)
        sampleType = "active_background";
    elseif contains(binFiles(i).name, "melamine", "IgnoreCase", true)
        sampleType = "melamine";
    else
        warning("Skipping file (does not contain active_background or melamine): %s", binFiles(i).name);
        continue; % Skip files that don't match
    end

    % Call Python script and pass the file path
    command = sprintf('"%s" "%s" "%s"', pythonExe, pythonScript, binFile);
    [status, result] = system(command);
    
    if status ~= 0
        warning("Python script execution failed for file: %s\nError: %s", binFiles(i).name, result);
        continue;
    end

    % Step 3: Parse JSON Output from Python
        try
        data = jsondecode(result);  % Convert JSON string to MATLAB structure

        if channel == "CH0"
            if sampleType == "active_background"
                time_stampCH0_act = [time_stampCH0_act; data.time_stampCH0];
            else
                time_stampCH0_mel = [time_stampCH0_mel; data.time_stampCH0];
            end
        
        elseif channel == "CH2"
            if sampleType == "active_background"
                energyCH2_act = [energyCH2_act; data.energyCH2];
                time_stampCH2_act = [time_stampCH2_act; data.time_stampCH2];
            else
                energyCH2_mel = [energyCH2_mel; data.energyCH2];
                time_stampCH2_mel = [time_stampCH2_mel; data.time_stampCH2];
            end
        end

    catch ME
        warning("Error parsing JSON output for file: %s. Skipping...", binFiles(i).name);
        disp(ME.message);
        continue;
    end
end
disp("Data imported successfully into MATLAB!");

energyCH2_mel(1:10)
energyCH2_act(1:10)
time_stampCH2_mel(1:10)
time_stampCH2_act(1:10)
time_stampCH0_mel(1:10)
time_stampCH0_act(1:10)

%% Step 3: Pass Energy and Time Stamp variables into new_time_windows_det.py
% Define path to time windows script
pythonScriptWindows = "C:\Users\cwolt\PycharmProjects\Research\Digitizer\new_time_windows_1det.py";

% Structure JSON data with shorter variable names
dataToPass = struct();
dataToPass.time_stampCH0_act = time_stampCH0_act;
dataToPass.energyCH2_act = energyCH2_act;
dataToPass.time_stampCH2_act = time_stampCH2_act;
dataToPass.time_stampCH0_mel = time_stampCH0_mel;
dataToPass.energyCH2_mel = energyCH2_mel;
dataToPass.time_stampCH2_mel = time_stampCH2_mel;

% Save JSON to temporary file
jsonFile = tempname + ".json";
fid = fopen(jsonFile, 'w');
fprintf(fid, jsonencode(dataToPass));
fclose(fid);

% Call Python script with JSON file as input
command = sprintf('"%s" "%s" "%s"', pythonExe, pythonScriptWindows, jsonFile);
[status, result] = system(command);

if status ~= 0
    warning("Python script execution failed for new_time_windows_det.py\nError: %s", result);
else
    disp("Processing complete. Python script executed successfully.");
end

% Parse the JSON output
data = jsondecode(result);

% Plot histograms in MATLAB
figure;
bar(data.bincenters_act, data.counts_act);
title('Active Background Energy Distribution');
xlabel('Energy');
ylabel('Counts');

figure;
bar(data.bincenters_mel, data.counts_mel);
title('Melamine Energy Distribution');
xlabel('Energy');
ylabel('Counts');
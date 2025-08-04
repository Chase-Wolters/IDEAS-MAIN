% MATLAB Script to load BIN file path and pass it to Python
clc; clear; close all;

%% Step 1: Add BIN Folder Path
binFolder = "C:\Users\cwolt\SynologyDrive\SynologyDrive\melamine_5kg_detector_side_paper"; % Update with Folder path

% Get list of all BIN files in the folder
binFiles = dir(fullfile(binFolder, '*.BIN'));

% Ensure files exist
if isempty(binFiles)
    error("Error: No BIN files found in the specified folder.");
end

% Initialize output variables
time_stampCH0 = [];
energyCH1 = [];
time_stampCH1 = [];
energyCH2 = [];
time_stampCH2 = [];
energyCH3 = [];
time_stampCH3 = [];
energyCH4 = [];
time_stampCH4 = [];

% Define Python executable path
pythonExe = "C:\Users\cwolt\AppData\Local\Programs\Python\Python310\python.exe";

% Define Python script paths for CH0 and CHN -referring to any channel
% other than 0
pythonScriptCH0 = "C:\Users\cwolt\PycharmProjects\Research\Digitizer\new_digitizer_data_NG.py";
pythonScriptCHN = "C:\Users\cwolt\PycharmProjects\Research\Digitizer\new_digitizer_data.py";

%% Step 2: Loop through each BIN file, determine channel type, and execute Python script
for i = 1:length(binFiles) % loops through each file in BIN folder, constructs full path
    binFile = fullfile(binFiles(i).folder, binFiles(i).name);
    fprintf("Processing file: %s\n", binFile);

    if contains(binFiles(i).name, "CH0", "IgnoreCase", true) % identifies channel #
        channel = "CH0";
        chNum = 0;
        pythonScript = pythonScriptCH0;
    elseif contains(binFiles(i).name, "CH1", "IgnoreCase", true)
        channel = "CH1";
        chNum = 1;
        pythonScript = pythonScriptCHN;
    elseif contains(binFiles(i).name, "CH2", "IgnoreCase", true)
        channel = "CH2";
        chNum = 2;
        pythonScript = pythonScriptCHN;
    elseif contains(binFiles(i).name, "CH3", "IgnoreCase", true)
        channel = "CH3";
        chNum = 3;
        pythonScript = pythonScriptCHN;
    elseif contains(binFiles(i).name, "CH4", "IgnoreCase", true)
        channel = "CH4";
        chNum = 4;
        pythonScript = pythonScriptCHN;
    else
        warning("Skipping file: %s", binFiles(i).name);
        continue;
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
        data = jsondecode(result); % parse JSON code for each instance

        if strcmp(channel, "CH0") % compares string values then assigns corresponding python variable to MATLAB variable
            time_stampCH0 = [time_stampCH0; data.time_stampCH0];
        else
            energyField = sprintf('energyCH%d', chNum); % dynamically creates variable names. 
            timeField = sprintf('time_stampCH%d', chNum);

            if isfield(data, energyField) && isfield(data, timeField) % matches created field names to var names in data
                % eval( executes string as MATLAB code
                eval(sprintf('%s = [%s; data.%s];', energyField, energyField, energyField)); % properly formats MATLAB variable assignment
                eval(sprintf('%s = [%s; data.%s];', timeField, timeField, timeField));
            else
                warning("Expected fields not found in JSON: %s or %s", energyField, timeField);
                continue;
            end
        end

    catch ME
        warning("Error parsing JSON output: %s. Skipping...", binFiles(i).name);
        disp(ME.message);
        continue;
    end
end

disp("Data imported successfully into MATLAB!");

%% Step 3: Pass Energy and Time Stamp variables into new_time_windows_det.py
% Define path to time windows script
pythonScriptWindows = "C:\Users\cwolt\PycharmProjects\Research\Digitizer\new_time_windows_4det.py";

% Structure JSON data
dataToPass = struct();
dataToPass.time_stampCH0 = time_stampCH0;
dataToPass.energyCH1 = energyCH1;
dataToPass.time_stampCH1 = time_stampCH1;
dataToPass.energyCH2 = energyCH2;
dataToPass.time_stampCH2 = time_stampCH2;
dataToPass.energyCH3 = energyCH3;
dataToPass.time_stampCH3 = time_stampCH3;
dataToPass.energyCH4 = energyCH4;
dataToPass.time_stampCH4 = time_stampCH4;

% Save JSON to file
jsonFile = tempname + ".json"; % create temporary filename
fid = fopen(jsonFile, 'w'); % opens file
fprintf(fid, jsonencode(dataToPass)); % encodes data back to JSON format
fclose(fid);

% Run Python script
command = sprintf('"%s" "%s" "%s"', pythonExe, pythonScriptWindows, jsonFile);
[status, result] = system(command);

if status ~= 0
    warning("Python script execution failed for new_time_windows_4det.py\nError: %s", result);
else
    disp("Processing complete. Python script executed successfully.");
end

% Parse the JSON output
data = jsondecode(result);

% Assign calibrated energy variables directly
if isfield(data, 'energyCH1_cal')
    energyCH1_mel = data.energyCH1_cal;
    fprintf("energyCH1_mel (first 10 entries):\n");
    disp(energyCH1_mel(1:min(10, end)));
end

if isfield(data, 'energyCH2_cal')
    energyCH2_mel = data.energyCH2_cal;
    fprintf("energyCH2_mel (first 10 entries):\n");
    disp(energyCH2_mel(1:min(10, end)));
end

if isfield(data, 'energyCH3_cal')
    energyCH3_mel = data.energyCH3_cal;
    fprintf("energyCH3_mel (first 10 entries):\n");
    disp(energyCH3_mel(1:min(10, end)));
end

if isfield(data, 'energyCH4_cal')
    energyCH4_mel = data.energyCH4_cal;
    fprintf("energyCH4_mel (first 10 entries):\n");
    disp(energyCH4_mel(1:min(10, end)));
end

% Assign calibrated coefficients directly
if isfield(data, 'coeffCH1_cal')
    coeffCH1_mel = data.coeffCH1_cal;
    fprintf("coeffCH1_mel (coefficients):\n");
    disp(coeffCH1_mel);
end

if isfield(data, 'coeffCH2_cal')
    coeffCH2_mel = data.coeffCH2_cal;
    fprintf("coeffCH2_mel (coefficients):\n");
    disp(coeffCH2_mel);
end

if isfield(data, 'coeffCH3_cal')
    coeffCH3_mel = data.coeffCH3_cal;
    fprintf("coeffCH3_mel (coefficients):\n");
    disp(coeffCH3_mel);
end

if isfield(data, 'coeffCH4_cal')
    coeffCH4_mel = data.coeffCH4_cal;
    fprintf("coeffCH4_mel (coefficients):\n");
    disp(coeffCH4_mel);
end


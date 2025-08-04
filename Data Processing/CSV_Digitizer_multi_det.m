clc; clear; close all;

%% Step 1: Set CSV Folder Path
csvFolder = "C:\Users\cwolt\OneDrive\Research\Digitizer\Real-data"; % Update this path

% Get list of all CSV files
csvFiles = dir(fullfile(csvFolder, '*.csv'));

if isempty(csvFiles)
    error("No CSV files found in the specified folder.");
end

% Initialize data containers
time_stampCH0 = [];
energyCH1 = []; time_stampCH1 = [];
energyCH2 = []; time_stampCH2 = [];
energyCH3 = []; time_stampCH3 = [];
energyCH4 = []; time_stampCH4 = [];

%% Step 2: Loop through and assign data to appropriate variables
for i = 1:length(csvFiles)
    csvFile = fullfile(csvFiles(i).folder, csvFiles(i).name);
    fprintf("Reading file: %s\n", csvFile);

    % Read data without assuming headers
    T = readtable(csvFile, 'ReadVariableNames', false);

    % Determine channel
    if contains(csvFiles(i).name, "CH0", "IgnoreCase", true)
        time_stampCH0 = [time_stampCH0; T.Var1];
    elseif contains(csvFiles(i).name, "CH1", "IgnoreCase", true)
        time_stampCH1 = [time_stampCH1; T.Var1];
        energyCH1 = [energyCH1; T.Var2];
    elseif contains(csvFiles(i).name, "CH2", "IgnoreCase", true)
        time_stampCH2 = [time_stampCH2; T.Var1];
        energyCH2 = [energyCH2; T.Var2];
    elseif contains(csvFiles(i).name, "CH3", "IgnoreCase", true)
        time_stampCH3 = [time_stampCH3; T.Var1];
        energyCH3 = [energyCH3; T.Var2];
    elseif contains(csvFiles(i).name, "CH4", "IgnoreCase", true)
        time_stampCH4 = [time_stampCH4; T.Var1];
        energyCH4 = [energyCH4; T.Var2];
    else
        warning("Skipping unrecognized file: %s", csvFiles(i).name);
        continue;
    end
end

disp("CSV data successfully imported!");

%% Step 3: Pass Energy and Time Stamp variables using a MAT file
pythonExe = "C:\Users\cwolt\AppData\Local\Programs\Python\Python310\python.exe"; % update with correct path
pythonScriptWindows = "C:\Users\cwolt\OneDrive\Research\Digitizer\Real-data\DT5720_Kate_readbatches.py"; % update path

matFile = tempname + ".mat";
save(matFile, ...
    'time_stampCH0', ...
    'energyCH1', 'time_stampCH1', ...
    'energyCH2', 'time_stampCH2', ...
    'energyCH3', 'time_stampCH3', ...
    'energyCH4', 'time_stampCH4');

command = sprintf('"%s" "%s" "%s"', pythonExe, pythonScriptWindows, matFile);
[status, result] = system(command);

if status ~= 0
    warning("Calibration script failed.\nError: %s", result);
    return;
else
    disp("Calibration script executed successfully.");
end

try
    data = jsondecode(result);
catch decodeErr
    error("Failed to decode JSON output from Python.\nRaw result:\n%s\n\nError message:\n%s", result, decodeErr.message);
end

for chNum = 1:4
    energyField = sprintf('energyCH%d_cal', chNum);
    coeffField = sprintf('coeffCH%d_cal', chNum);
    energyVar = sprintf('energyCH%d_ANFO', chNum);
    coeffVar = sprintf('coeffCH%d_ANFO', chNum);

    if isfield(data, energyField)
        assignin('base', energyVar, data.(energyField));
        fprintf("%s (first 10):\n", energyVar); disp(data.(energyField)(1:min(10, end)));
    end

    if isfield(data, coeffField)
        assignin('base', coeffVar, data.(coeffField));
        fprintf("%s (coefficients):\n", coeffVar); disp(data.(coeffField));
    end
end

%% Step 4: Display sample calibrated values and assign to base workspace
for chNum = 1:4
    energyField = sprintf('energyCH%d_cal', chNum);
    coeffField = sprintf('coeffCH%d_cal', chNum);
    energyVar = sprintf('energyCH%d_ANFO', chNum);
    coeffVar = sprintf('coeffCH%d_ANFO', chNum);

    if isfield(data, energyField)
        assignin('base', energyVar, data.(energyField));
        fprintf("%s (first 10):\n", energyVar);
        disp(data.(energyField)(1:min(10, end)));
    end

    if isfield(data, coeffField)
        assignin('base', coeffVar, data.(coeffField));
        fprintf("%s (coefficients):\n", coeffVar);
        disp(data.(coeffField));
    end
end

%% Step 5: Collect and display calibration coefficients as a summary table
coeffMatrix = [];
rowLabels = {};

for chNum = 1:4
    coeffVar = sprintf('coeffCH%d_ANFO', chNum);
    if evalin('base', sprintf("exist('%s','var')", coeffVar))
        coeffs = evalin('base', coeffVar);
        coeffMatrix = [coeffMatrix; coeffs(:)'];
        rowLabels{end+1} = sprintf('CH%d', chNum);
    end
end

if ~isempty(coeffMatrix)
    fprintf("\nSummary of Calibration Coefficients (quadratic fits):\n");
    coeffTable = array2table(coeffMatrix, ...
        'VariableNames', {'a_quad', 'b_linear', 'c_intercept'}, ...
        'RowNames', rowLabels);
    disp(coeffTable);
end

%% Step 6: Plot calibration curves and energy histograms
x = linspace(0, 1024, 200);  % ADC channel range
colors = lines(4);

% Calibration curves
figure;
hold on;
for chNum = 1:4
    coeffVar = sprintf('coeffCH%d_ANFO', chNum);
    if evalin('base', sprintf("exist('%s','var')", coeffVar))
        coeffs = evalin('base', coeffVar);
        y = polyval(coeffs, x);
        plot(x, y, 'DisplayName', sprintf('CH%d', chNum), 'LineWidth', 1.5, 'Color', colors(chNum,:));
    end
end
xlabel('Channel');
ylabel('Calibrated Energy');
title('Calibration Curves for CH1–CH4');
legend('Location', 'northwest');
grid on;
hold off;

% Energy histograms
figure;
for chNum = 1:4
    energyVar = sprintf('energyCH%d_ANFO', chNum);
    if evalin('base', sprintf("exist('%s','var')", energyVar))
        subplot(2, 2, chNum);  % Create 2x2 grid of plots
        energy = evalin('base', energyVar);
        [counts, edges] = histcounts(energy, 'BinWidth', 20, 'BinLimits', [0, 14000]);
        binCenters = edges(1:end-1) + diff(edges)/2;
        bar(binCenters, counts, 'FaceColor', colors(chNum,:));
        title(sprintf('Energy Distribution – CH%d', chNum));
        xlabel('Calibrated Energy');
        ylabel('Counts');
        grid on;
    end
end

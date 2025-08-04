 % MATLAB Script to Set Up Python Environment (Virtual Env or System Python)
clc; clear; close all;

%% Step 1: Select Python Mode (Virtual Environment or System Python)
useVirtualEnv = true;  % Set to false to use system-wide Python

if useVirtualEnv
    disp("Using Virtual Environment (.venv)...");
    pythonExe = "C:\Users\cwolt\AppData\Local\Programs\Python\Python310\python.exe";  % Path to Python inside virtual environment
    venvPath = "C:\Users\cwolt\PycharmProjects\Research\.venv1";  % Path to virtual environment
    executionMode = "OutOfProcess";  % Use Out-of-Process to prevent MATLAB crashes
else
    disp("Using System-Wide Python...");
    pythonExe = "C:\Users\cwolt\AppData\Local\Programs\Python\Python310\python.exe";  % System Python path
    venvPath = "";  % No virtual environment path
    executionMode = "InProcess";  % Default MATLAB behavior
end

%% Step 2: Upgrade pip to the latest version
disp("Upgrading pip...");
system(sprintf('"%s" -m pip install --upgrade pip', pythonExe));

%% Step 3: Check & Set Python in MATLAB
disp("Checking Python environment...");

p = pyenv;
if p.Status == "Loaded" && p.Version ~= pythonExe
    disp("Terminating current Python environment...");
    terminate(p);
end

disp("Setting MATLAB Python environment...");
pyenv('Version', pythonExe, 'ExecutionMode', executionMode);

% Verify Python is working
try
    py.print("Python is working in MATLAB.");
catch
    error("Python is not working in MATLAB. Check your Python installation and pyenv settings.");
end

%% Step 4: Install & Verify Missing Python Packages
disp("Checking and installing missing Python packages...");

% uninstall default torch
system(sprintf('"%s" -m pip uninstall -y torch', pythonExe));

requiredPackages = {'torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126', 'torchvision', 'numpy', 'scipy', 'matplotlib' 'ftfy', 'regex', 'h5py','timm'}; % added ftfy, regex

for i = 1:length(requiredPackages)
    package = requiredPackages{i};
    try
        py.importlib.import_module(package);
        fprintf("Python package '%s' is already installed.\n", package);
    catch
        fprintf("Installing Python package: %s...\n", package);
        system(sprintf('"%s" -m pip install --no-cache-dir %s', pythonExe, package));
    end
end

% Ensure CLIP is installed in Python 3.10 explicitly
disp("Verifying CLIP installation in Python 3.10...");
clipCheckCmd = sprintf('"%s" -c "import clip; print(clip.available_models())"', pythonExe);
[clipStatus, clipResult] = system(clipCheckCmd);

if clipStatus ~= 0
    disp("CLIP is not installed. Installing in Python 3.10...");
    system(sprintf('"%s" -m pip install -e C:\\Users\\cwolt\\PycharmProjects\\Research\\CLIP-main', pythonExe)); % Change file path to correct clip-main path. Ensure double "\\"
else
disp("CLIP is already installed in Python 3.10.");
end

% % check if git is installed on machine, install if not already
% disp("Checking if Git is installed...");
% 
% [gitStatus, gitVersion] = system("git --version");
% 
% if gitStatus ~= 0
%     disp("Git is not installed. Installing Git...");
%     system('winget install --id Git.Git -e --silent'); % Installs Git using Windows Package Manager
%     pause(10); % Wait for installation to complete
% else
%     fprintf("Git is already installed: %s\n", gitVersion);
% end
% 
% % install openai-clip from github repo
% disp("Installing OpenAI CLIP...");
% 
% try
%     % Try installing from GitHub
%     status = system(sprintf('"%s" -m pip install git+https://github.com/openai/CLIP.git', pythonExe));
% 
%     % Check if installation was successful
%     if status ~= 0
%         error("Git-based installation failed.");
%     end
% catch
%     % Fallback: Install from PyPI
%     disp("Git-based installation failed. Trying PyPI instead...");
%     system(sprintf('"%s" -m pip install clip-by-openai', pythonExe));
% end

%% Step 5: Fix Potential PyTorch DLL Path Issues (Only for Virtual Environment)
if useVirtualEnv
    disp("Fixing potential PyTorch DLL path issues...");
    dll_path = fullfile(venvPath, "Lib", "site-packages", "torch", "lib");
    if count(py.sys.path, dll_path) == 0
        fprintf("Adding PyTorch DLL path to MATLAB...\n");
        insert(py.sys.path, int32(0), dll_path);
    end
end

disp("Setup Complete! You can now use Python packages in MATLAB.");

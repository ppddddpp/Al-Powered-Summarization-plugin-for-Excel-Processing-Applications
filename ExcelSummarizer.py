import subprocess
import sys
import os
import time
import threading
import urllib.request
import zipfile
import io
import shutil

def check_python_version():
    major, minor = sys.version_info[:2]
    if major == 3 and minor == 12:
        print("\n You are using Python 3.12. Some dependencies like 'tiktoken' may require 'setuptools' and Rust toolchain.")
        print("   If facing errors, you should installing setuptools manually or switching to Python 3.11 for best compatibility.\n")

def ensure_setuptools():
    """
    Ensures that setuptools is installed in the environment.

    This function attempts to import the setuptools module. If the import
    fails, it installs setuptools using pip. If setuptools is already
    installed, it prints a confirmation message.
    """

    try:
        import setuptools
    except ImportError:
        print("setuptools not found. Installing it now...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "setuptools"])
    else:
        print("setuptools is already installed.")
        
def find_requirements_txt(base_dir):
    """
    Searches for the 'requirements.txt' file within the base directory.
    
    Returns the full path if found, otherwise returns None.
    """
    for root, _, files in os.walk(base_dir):
        if "requirements.txt" in files:
            return os.path.join(root, "requirements.txt")
    return None

def install_python_dependencies():
    """
    Installs Python dependencies from the requirements.txt file found in the project directory.

    If requirements.txt is found, it installs dependencies using pip. Otherwise, it prints a warning and skips installation.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    requirements_path = find_requirements_txt(base_dir)

    if not requirements_path:
        print("Warning: No 'requirements.txt' found. Skipping Python dependency installation.")
        return

    try:
        print(f"Installing Python dependencies from {requirements_path}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", requirements_path])
        print("Python dependencies installed successfully.")
    except subprocess.CalledProcessError:
        print("An error occurred while installing Python dependencies.")
        sys.exit(1)

def install_npm_dependencies():
    """
    Installs npm dependencies from the package.json in the gradle_project folder.

    This function performs the following steps:

    1. Removes the existing node_modules folder.
    2. Clears the npm cache.
    3. Installs npm dependencies with verbose output.

    If any step fails, the function will output an error message and exit the program.

    If no package.json is found in the gradle_project folder, the function will print a message and do nothing.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    gradle_project_dir = os.path.join(base_dir, "Summarizer", "gradle_project")
    package_json_path = os.path.join(gradle_project_dir, "package.json")
    
    if os.path.exists(package_json_path):
        try:
            print("Removing existing node_modules...")
            shutil.rmtree(os.path.join(gradle_project_dir, "node_modules"), ignore_errors=True)
            
            print("Clearing npm cache...")
            subprocess.check_call("npm.cmd cache clean --force", cwd=gradle_project_dir, shell=True)
            
            print("Installing npm dependencies with verbose output...")
            subprocess.check_call("npm.cmd install --verbose", cwd=gradle_project_dir, env=os.environ, shell=True)
            print("npm dependencies installed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"An error occurred while installing npm dependencies: {e}")
            sys.exit(1)
    else:
        print("No package.json found in the gradle_project folder. Skipping npm install.")

def update_env_from_fnm():
    """
    Updates environment variables from the output of 'fnm env'.

    Calls 'fnm env' and parses each line that starts with "export".
    If the line can be parsed into a key-value pair, the corresponding
    environment variable is updated. If the key is "PATH", the value is
    prepended to the existing PATH environment variable.

    If 'fnm env' fails to run, or if any error occurs during parsing,
    exits the program with status code 1.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    local_npm_dir = os.path.join(base_dir, "Summarizer", "npm")
    fnm_executable = os.path.join(local_npm_dir, "fnm.exe")
    
    try:
        print("Evaluating 'fnm env' to update environment variables...")
        env_output = subprocess.check_output(
            [fnm_executable, "env"],
            shell=True,
            text=True,
            env=os.environ
        ).strip()
        # Parse each line that starts with "export"
        for line in env_output.splitlines():
            line = line.strip()
            if line.startswith("export "):
                try:
                    key_val = line[len("export "):]
                    key, value = key_val.split("=", 1)
                    value = value.strip().strip('"')
                    if key == "PATH":
                        os.environ[key] = value + os.pathsep + os.environ.get("PATH", "")
                    else:
                        os.environ[key] = value
                    print(f"Updated environment variable: {key}")
                except Exception as parse_err:
                    print(f"Error parsing line: {line}: {parse_err}")
        print("Environment variables updated successfully from fnm env.")
    except subprocess.CalledProcessError as e:
        print("Error running 'fnm env':", e)
        sys.exit(1)

def install_node_with_fnm(fnm_path, version="23", retries=3, delay=5):
    """
    Installs Node.js with the given version using fnm.

    This function runs fnm with the given path and version, and captures the output.
    If the command succeeds, prints a success message and returns True.
    If the command fails, prints the output and retries up to 'retries' times
    with a delay of 'delay' seconds between attempts.
    If all retries fail, prints an error message and returns False.

    :param fnm_path: Path to the fnm executable.
    :param version: Node.js version to install. Defaults to "23".
    :param retries: Number of retries if the command fails. Defaults to 3.
    :param delay: Delay in seconds between retries. Defaults to 5.
    :return: True if the installation succeeded, False otherwise.
    """
    for attempt in range(1, retries + 1):
        print(f"Attempt {attempt}: Installing Node.js version {version} using fnm...")
        result = subprocess.run(
            [fnm_path, "install", version],
            shell=True,
            capture_output=True,
            text=True,
            env=os.environ
        )
        if result.returncode == 0:
            print("Node.js installed successfully via fnm.")
            return True
        else:
            print("Error installing Node.js with fnm:")
            print("stdout:", result.stdout)
            print("stderr:", result.stderr)
            if attempt < retries:
                print(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                print("Maximum retries reached. Exiting.")
                return False


def install_fnm_and_node():
    """
    Installs fnm (Fast Node Manager) and Node.js version 23 locally.

    This function performs the following steps:
    1. Downloads and extracts fnm if it is not already present in the local directory.
    2. Sets the FNM_DIR environment variable to ensure Node.js is installed locally.
    3. Installs Node.js version 23 using fnm.
    4. Updates environment variables using 'fnm env' to ensure Node.js and npm are accessible.
    5. Verifies the installation by checking the versions of Node.js and npm.

    If any step fails, the function will output an error message and exit the program.
    """

    base_dir = os.path.dirname(os.path.abspath(__file__))
    local_npm_dir = os.path.join(base_dir, "Summarizer", "npm")
    os.makedirs(local_npm_dir, exist_ok=True)

    # Download and extract fnm if it doesn't exist.
    fnm_executable = os.path.join(local_npm_dir, "fnm.exe")
    if not os.path.exists(fnm_executable):
        print("Downloading portable fnm...")
        fnm_zip_url = "https://github.com/Schniz/fnm/releases/download/v1.38.1/fnm-windows.zip"
        try:
            with urllib.request.urlopen(fnm_zip_url) as response:
                data = response.read()
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                z.extractall(local_npm_dir)
        except Exception as e:
            print(f"Error downloading or extracting fnm: {e}")
            sys.exit(1)
        
        if not os.path.exists(fnm_executable):
            for item in os.listdir(local_npm_dir):
                item_path = os.path.join(local_npm_dir, item)
                if os.path.isdir(item_path):
                    candidate = os.path.join(item_path, "fnm.exe")
                    if os.path.exists(candidate):
                        shutil.move(candidate, fnm_executable)
                        break
        if not os.path.exists(fnm_executable):
            print("fnm executable could not be found after extraction.")
            sys.exit(1)
        print("fnm downloaded and extracted successfully.")

    # Set FNM_DIR so that fnm installs Node.js into local folder.
    os.environ["FNM_DIR"] = local_npm_dir
    print(f"Setting FNM_DIR to: {local_npm_dir}")

    fnm_path = fnm_executable
    print(f"Using fnm at: {fnm_path}")
    
    # Try to install Node.js using fnm with retry logic.
    if not install_node_with_fnm(fnm_path, version="23", retries=3, delay=5):
        sys.exit(1)

    # Update environment using 'fnm env'
    update_env_from_fnm()

    # Verify that npm is available.
    try:
        npm_version = subprocess.check_output(
            "npm.cmd -v",
            shell=True, text=True, env=os.environ
        ).strip()
        print(f"npm version detected: {npm_version}")
    except subprocess.CalledProcessError:
        print("Error: npm command not found after activation.")
        sys.exit(1)

    # Verify installation by checking versions.
    try:
        node_version = subprocess.check_output(
            ["powershell", "-Command", "node -v"],
            shell=True, text=True, env=os.environ
        ).strip()
        npm_version = subprocess.check_output(
            ["powershell", "-Command", "npm -v"],
            shell=True, text=True, env=os.environ
        ).strip()
        print(f"Node.js version installed: {node_version}")
        print(f"npm version installed: {npm_version}")
    except subprocess.CalledProcessError as e:
        print("Error verifying Node.js/npm versions.")
        sys.exit(1)

def run_summarizer_script():
    """
    Starts the summarizer.py script using the current Python interpreter.

    If the summarizer.py script is not found, an error message is printed and the program exits with status code 1.

    Returns a subprocess.Popen object representing the running summarizer.py script.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    summarizer_script = os.path.join(base_dir, "Summarizer", "SummarizerModule", "summarizer.py")
    
    if not os.path.exists(summarizer_script):
        print(f"Error: Could not find {summarizer_script}")
        sys.exit(1)

    print("Starting summarizer.py...")
    return subprocess.Popen([sys.executable, summarizer_script])

def run_npm_start():
    """
    Starts the 'npm start' command in the gradle_project folder.

    If the folder does not contain a package.json, this function will do nothing and return None.

    The function will pass the input 'n\n' to the npm process to prevent it from hanging indefinitely.

    If the npm process completes within 60 seconds, this function will return the subprocess.Popen object.
    Otherwise, it will print a message and return None.

    Returns a subprocess.Popen object or None
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    gradle_project_dir = os.path.join(base_dir, "Summarizer", "gradle_project")
    package_json_path = os.path.join(gradle_project_dir, "package.json")
    
    if not os.path.exists(package_json_path):
        print("No package.json found in the gradle_project folder. Skipping npm install/start.")
        return

    print("Starting 'npm start' in gradle_project folder...")
    try:
        proc = subprocess.Popen(
            "npm.cmd start",
            cwd=gradle_project_dir,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=os.environ,
            shell=True
        )
        try:
            stdout, stderr = proc.communicate(input="n\n", timeout=60)
            print(stdout)
            if stderr:
                print(stderr, file=sys.stderr)
        except subprocess.TimeoutExpired:
            print("npm process did not complete within the timeout period; leaving it running.")
        return proc
    except Exception as e:
        print(f"An error occurred while starting npm: {e}")
        sys.exit(1)

def run_summarizer():
    """
    Runs the summarizer.py script in a subprocess and the 'npm start' command in a thread.

    The summarizer.py script is started first, and the 'npm start' command is started in a separate thread.
    The summarizer.py subprocess is waited on, and the 'npm start' thread is joined.
    A success message is printed after both processes have finished.

    Returns None
    """
    summarize_proc = run_summarizer_script()
    npm_thread = threading.Thread(target=run_npm_start)
    npm_thread.start()
    summarize_proc.wait()
    npm_thread.join()
    print("Both summarizer.py and npm start processes have finished.")

if __name__ == "__main__":
    check_python_version()
    ensure_setuptools()
    install_python_dependencies()
    install_fnm_and_node()
    install_npm_dependencies()
    run_summarizer()

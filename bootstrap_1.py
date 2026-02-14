"""
.venv\Scripts\python.exe bootstrap_1.py

PREVIEW:
        .venv\Scripts\python.exe bootstrap_1.py --dry-run
        
        
        .venv setup python -m venv .venv
        .venv\Scripts\activate
        .venv\Scripts\python.exe -m pip install --upgrade pip
        .venv\Scripts\python.exe -m pip install <missing packages>

"""

"""NEXT MODIFICATIONS TO BE PENDING
also i wanna use something dynamic as something dynamic as on some places various versions of python are used so i want this script to provide an prompt at begining asking for which versions of python i wanna use and it should create different env for each version and also i want next update as an floating button or menu which i can use to activate deactivate the environment and any version i want to activate or deactivate as i please like a switch board i wanna turn on light or turn off fan or vise versa i can activate any environment or deeactivate it just by that floating window as i please in the project folder so that i don need to use comands to switch the environment and other stuff 

SECOND
i want an second window which holds the whole project structure of my roject i wanna test or run any script I just need to click there and the script will run in terminal i dont have to face the issue like file not found folder not found moduls not found any kind of these errors if this kind of response comes the script should auto recalculate and reshedule everything an make the script running as per situtaion or condition

"""

import os
import sys
import ast
import subprocess
import importlib.util
import json

print("▶ Starting bootstrap environment setup")

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# -------------------- STEP 0: FIND EXISTING VENV --------------------
print("\n[STEP 0] Searching for existing virtual environments")

MODULE_TO_PIP = {
    "cv2": "opencv-python",
    "PIL": "Pillow",
    "sklearn": "scikit-learn",
    "bs4": "beautifulsoup4",
    "yaml": "PyYAML",
}

DRY_RUN = "--dry-run" in sys.argv

CANDIDATE_ENVS = [".venv", "venv"]
VENV_PATH = None

for name in CANDIDATE_ENVS:
    candidate = os.path.join(PROJECT_ROOT, name)
    python_path = os.path.join(candidate, "Scripts", "python.exe")
    if os.path.exists(python_path):
        VENV_PATH = candidate
        print(f"✔ Found existing virtual environment: {candidate}")
        break

# If none found, default to .venv
if VENV_PATH is None:
    VENV_PATH = os.path.join(PROJECT_ROOT, ".venv")
    print("❌ No existing virtual environment found")

print(f"▶ Virtualenv path selected: {VENV_PATH}")

# -------------------- STEP 1: CREATE VENV (ONLY IF MISSING) --------------------
print("\n[STEP 1] Checking virtual environment")

if not os.path.exists(VENV_PATH):
    print("⬇ Creating new virtual environment")
    subprocess.check_call([sys.executable, "-m", "venv", VENV_PATH])
    print("✔ Virtual environment created")

    print("⬆ Upgrading pip")
    subprocess.check_call([
        os.path.join(VENV_PATH, "Scripts", "pip"),
        "install",
        "--upgrade",
        "pip"
    ])
else:
    print("✔ Using existing virtual environment")

# Select python inside venv
if os.name == "nt":
    VENV_PYTHON = os.path.join(VENV_PATH, "Scripts", "python.exe")
else:
    VENV_PYTHON = os.path.join(VENV_PATH, "bin", "python")

print(f"▶ Using venv python: {VENV_PYTHON}")

# -------------------- STEP 2: SCAN IMPORTS --------------------
print("\n[STEP 2] Scanning project files for imports")

STANDARD_LIBS = set(sys.builtin_module_names)
found_imports = set()

def is_std_lib(module):
    if module in ("__main__",):
        return True
    if module in STANDARD_LIBS:
        return True
    try:
        spec = importlib.util.find_spec(module)
    except (ModuleNotFoundError, ValueError):
        return False
    if spec is None or spec.origin is None:
        return True
    return "site-packages" not in spec.origin

def scan_file(file_path):
    print(f"  ▶ Scanning: {file_path}")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())
    except Exception as e:
        print(f"    ⚠ Skipped (parse error): {e}")
        return

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for name in node.names:
                module = name.name.split(".")[0]
                if not is_std_lib(module):
                    found_imports.add(module)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                module = node.module.split(".")[0]
                if not is_std_lib(module):
                    found_imports.add(module)

IGNORE_DIRS = {
    VENV_PATH,
    os.path.join(PROJECT_ROOT, ".git"),
    os.path.join(PROJECT_ROOT, "__pycache__"),
    os.path.join(PROJECT_ROOT, ".idea"),
    os.path.join(PROJECT_ROOT, ".vscode"),
}

for root, _, files in os.walk(PROJECT_ROOT):
    # if any (root.startswith(ignored) for ignored in IGNORE_DIRS):
    if any(os.path.commonpath([root, ignored]) == ignored for ignored in IGNORE_DIRS):
        print(f"  ⚠ Skipping ignored directory: {root}")
        continue
    for file in files:
        if file.endswith(".py") and file != os.path.basename(__file__):
            scan_file(os.path.join(root, file))

third_party = sorted(found_imports)

print("\n▶ Third-party modules required by project:")
for pkg in third_party:
    print(f"  - {pkg}")

with open("requirements_auto.txt", "w") as f:
    for pkg in third_party:
        f.write(pkg + "\n")

print("✔ requirements_auto.txt written")

with open("requirements_clean.txt", "w") as f:
    for pkg in third_party:
        f.write(MODULE_TO_PIP.get(pkg, pkg) + "\n")

print("✔ requirements_clean.txt written")

# -------------------- STEP 3: CHECK INSTALLED PACKAGES --------------------
print("\n[STEP 3] Checking installed packages in environment")

def get_installed_packages():
    # if package == "test":
    #     return True
    # try:
    #     subprocess.check_call(
    #         [VENV_PYTHON, "-c", f"import {package}"],
    #         stdout=subprocess.DEVNULL,
    #         stderr=subprocess.DEVNULL
    #     )
    #     return True
    # except subprocess.CalledProcessError:
    #     return False
    output = subprocess.check_output(
        [VENV_PYTHON, "-m", "pip", "freeze"],
        text = True
    )
    return {line.split("==")[0].lower() for line in output.splitlines()}

missing = []
installed_by_script = []
installed = get_installed_packages()

for package in third_party:
    pip_name = MODULE_TO_PIP.get(package, package)
    if pip_name.lower() in installed:
        print(f"✔ {package} already installed")
    else:
        print(f"❌ {package} missing")
        missing.append(pip_name)

missing = sorted(set(missing))
# for package in third_party:
#     if is_installed(package):
#         print(f"✔ {package} already installed")
#     else:
#         print(f"❌ {package} missing")
#         missing.append(package)

# -------------------- STEP 4: INSTALL MISSING --------------------
print("\n[STEP 4] Installing missing packages")

for package in missing:
    if DRY_RUN:
        print(f"[DRY-RUN] Would install {package}")
        # pip_name = MODULE_TO_PIP.get(package, package)
    else:
        subprocess.check_call([VENV_PYTHON, "-m", "pip", "install", package])
        installed_by_script.append(package)
        print(f"✔ Installed {package}")

# -------------------- STEP 5: FREEZE ENV --------------------
print("\n[STEP 5] Locking environment versions")

with open("requirements_locked.txt", "w") as f:
    subprocess.check_call(
        [VENV_PYTHON, "-m", "pip", "freeze"],
        stdout=f
    )

print("✔ requirements_locked.txt written")
print("\n✔ Environment setup completed successfully")

installed = get_installed_packages()

# -------------------- STEP 6: DEPENDENCY WRITING REPORTS --------------------
print("\n[STEP 6] Writing dependency reports")

report = {
    "found_imports": sorted(third_party),
    "installed": sorted(installed),
    "missing": sorted(missing),
    "installed_by_script": installed_by_script
}

with open("dependency_report.json", "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2)

with open("dependency_report.txt", "w", encoding="utf-8") as f:
    # for key, values in report.items():
    f.write("Dependency Report\n")
    f.write("===================\n\n")
    
    f.write("Found imports:\n")
    for m in sorted(third_party):
        f.write(f"  - {m}\n")
        
    f.write("\nMissing packages:\n")
    for m in missing:
        f.write(f" - {m}\n")
    
    f.write("\nInstalled by script:\n")
    for m in installed_by_script:
        f.write(f" - {m}\n")
        

print("✔ dependency_report.json written")
print("✔ dependency_report.txt written")
        # f.write(f"{key}:\n")
        # for value in values:
        #     f.write(f"  - {value}\n")
        # f.write("\n")


# -------------------- STEP 7: GENERATING PYPROJECT.TOML --------------------
print("\n[STEP 7] Generating pyproject.toml")

with open("pyproject.toml", "w", encoding="utf-8") as f:
    f.write("[project]\n")
    f.write('name = "project_100_angela"\n')
    f.write('version = "1.0.0"\n')
    f.write('description = "Auto-generated dependency file"\n')
    f.write('requires-python = ">=3.10"\n')
    f.write("dependencies = [\n")
    
    for pkg in sorted(set(MODULE_TO_PIP.get(p,p) for p in third_party)):
        f.write(f'  "{pkg}", \n')
        
    f.write("]\n")

print("✔ pyproject.toml written")

    
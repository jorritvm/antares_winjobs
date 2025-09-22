import os
import shutil
from enum import Enum
import subprocess

class ZipMethod(Enum):
    """Available methods for creating ZIP archives."""
    SEVEN_Z_ENV = "7z_env"
    SEVEN_Z_CFG = "7z_cfg"
    BUILTIN = "zipfile"


def identify_best_zip_method(user_7z_path: str) -> Enum:
    """Identify the best available ZIP method.

    Priority:
    1. Use 7z if available on PATH.
    2. Use user-provided 7z path if configured.
    3. Fallback to Python's built-in zipfile module.
    """
    # Check if "7z" is available on PATH
    if shutil.which("7z"):
        return ZipMethod.SEVEN_Z_ENV

    # Check if user provided a custom 7z path in config
    if user_7z_path and os.path.exists(user_7z_path):
        return ZipMethod.SEVEN_Z_CFG

    # Fallback
    return ZipMethod.BUILTIN

def smart_zip_folder(source_folder_path: str,
                     output_zip_file_path: str,
                     exclude_folder_names: list[str] = None,
                     user_7z_path=None):
    """Zip a folder, optionally excluding some subfolders."""

    # verification of inputs
    if not os.path.exists(source_folder_path):
        raise ValueError(f"Source folder {source_folder_path} does not exist.")
    if not os.path.isdir(source_folder_path):
        raise ValueError(f"Source path {source_folder_path} is not a directory.")
    if os.path.exists(output_zip_file_path):
        raise ValueError(f"Output zip file {output_zip_file_path} already exists.")

    exclude_folder_names = set(exclude_folder_names or [])
    method = identify_best_zip_method(user_7z_path)

    if method in {ZipMethod.SEVEN_Z_ENV, ZipMethod.SEVEN_Z_CFG}:
        # Use 7z
        seven_zip_exe = shutil.which("7z") if method == ZipMethod.SEVEN_Z_ENV else user_7z_path
        smart_zip_with_7z(source_folder_path, output_zip_file_path, seven_zip_exe, exclude_folder_names)
    else:
        # Built-in zipfile
        smart_zip_with_builtin(exclude_folder_names)


def smart_zip_with_7z(source_folder_path, output_zip_file_path, seven_zip_exe, exclude_folder_names):
    """Zip a folder using 7z, excluding specified subfolders."""
    if not seven_zip_exe or not os.path.exists(seven_zip_exe):
        raise ValueError("7z executable not found.")

    exclude_params = []
    for d in exclude_folder_names:
        exclude_params += ["-xr!{}".format(d)]
    # cmd = [seven_zip_exe, "a", "-tzip", "-mx=0", output_zip_file_path, source_folder_path] + exclude_params
    # subprocess.run(cmd, check=True)
    # "." = take all files in the current directory (when cwd is set to source_folder_path)
    cmd = [seven_zip_exe, "a", "-tzip", "-mx=0", output_zip_file_path, "."] + exclude_params

    # Run 7z with a *temporary working directory* set just for this subprocess
    subprocess.run(cmd, cwd=source_folder_path, check=True)


def smart_zip_with_builtin(exclude_folder_names):
    with ZipFile(output_path, "w", ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(source_path):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_folder_names]
            for file in files:
                file_path = Path(root) / file
                zipf.write(file_path, file_path.relative_to(source_path))



def qdfqdf():
    pass

def unzip_file(zip_file: str, extract_to: str, method: ZipMethod = ZipMethod.BUILTIN, user_7z_path=None):
    """Unzip a zip file using the specified method."""
    zip_path = Path(zip_file)
    extract_path = Path(extract_to)
    extract_path.mkdir(parents=True, exist_ok=True)

    if method in {ZipMethod.SEVEN_Z_ENV, ZipMethod.SEVEN_Z_CFG}:
        seven_zip_exe = shutil.which("7z") if method == ZipMethod.SEVEN_Z_ENV else user_7z_path
        if not seven_zip_exe:
            raise ValueError("7z executable not found.")

        cmd = [seven_zip_exe, "x", str(zip_path), f"-o{extract_path}"]
        subprocess.run(cmd, check=True)
    else:
        with ZipFile(zip_path, "r") as zipf:
            zipf.extractall(extract_path)
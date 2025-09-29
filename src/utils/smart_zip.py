from enum import Enum
import os
from pathlib import Path
import shutil
import subprocess
from zipfile import ZipFile, ZIP_STORED


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

    exclude_folder_names = set(exclude_folder_names or []) # set of folder names
    method = identify_best_zip_method(user_7z_path)

    if method in {ZipMethod.SEVEN_Z_ENV, ZipMethod.SEVEN_Z_CFG}:
        # Use 7z
        seven_zip_exe = shutil.which("7z") if method == ZipMethod.SEVEN_Z_ENV else user_7z_path
        zip_with_7z(source_folder_path, output_zip_file_path, seven_zip_exe, exclude_folder_names)
    else:
        # Built-in zipfile
        zip_with_builtin(source_folder_path, output_zip_file_path, exclude_folder_names)
    return output_zip_file_path


def zip_with_7z(source_folder_path, output_zip_file_path, seven_zip_exe, exclude_folder_names):
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


def zip_with_builtin(source_folder_path, output_zip_file_path, exclude_folder_names):
    """Zip a folder using Python's built-in zipfile module, excluding specified subfolders."""
    source_path = Path(source_folder_path)
    with ZipFile(output_zip_file_path, "w", ZIP_STORED) as zipf:
        for root, dirs, files in os.walk(source_folder_path):
            # Skip excluded directories and the root folder itself
            dirs[:] = [d for d in dirs if d not in exclude_folder_names and Path(root, d) != source_path]
            # Add empty directories
            if not files and not dirs:
                dir_path = Path(root)
                rel_dir = dir_path.relative_to(source_path)
                if rel_dir != Path('.') and not any(part in exclude_folder_names for part in rel_dir.parts):
                    zipf.writestr(str(rel_dir) + '/', '')
            for file in files:
                file_path = Path(root) / file
                # Skip files in the output folder
                if source_path == file_path.parent:
                    arcname = file
                else:
                    arcname = file_path.relative_to(source_path)
                # Only add files not in excluded folders
                if not any(part in exclude_folder_names for part in file_path.relative_to(source_path).parts):
                    zipf.write(file_path, arcname)


def smart_unzip_file(input_zip_file_path: str, output_folder_path: str, user_7z_path=None):
    """Unzip a zip file using 7z if available, or builtin otherwise.

    output_folder_path is the parent folder in which the zip file will be extracted
    in a subfolder with the same name as the zipfile.
    """
    # input verification
    if not os.path.exists(input_zip_file_path):
        raise ValueError(f"Input zip file {input_zip_file_path} does not exist.")
    if not os.path.isfile(input_zip_file_path):
        raise ValueError(f"Input path {input_zip_file_path} is not a file.")
    if not os.path.exists(output_folder_path):
        raise ValueError(f"Output folder {output_folder_path} does not exist.")

    basename_without_ext = os.path.splitext(os.path.basename(input_zip_file_path))[0]
    study_folder_path = os.path.join(output_folder_path, basename_without_ext)

    if os.path.exists(study_folder_path):
        raise ValueError(f"Study folder {study_folder_path} already exists. Cannot unzip safely.")

    method = identify_best_zip_method(user_7z_path)
    if method in {ZipMethod.SEVEN_Z_ENV, ZipMethod.SEVEN_Z_CFG}:
        # Use 7z
        seven_zip_exe = shutil.which("7z") if method == ZipMethod.SEVEN_Z_ENV else user_7z_path
        unzip_with_7z(input_zip_file_path, study_folder_path, seven_zip_exe)
    else:
        # Built-in zipfile
        unzip_with_builtin(input_zip_file_path, study_folder_path)
    return study_folder_path

def unzip_with_7z(input_zip_file_path: str, output_folder_path: str, seven_zip_exe: str):
    """Unzip a folder using 7z."""
    if not seven_zip_exe or not os.path.exists(seven_zip_exe):
        raise ValueError("7z executable not found.")

    cmd = [seven_zip_exe, "x", input_zip_file_path, f"-o{output_folder_path}"]
    subprocess.run(cmd, check=True)

def unzip_with_builtin(input_zip_file_path: str, output_folder_path: str):
    """Unzip a folder using Python's built-in zipfile module."""
    with ZipFile(input_zip_file_path, "r") as zipf:
        zipf.extractall(output_folder_path)

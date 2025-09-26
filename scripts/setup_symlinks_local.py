"""
Script to create symbolic links to local fixed disk drives and share them over the network.
Intended to be run on Windows with admin privileges.
Does not rely on any external Python packages.
"""

import os
import subprocess
import string
import ctypes

LINK_ROOT = r"C:\links"
DRIVES_FOLDER = os.path.join(LINK_ROOT, "drives")

def is_local_drive(drive_letter: str) -> bool:
    """Returns True if the drive is a local fixed disk (not removable, not network, not CD)."""
    DRIVE_TYPES = {
        0: "DRIVE_UNKNOWN",
        1: "DRIVE_NO_ROOT_DIR",
        2: "DRIVE_REMOVABLE",
        3: "DRIVE_FIXED",       # ✅ What we want
        4: "DRIVE_REMOTE",      # Network drive
        5: "DRIVE_CDROM",
        6: "DRIVE_RAMDISK"
    }

    drive_path = f"{drive_letter}:"
    drive_type = ctypes.windll.kernel32.GetDriveTypeW(drive_path)
    return DRIVE_TYPES.get(drive_type) == "DRIVE_FIXED"

def create_symlink(drive_folder: str, drive_letter: str) -> None:
    """Create a directory symbolic link to a fixed disk drive."""
    full_path = os.path.join(drive_folder, drive_letter)
    if os.path.exists(full_path):
        print(f"Skipping {full_path}, already exists.")
        return
    run_cmd(wd=drive_folder, cmd=f'mklink /D "{drive_letter}" "{drive_letter}:\\"')


def create_network_share(drive_folder: str, drive_letter: str) -> None:
    """Create a network share with Everyone having full access."""
    full_path = os.path.join(drive_folder, drive_letter)
    run_cmd(wd=drive_folder, cmd=f'net share {drive_letter}="{full_path}" /GRANT:everyone,FULL')

def run_cmd(wd: str, cmd: str) -> None:
    """Run a shell command in the specified working directory and print output."""
    old_wd = os.getcwd()
    try:
        os.chdir(wd)
        print(f"> {cmd}")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout.strip())
        if result.stderr:
            print(result.stderr.strip())
    finally:
        os.chdir(old_wd)

if __name__ == "__main__":
    print("----------------------------------------")
    print("symbolic link generation script")
    print("Python version - 2025")
    print("----------------------------------------")
    print(f"Will create {LINK_ROOT}")
    print(f"Will create {DRIVES_FOLDER} containing a symlink to each local drive")
    print(f"Will share these symlinks as network shares")
    print("----------------------------------------")
    choice = input("Continue? (y/n): ").strip().lower()
    if choice == "y":
        # 1. Create folders
        os.makedirs(LINK_ROOT, exist_ok=True)
        os.makedirs(DRIVES_FOLDER, exist_ok=True)

        # 2. Scan all drive letters and filter for local drives
        alphabet = string.ascii_uppercase
        for drive_letter in alphabet:
            if is_local_drive(drive_letter):
                print(f"Creating symlink and network share for {drive_letter}:")
                create_symlink(DRIVES_FOLDER, drive_letter)
                create_network_share(DRIVES_FOLDER, drive_letter)
        print("Done.")
    else:
        print("Aborted.")
        exit(0)
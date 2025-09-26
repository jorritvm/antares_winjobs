"""
Script to create symbolic links to network shares on remote machines.
Intended to be run on Windows with admin privileges.
Does not rely on any external Python packages.
Must be run after setup_symlinks_local.py has been run on each target machine.
"""
import os
import subprocess

LINK_ROOT = r"C:\links"
# dict with key = hostname and value = list of share names ["C", "D", ...])
SHARES = {
    "LENOVO": ["C", "G"],
}

def create_symlink(link_location: str, link_name: str, target: str):
    """Create a directory symbolic link."""
    full_path = os.path.join(link_location, link_name)
    if os.path.exists(full_path):
        print(f"Skipping {link_location}, already exists.")
        return
    run_cmd(wd=link_location, cmd=f'mklink /D "{link_name}" "{target}"')

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
    print(f"Must be run AFTER setup_symlinks_local.py has been run on each target machine")
    print(f"Will create symlinks in {LINK_ROOT} to each machine and drive specified")
    print("----------------------------------------")
    choice = input("Continue? (y/n): ").strip().lower()
    if choice == "y":
        print("Creating symbolic links to other machines...")
        for host, shares in SHARES.items():
            for share in shares:
                link_name = f"{host}_{share}"
                target = f"\\\\{host}\\{share}"
                create_symlink(LINK_ROOT, link_name, target)
        print("Done.")
    else:
        print("Aborted.")
        exit(0)

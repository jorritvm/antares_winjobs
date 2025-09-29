import os
import subprocess

def create_symlink_with_same_name(where: str, target: str) -> None:
    """Create a directory symbolic link in 'where' to folder 'target'.
    The link name will be the same as the target folder name.
    target must be an absolute path"""

    link_name = os.path.basename(target)
    create_symlink(where, link_name, target)


def create_symlink(where: str, link_name: str, target: str) -> None:
    """Create a directory symbolic link in 'where' to folder 'target'.
    link_name must be a simple name (no path separators),
    target must be an absolute path"""

    full_path = os.path.join(where, link_name)
    if os.path.exists(full_path):
        print(f"Skipping {full_path}, already exists.")
        return
    run_cmd(wd=where, cmd=f'mklink /D "{link_name}" "{target}"')


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
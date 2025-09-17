from typing import Final
import hashlib
import os
from pathlib import Path
import subprocess
import sys
from typing import List, Literal, Optional, Union
from datetime import datetime
import traceback
import shlex


def seconds_from_interval(s: str) -> int:
    """Convert a human-friendly interval string into seconds.

    Supports suffixes: ms, s, m, h. Minimum 1 second.
    """
    s = s.strip().lower()
    if s.endswith("ms"):
        try:
            return max(1, int(float(s[:-2]) / 1000.0))
        except ValueError:
            return 1
    if s.endswith("s"):
        return int(float(s[:-1]))
    if s.endswith("m"):
        return int(float(s[:-1]) * 60)
    if s.endswith("h"):
        return int(float(s[:-1]) * 3600)
    return int(float(s))


def run_shell(cmd: Union[str, List[str]], cwd: Optional[Path] = None, check_throw_exception_on_exit_code: bool = True, stdout=None, stderr=None, text=None, capture_output: bool = False, encoding: str = 'utf-8', verbose: bool = True) -> subprocess.CompletedProcess:
    """Echo + run a shell command"""
    if verbose:
        LOG(f">>> {cmd} (cwd={cwd or Path.cwd()})")
    is_shell = isinstance(cmd, str)
    return subprocess.run(cmd, shell=is_shell, cwd=cwd, check=check_throw_exception_on_exit_code, stdout=stdout, stderr=stderr, text=text, capture_output=capture_output, encoding=encoding)


def change_dir(path: str):
    LOG(f"Changing directory to {path}")
    os.chdir(path)


def LOG(*values: object, sep: str = " ", end: str = "\n", file=None, highlight: bool = False, show_time=True, show_traceback: bool = False, flush: bool = True) -> None:
    # Prepare the message
    message = sep.join(str(value) for value in values)

    # Add timestamp if requested
    if show_time:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"[{timestamp}] {message}"

    # Add backtrace if requested
    if show_traceback:
        tb = traceback.format_stack()
        print(f"Total stack frames: {len(tb)}")  # Debug line
        max_frames = 5  # Maximum number of frames to print
        if len(tb) > max_frames:
            # Keep only the last 10 frames
            filtered_tb = tb[-max_frames:]
        else:
            filtered_tb = tb  # Keep all frames if stack is shallow
        message = f"{message}\nBacktrace:\n" + "".join(filtered_tb)

    if highlight:
        HIGHLIGHT_COLOR = "\033[92m"  # green
        BOLD = "\033[1m"
        RESET = "\033[0m"
        print(f"{BOLD}{HIGHLIGHT_COLOR}", end="", file=file, flush=flush)  # turn to highlight color
        print(message, end="", file=file, flush=flush)  # print message
        print(f"{RESET}", end=end, file=file, flush=flush)  # reset
    else:
        print(message, end=end, file=file, flush=flush)


def is_diff_ignore_eol(file1: Path, file2: Path) -> bool:
    return normalize_lines(file1) != normalize_lines(file2)


def normalize_lines(p: Path) -> bytes:
    with p.open("rb") as f:
        return f.read().replace(b"\r\n", b"\n")


def md5sum(file_path):
    with open(file_path, 'rb') as f:
        md5 = hashlib.md5(f.read()).hexdigest()
    return md5


def read_value_from_credential_file(credentials_file_path: str, key_to_read: str, exit_on_error: bool = True) -> Union[str, None]:
    """
    Reads a specific key's value from a credentials file.
    Returns the value if found, otherwise None.
    """
    if os.path.exists(credentials_file_path):
        try:
            with open(credentials_file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        try:
                            key, value = line.split('=', 1)
                            if key == key_to_read:
                                return value
                        except ValueError:
                            # Handle lines that don't contain '='
                            LOG(f"Warning: Skipping malformed line in {credentials_file_path}: {line}")
                            continue
        except Exception as e:
            if exit_on_error:
                LOG(f"Error reading credentials file {credentials_file_path}: {e}")
                sys.exit(1)
    else:
        LOG(f"Credentials file {credentials_file_path} not found.")
    return None


def show_noti(title="Notification", message="Noti!", duration=5):
    run_shell(
        cmd=f"~/local_tools/dev_common/noti_utils.py --title {shell_escape(title)} --message {shell_escape(message)} --duration {duration}", check_throw_exception_on_exit_code=False, verbose= False)


def shell_escape(str_to_escape: str):
    return shlex.quote(str_to_escape)

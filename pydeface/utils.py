"""Utility scripts for pydeface."""

import sys
import subprocess


def run_shell_cmd(cmd, cwd=[]):
    """Run a command in the shell using Popen."""
    if cwd:
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                                   cwd=cwd)
    else:
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    for line in process.stdout:
        print(line.strip())
    process.wait()


def usage():
    """Print the docstring and exit."""
    sys.stdout.write(__doc__)
    sys.exit(2)

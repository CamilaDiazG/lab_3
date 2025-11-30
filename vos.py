#!/usr/bin/env python3
"""vos.py - Virtual Operating System entrypoint."""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from vos.core.sys import Kernel
from vos.shell.repl import shell_process


def main():
    """
    Start VOS with initial shell process.

    This function:
    1. Creates a new Kernel instance
    2. Spawns the initial shell with PID 0
    3. Runs the shell directly (blocking until exit)
    """
    print("=" * 60)
    print("Virtual Operating System (VOS) - Lab 3")
    print("=" * 60)
    print()

    # Create kernel
    kernel = Kernel()

    # Spawn initial shell with PID 0
    shell_pid = kernel.spawn(shell_process, name="shell0")

    if shell_pid != 0:
        print(f"Warning: Initial shell has PID {shell_pid} (expected 0)")

    # Get the shell PCB and run it directly
    shell_pcb = kernel.processes[shell_pid]

    # Execute the shell (this blocks until shell exits)
    try:
        shell_pcb.prog(kernel, shell_pcb)
    except Exception as e:
        print(f"\nShell crashed: {e}")

    print("\n" + "=" * 60)
    print("VOS Shutdown")
    print("=" * 60)


if __name__ == "__main__":
    main()
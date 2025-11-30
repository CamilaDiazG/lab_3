import os
from typing import Dict, Optional, Callable, Any, List, Tuple
from vos.core.process import PCB, State
from vos.core.vm import VM


class Scheduler:
    """Simple FIFO scheduler interface."""

    def __init__(self):
        self.ready_queue: List[PCB] = []

    def add(self, pcb: PCB) -> None:
        """Add PCB to ready queue."""
        if pcb.state == State.READY:
            self.ready_queue.append(pcb)

    def next(self) -> Optional[PCB]:
        """Get next ready process (FIFO)."""
        if self.ready_queue:
            return self.ready_queue.pop(0)
        return None


class Kernel:
    """
    Kernel managing all processes and scheduling.

    Responsibilities:
    - Process creation (spawn)
    - Process scheduling (dispatch)
    - Process table management
    - System call interface for processes
    """

    def __init__(self):
        self.processes: Dict[int, PCB] = {}  # All processes by PID
        self.sched = Scheduler()
        self.running: Optional[PCB] = None
        self.next_pid = 0  # Start from 0 for initial shell
        self.clock = 0
        self.cwd = os.getcwd()  # Current working directory

    def spawn(self, prog: Callable[[Any, PCB], None], *args, name: str = "") -> int:
        """
        Create a new process.

        Args:
            prog: Process program function(kernel, pcb)
            *args: Optional arguments (can be stored in PCB or handled by prog)
            name: Optional process name for debugging

        Returns:
            PID of newly created process
        """
        pid = self.next_pid
        self.next_pid += 1

        # Wrap program to handle arguments if provided
        if args:
            # Store args in a closure
            original_prog = prog

            def wrapped_prog(kernel, pcb):
                # Check if we need to initialize args storage
                if not hasattr(pcb, '_args_stored'):
                    pcb._args = args
                    pcb._args_stored = True
                return original_prog(kernel, pcb, *pcb._args)

            prog = wrapped_prog

        # Create PCB with fresh VM
        pcb = PCB(
            pid=pid,
            state=State.NEW,
            vm=VM(),
            prog=prog,
            name=name or f"proc{pid}"
        )

        # Store in process table
        self.processes[pid] = pcb

        # Admit to scheduler (NEW → READY)
        pcb.state = State.READY
        self.sched.add(pcb)

        return pid

    def dispatch(self) -> None:
        """
        Execute one time slice (dispatch cycle).

        Steps:
        1. Preempt current process if still RUNNING
        2. Get next READY process from scheduler
        3. Mark new process as RUNNING
        4. Execute one step of its program
        5. Handle state changes (TERMINATED, WAITING, etc.)
        """
        self.clock += 1

        # Step 1: Preempt current process if still RUNNING
        if self.running and self.running.state == State.RUNNING:
            self.running.state = State.READY
            self.sched.add(self.running)
            self.running = None

        # Step 2: Get next READY process
        pcb = self.sched.next()

        if not pcb:
            # No process available, CPU idle
            self.running = None
            return

        # Step 3: Mark as RUNNING
        self.running = pcb
        pcb.state = State.RUNNING

        # Step 4: Execute one step of program
        try:
            pcb.prog(self, pcb)
            pcb.cpu_time += 1
        except Exception as e:
            # Process crashed, terminate it
            print(f"[{self.clock}] Process {pcb.pid} crashed: {e}")
            pcb.state = State.TERMINATED

        # Step 5: Handle state changes
        if pcb.state == State.TERMINATED:
            # Remove from process table
            del self.processes[pcb.pid]
            self.running = None
        elif pcb.state == State.WAITING:
            # Process blocked itself, remove from running
            self.running = None
            # Note: Process stays in self.processes but not in ready queue

    def ps(self) -> List[Tuple[int, str, str]]:
        """
        Return process table (like Unix ps command).

        Returns:
            List of (pid, name, state) tuples
        """
        result = []
        for pid, pcb in sorted(self.processes.items()):
            result.append((pid, pcb.name, pcb.state.name))
        return result

    # ============= SYSTEM CALLS =============

    def kill_sys(self, pid: int) -> bool:
        """
        Terminate process with given PID.

        Args:
            pid: Process ID to terminate

        Returns:
            True if process was terminated, False if not found
        """
        if pid not in self.processes:
            return False

        pcb = self.processes[pid]
        pcb.state = State.TERMINATED

        # Remove from process table
        del self.processes[pid]

        # If it was running, clear running reference
        if self.running and self.running.pid == pid:
            self.running = None

        return True

    def ls_sys(self) -> List[str]:
        """
        List directory contents.

        Returns:
            List of filenames/directories in current working directory
        """
        try:
            return os.listdir(self.cwd)
        except Exception as e:
            print(f"ls error: {e}")
            return []

    def cd_sys(self, path: str) -> bool:
        """
        Change current working directory.

        Args:
            path: Path to change to (relative or absolute)

        Returns:
            True if successful, False if path doesn't exist or isn't a directory
        """
        try:
            # Resolve path relative to current directory
            new_path = os.path.join(self.cwd, path)
            new_path = os.path.abspath(new_path)

            # Check if it's a valid directory
            if os.path.isdir(new_path):
                self.cwd = new_path
                return True
            else:
                return False
        except Exception:
            return False

    def touch_sys(self, path: str) -> bool:
        """
        Create empty file or update timestamp.

        Args:
            path: Filename to create/touch

        Returns:
            True if successful, False otherwise
        """
        try:
            full_path = os.path.join(self.cwd, path)
            # Create file if it doesn't exist, update timestamp if it does
            open(full_path, "a").close()
            return True
        except Exception as e:
            print(f"touch error: {e}")
            return False

    def cat_sys(self, path: str) -> Optional[str]:
        """
        Read and return file contents.

        Args:
            path: Filename to read

        Returns:
            File contents as string, or None if error
        """
        try:
            full_path = os.path.join(self.cwd, path)
            with open(full_path, "r") as f:
                return f.read()
        except Exception as e:
            print(f"cat error: {e}")
            return None

    def exit_sys(self, pcb: PCB) -> None:
        """
        Mark current process as terminated (for exit command).

        Args:
            pcb: Process Control Block to terminate
        """
        pcb.state = State.TERMINATED

    # ============= UTILITY METHODS =============

    def run(self, cycles: int = 100, verbose: bool = True) -> None:
        """
        Run kernel for specified number of dispatch cycles.

        Args:
            cycles: Number of dispatch cycles to execute
            verbose: Print execution trace
        """
        if verbose:
            print(f"{'=' * 60}")
            print(f"Kernel Starting (max {cycles} cycles)")
            print(f"{'=' * 60}\n")

        for _ in range(cycles):
            prev_running = self.running

            self.dispatch()

            # Log context switches
            if verbose and prev_running != self.running:
                prev_str = f"P{prev_running.pid}({prev_running.name})" if prev_running else "IDLE"
                curr_str = f"P{self.running.pid}({self.running.name})" if self.running else "IDLE"
                print(f"[{self.clock:3d}] {prev_str:15s} → {curr_str:15s}")

            # Stop if no processes remain
            if not self.processes:
                if verbose:
                    print(f"\n{'=' * 60}")
                    print(f"All processes completed at cycle {self.clock}")
                    print(f"{'=' * 60}")
                break

        if verbose and self.processes:
            print(f"\n{'=' * 60}")
            print(f"Kernel stopped at cycle {self.clock}")
            print(f"Active processes: {len(self.processes)}")
            print(f"{'=' * 60}")

    def print_ps(self) -> None:
        """Print formatted process table."""
        print("\nProcess Table:")
        print(f"{'PID':<6} {'Name':<15} {'State':<12}")
        print("-" * 35)
        for pid, name, state in self.ps():
            print(f"{pid:<6} {name:<15} {state:<12}")
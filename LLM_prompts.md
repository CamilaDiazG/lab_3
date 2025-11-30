# LLM Prompts for Lab 3 - System Calls & Shell

## Prompt 1: Filesystem System Calls Design

**Prompt:**
```
I'm implementing filesystem system calls (ls, cd, touch, cat) for a simulated OS kernel in Python. The kernel has a `self.cwd` attribute for current working directory. For each syscall:

- ls_sys(): should return list of files/dirs in cwd
- cd_sys(path): should change cwd if valid directory
- touch_sys(path): should create/update file
- cat_sys(path): should return file contents

Show me how to implement these using Python's os module with proper error handling.
```

**Part of Lab:** Step 2 - Filesystem syscalls (Section 4.2)

**Modifications Made:**
- Added return type hints for clarity
- Added try-except blocks for better error handling
- Used `os.path.join()` and `os.path.abspath()` for robust path handling
- Made error messages more descriptive

---

## Prompt 2: Interactive Shell Process Implementation

**Prompt:**
```
I need to implement an interactive shell process for my OS simulator. The shell should:

1. Run in a while True loop
2. Display a prompt showing PID and current directory
3. Parse user commands (ps, kill, ls, cd, touch, cat, shell, exit)
4. Call kernel system calls appropriately
5. Handle the "shell" command by spawning a nested shell
6. Handle the "exit" command by terminating current shell

The shell is a function: `shell_process(kernel, pcb)` where kernel has methods like `kill_sys()`, `ls_sys()`, etc.

Give me a complete implementation with command parsing and nested shell support.
```

**Part of Lab:** Step 3 & 4 - Shell program and commands (Sections 4.3-4.4)

**Modifications Made:**
- Added help command for better UX
- Added pwd command (not in requirements but useful)
- Improved prompt formatting with directory name
- Added error handling for EOFError (Ctrl+D) and KeyboardInterrupt (Ctrl+C)
- Added clearer output messages
- Made command parsing more robust with .strip() and error checking

---

## Prompt 3: Process Termination System Call

**Prompt:**
```
I need to implement a kill_sys(pid) system call in my kernel. The kernel has:
- self.processes: Dict[int, PCB] mapping PIDs to process control blocks
- self.running: currently running PCB or None
- PCB has a `state` attribute

The kill_sys should:
1. Find the process by PID
2. Mark it as TERMINATED
3. Remove it from self.processes
4. Handle if it's currently running

Show me the implementation with proper error handling.
```

**Part of Lab:** Step 1 - kill_sys implementation (Section 4.1)

**Modifications Made:**
- Added check to clear self.running if terminated process is currently running
- Added return value (True/False) for success indication
- Simplified logic by directly deleting from dict after state change

---

## Prompt 4: VOS Entrypoint Design

**Prompt:**
```
I need to create a vos.py entrypoint file that:

1. Creates a Kernel instance
2. Spawns an initial shell process with PID 0
3. Runs that shell directly (the shell has a blocking while loop)
4. Shows startup and shutdown messages

The kernel has a spawn() method that returns PID, and processes are stored in kernel.processes.
The shell_process function signature is: shell_process(kernel, pcb)

Give me a clean main() function for this entrypoint.
```

**Part of Lab:** Step 6 - vos.py entrypoint (Section 4.6)

**Modifications Made:**
- Added sys.path manipulation for proper imports
- Added try-except around shell execution for crash handling
- Added clearer startup/shutdown messages with formatting
- Added warning if shell PID is not 0 (for debugging)

---

## Prompt 5: Demo Task Programs

**Prompt:**
```
I need demo programs for my OS that can be spawned from the shell. Create:

1. idle_process(kernel, pcb, cycles): runs for N cycles then terminates
2. memory_touch_process(kernel, pcb, num_pages): touches N memory pages using pcb.vm.write_byte()

Each should:
- Use hasattr() to initialize state on first run
- Track progress and terminate when done
- Print completion messages
- Set pcb.state = State.TERMINATED when done

Show me clean implementations.
```

**Part of Lab:** Step 5 - Test programs for custom commands (Section 4.5)

**Modifications Made:**
- Added more demo programs (counter, CPU burst, I/O simulation) for variety
- Added docstrings explaining each program's purpose
- Made the memory_touch_process use 4KB page size calculation
- Added clearer output messages with PID identification

---

## Summary

These prompts helped scaffold the entire Lab 3 implementation:
- **Prompt 1-3** built the core system calls and kernel functionality
- **Prompt 4** created the entry point
- **Prompt 5** provided test programs

All responses were integrated with minimal changes - mostly adding docstrings, improving error messages, and ensuring consistent code style with existing lab code.
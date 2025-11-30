"""shell/repl.py - Interactive shell process for VOS."""

import os


def shell_process(kernel, pcb):
    """
    Interactive shell process that runs commands.

    This shell supports:
    - ps: list processes
    - kill <pid>: terminate a process
    - ls: list directory contents
    - cd <path>: change directory
    - touch <file>: create/update file
    - cat <file>: display file contents
    - shell: spawn nested shell
    - exit: exit current shell
    - test1, test2: run demo programs

    Args:
        kernel: Kernel instance
        pcb: This shell's Process Control Block
    """
    from vos.examples.demo_tasks import idle_process, memory_touch_process

    print(f"\n{'=' * 60}")
    print(f"VOS Shell Started (PID {pcb.pid})")
    print(f"Type 'help' for available commands")
    print(f"{'=' * 60}\n")

    while True:
        try:
            # Display prompt with PID and current directory
            cwd_display = os.path.basename(kernel.cwd) or kernel.cwd
            prompt = f"vos[{pcb.pid}]:{cwd_display}> "
            command_line = input(prompt).strip()

            if not command_line:
                continue

            # Parse command and arguments
            parts = command_line.split()
            cmd = parts[0]
            args = parts[1:]

            # Execute command
            if cmd == "help":
                print("\nAvailable commands:")
                print("  ps              - List all processes")
                print("  kill <pid>      - Terminate process")
                print("  ls              - List directory contents")
                print("  cd <path>       - Change directory")
                print("  touch <file>    - Create/update file")
                print("  cat <file>      - Display file contents")
                print("  pwd             - Print working directory")
                print("  shell           - Spawn nested shell")
                print("  exit            - Exit current shell")
                print("  test1           - Run idle process demo")
                print("  test2           - Run memory touch demo")
                print()

            elif cmd == "ps":
                print(f"\n{'PID':<6} {'Name':<20} {'State':<12}")
                print("-" * 40)
                for pid, name, state in kernel.ps():
                    print(f"{pid:<6} {name:<20} {state:<12}")
                print()

            elif cmd == "kill":
                if not args:
                    print("Usage: kill <pid>")
                else:
                    try:
                        target_pid = int(args[0])
                        if target_pid == pcb.pid:
                            print(f"Warning: Killing current shell (PID {pcb.pid})")
                            kernel.kill_sys(target_pid)
                            break
                        elif kernel.kill_sys(target_pid):
                            print(f"Process {target_pid} terminated")
                        else:
                            print(f"Process {target_pid} not found")
                    except ValueError:
                        print("Invalid PID (must be an integer)")

            elif cmd == "ls":
                entries = kernel.ls_sys()
                if entries:
                    # Sort and display in columns
                    entries.sort()
                    for entry in entries:
                        full_path = os.path.join(kernel.cwd, entry)
                        if os.path.isdir(full_path):
                            print(f"  {entry}/")
                        else:
                            print(f"  {entry}")
                else:
                    print("(empty directory)")

            elif cmd == "cd":
                if not args:
                    print("Usage: cd <path>")
                else:
                    path = args[0]
                    if kernel.cd_sys(path):
                        print(f"Changed to: {kernel.cwd}")
                    else:
                        print(f"cd: {path}: No such directory")

            elif cmd == "touch":
                if not args:
                    print("Usage: touch <filename>")
                else:
                    filename = args[0]
                    if kernel.touch_sys(filename):
                        print(f"Created/updated: {filename}")
                    else:
                        print(f"Failed to create: {filename}")

            elif cmd == "cat":
                if not args:
                    print("Usage: cat <filename>")
                else:
                    filename = args[0]
                    content = kernel.cat_sys(filename)
                    if content is not None:
                        print(content)
                    else:
                        print(f"cat: {filename}: No such file or cannot read")

            elif cmd == "pwd":
                print(kernel.cwd)

            elif cmd == "shell":
                # Spawn nested shell
                child_pid = kernel.spawn(shell_process, name=f"shell{kernel.next_pid}")
                print(f"Spawned nested shell with PID {child_pid}")

                # Get the child PCB
                child_pcb = kernel.processes[child_pid]

                # Directly call the shell process (nested execution)
                # This blocks until the child shell exits
                child_pcb.prog(kernel, child_pcb)

                print(f"\nReturned to shell PID {pcb.pid}")

            elif cmd == "exit":
                print(f"Exiting shell (PID {pcb.pid})")
                kernel.exit_sys(pcb)
                break

            elif cmd == "test1":
                # Run idle process from Lab 1/2
                pid = kernel.spawn(idle_process, 5, name="idle_test")
                print(f"Spawned idle process with PID {pid} (will idle for 5 cycles)")

            elif cmd == "test2":
                # Run memory touch process from Lab 1/2
                pid = kernel.spawn(memory_touch_process, 10, name="memtest")
                print(f"Spawned memory touch process with PID {pid} (will access 10 pages)")

            else:
                print(f"Unknown command: {cmd}")
                print("Type 'help' for available commands")

        except EOFError:
            # Ctrl+D pressed
            print("\nExiting shell (EOF)")
            kernel.exit_sys(pcb)
            break
        except KeyboardInterrupt:
            # Ctrl+C pressed
            print("\n^C")
            continue
        except Exception as e:
            print(f"Error: {e}")
"""examples/demo_tasks.py - Demo programs for VOS testing."""

from vos.core.process import State


def idle_process(kernel, pcb, cycles: int):
    """
    Simple idle process that runs for a specified number of cycles.

    Args:
        kernel: Kernel instance
        pcb: Process Control Block
        cycles: Number of cycles to run before terminating
    """
    if not hasattr(pcb, 'count'):
        pcb.count = 0

    pcb.count += 1

    if pcb.count >= cycles:
        print(f"  [P{pcb.pid}] Idle process completed {cycles} cycles")
        pcb.state = State.TERMINATED


def memory_touch_process(kernel, pcb, num_pages: int):
    """
    Process that touches multiple memory pages to demonstrate paging.

    Args:
        kernel: Kernel instance
        pcb: Process Control Block
        num_pages: Number of pages to touch
    """
    if not hasattr(pcb, 'page_count'):
        pcb.page_count = 0

    # Touch a new page each cycle
    page_address = pcb.page_count * 4096  # 4KB pages
    pcb.vm.write_byte(page_address, pcb.page_count)

    pcb.page_count += 1

    if pcb.page_count >= num_pages:
        print(f"  [P{pcb.pid}] Touched {num_pages} pages")
        pcb.state = State.TERMINATED


def counter_process(kernel, pcb, target: int = 10):
    """
    Simple counter process for testing.

    Args:
        kernel: Kernel instance
        pcb: Process Control Block
        target: Count to reach before terminating
    """
    if not hasattr(pcb, 'count'):
        pcb.count = 0

    pcb.count += 1

    if pcb.count >= target:
        print(f"  [P{pcb.pid}] Counter reached {target}")
        pcb.state = State.TERMINATED


def cpu_burst_process(kernel, pcb):
    """
    CPU-bound process that performs computation.

    Args:
        kernel: Kernel instance
        pcb: Process Control Block
    """
    if not hasattr(pcb, 'sum'):
        pcb.sum = 0
        pcb.iterations = 0

    # Simulate CPU-intensive work
    for i in range(100):
        pcb.sum += i

    pcb.iterations += 1

    if pcb.iterations >= 20:
        print(f"  [P{pcb.pid}] CPU burst completed, sum={pcb.sum}")
        pcb.state = State.TERMINATED


def io_simulation_process(kernel, pcb):
    """
    Process that simulates I/O operations by going into WAITING state.

    Args:
        kernel: Kernel instance
        pcb: Process Control Block
    """
    if not hasattr(pcb, 'phase'):
        pcb.phase = 'compute'
        pcb.steps = 0

    pcb.steps += 1

    if pcb.phase == 'compute':
        if pcb.steps >= 3:
            # Simulate starting I/O
            pcb.phase = 'waiting'
            pcb.state = State.WAITING
            pcb.io_complete_at = kernel.clock + 5
            print(f"  [P{pcb.pid}] Starting I/O operation")

    elif pcb.phase == 'waiting':
        # Check if I/O is complete
        if kernel.clock >= pcb.io_complete_at:
            pcb.phase = 'done'
            pcb.state = State.READY
            kernel.sched.add(pcb)
            print(f"  [P{pcb.pid}] I/O operation completed")

    elif pcb.phase == 'done':
        if pcb.steps >= 8:
            print(f"  [P{pcb.pid}] Process completed")
            pcb.state = State.TERMINATED
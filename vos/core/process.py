"""process.py - PCB and State for cooperative scheduler."""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, TYPE_CHECKING
from vos.core.vm import VM

if TYPE_CHECKING:
    from typing import Any as Kernel, Any as PCB
else:
    Kernel = 'Kernel'
    PCB = 'PCB'


class State(Enum):
    """Five-state process model."""
    NEW = auto()
    READY = auto()
    RUNNING = auto()
    WAITING = auto()
    TERMINATED = auto()


@dataclass
class PCB:
    """Process Control Block with per-process VM."""
    # Required
    pid: int
    state: State = State.NEW
    vm: VM = field(default_factory=VM)
    prog: Callable[[Kernel, PCB], None] = lambda k, p: None

    # Optional (justified: statistics, debugging, future priority scheduling)
    cpu_time: int = 0
    name: str = ""
    priority: int = 0

    def __repr__(self) -> str:
        name_str = f" ({self.name})" if self.name else ""
        return f"PCB(pid={self.pid}{name_str}, state={self.state.name})"


# Round-Robin Usage:
# States: NEW→READY→RUNNING↔WAITING, RUNNING→TERMINATED
# Fields: pid (id), state (lifecycle), vm (isolation), prog (code),
#         cpu_time (stats), name (debug), priority (future)
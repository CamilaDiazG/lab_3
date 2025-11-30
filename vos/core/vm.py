from dataclasses import dataclass, field
from typing import Dict, Optional, List
from collections import deque

# Constants
PAGE_SIZE = 256
VIRTUAL_PAGES = 16
PHYSICAL_FRAMES = 8


@dataclass
class PTEntry:
    """Page Table Entry - represents a mapping from virtual page to physical frame"""
    frame: Optional[int] = None  # Physical frame number (None if not present)
    present: bool = False  # Is the page currently in physical memory?
    dirty: bool = False  # Has the page been modified?


@dataclass
class PageTable:
    """Maps virtual page numbers to page table entries"""
    entries: Dict[int, PTEntry] = field(default_factory=dict)

    def get_entry(self, page_no: int) -> PTEntry:
        """Get or create a page table entry for a virtual page"""
        if page_no not in self.entries:
            self.entries[page_no] = PTEntry()
        return self.entries[page_no]


@dataclass
class PhysicalMemory:
    """Represents physical RAM with frames"""
    frames: Dict[int, bytearray] = field(default_factory=dict)
    free_list: List[int] = field(default_factory=list)

    def __post_init__(self):
        """Initialize all physical frames and mark them as free"""
        for frame_no in range(PHYSICAL_FRAMES):
            self.frames[frame_no] = bytearray(PAGE_SIZE)
            self.free_list.append(frame_no)

    def allocate_frame(self) -> Optional[int]:
        """Allocate a free frame, return frame number or None if no free frames"""
        if self.free_list:
            return self.free_list.pop(0)
        return None

    def free_frame(self, frame_no: int):
        """Mark a frame as free"""
        self.free_list.append(frame_no)


class VM:
    """Virtual Memory simulation with paging and FIFO replacement"""

    def __init__(self):
        self.page_table = PageTable()
        self.physical_memory = PhysicalMemory()

        # FIFO queue for page replacement (stores page numbers)
        self.fifo_queue: deque = deque()

        # Reverse mapping: frame -> page (for eviction)
        self.frame_to_page: Dict[int, int] = {}

        # Backing store: simulates disk storage for pages
        self.backing_store: Dict[int, bytearray] = {}

        # Statistics
        self.page_faults = 0
        self.page_evictions = 0

    def _ensure_in_ram(self, page_no: int):
        """
        Ensure a page is loaded in physical RAM.
        Handles page faults and FIFO replacement.
        """
        entry = self.page_table.get_entry(page_no)

        # Page is already in RAM
        if entry.present:
            return

        # PAGE FAULT occurred
        self.page_faults += 1
        print(f"[PAGE FAULT] Page {page_no} not in RAM")

        # Try to allocate a free frame
        frame_no = self.physical_memory.allocate_frame()

        # No free frames available - need to evict (FIFO)
        if frame_no is None:
            # Get the oldest page from FIFO queue
            victim_page = self.fifo_queue.popleft()
            victim_entry = self.page_table.get_entry(victim_page)

            frame_no = victim_entry.frame
            print(f"[EVICTION] Evicting page {victim_page} from frame {frame_no}")
            self.page_evictions += 1

            # Write back to backing store if dirty
            if victim_entry.dirty:
                print(f"[WRITE-BACK] Page {victim_page} is dirty, saving to backing store")
                self.backing_store[victim_page] = bytearray(
                    self.physical_memory.frames[frame_no]
                )

            # Mark victim as not present
            victim_entry.present = False
            victim_entry.frame = None
            victim_entry.dirty = False

            # Remove from reverse mapping
            del self.frame_to_page[frame_no]

        # Load page from backing store if it exists, otherwise zero it
        if page_no in self.backing_store:
            print(f"[LOAD] Loading page {page_no} from backing store into frame {frame_no}")
            self.physical_memory.frames[frame_no][:] = self.backing_store[page_no]
        else:
            print(f"[ZERO] Initializing page {page_no} in frame {frame_no}")
            self.physical_memory.frames[frame_no][:] = bytearray(PAGE_SIZE)

        # Update page table entry
        entry.frame = frame_no
        entry.present = True
        entry.dirty = False

        # Add to FIFO queue and reverse mapping
        self.fifo_queue.append(page_no)
        self.frame_to_page[frame_no] = page_no

    def read_byte(self, vaddr: int) -> int:
        """
        Read a byte from a virtual address.
        Performs address translation and handles page faults.
        """
        # Address translation: split virtual address into page number and offset
        page_no = vaddr // PAGE_SIZE
        offset = vaddr % PAGE_SIZE

        # Validate virtual address
        if page_no >= VIRTUAL_PAGES:
            raise ValueError(f"Virtual address {vaddr} out of range")

        # Ensure page is in RAM
        self._ensure_in_ram(page_no)

        # Get physical frame and read byte
        entry = self.page_table.get_entry(page_no)
        frame_no = entry.frame

        value = self.physical_memory.frames[frame_no][offset]
        print(f"[READ] vaddr={vaddr} (page={page_no}, offset={offset}) -> frame={frame_no} -> value={value}")

        return value

    def write_byte(self, vaddr: int, value: int):
        """
        Write a byte to a virtual address.
        Performs address translation, handles page faults, and sets dirty bit.
        """
        # Address translation
        page_no = vaddr // PAGE_SIZE
        offset = vaddr % PAGE_SIZE

        # Validate virtual address and value
        if page_no >= VIRTUAL_PAGES:
            raise ValueError(f"Virtual address {vaddr} out of range")
        if not (0 <= value <= 255):
            raise ValueError(f"Value {value} must be a byte (0-255)")

        # Ensure page is in RAM
        self._ensure_in_ram(page_no)

        # Get physical frame and write byte
        entry = self.page_table.get_entry(page_no)
        frame_no = entry.frame

        self.physical_memory.frames[frame_no][offset] = value

        # Mark page as dirty (modified)
        entry.dirty = True

        print(f"[WRITE] vaddr={vaddr} (page={page_no}, offset={offset}) -> frame={frame_no} <- value={value}")

    def zero_page(self, page_no: int):
        """Initialize a page with zeros"""
        if page_no >= VIRTUAL_PAGES:
            raise ValueError(f"Page {page_no} out of range")

        # Ensure page is in RAM
        self._ensure_in_ram(page_no)

        # Get frame and zero it
        entry = self.page_table.get_entry(page_no)
        frame_no = entry.frame

        self.physical_memory.frames[frame_no][:] = bytearray(PAGE_SIZE)
        entry.dirty = True

        print(f"[ZERO] Page {page_no} zeroed in frame {frame_no}")

    def print_stats(self):
        """Print VM statistics"""
        print("\n=== VM Statistics ===")
        print(f"Page faults: {self.page_faults}")
        print(f"Page evictions: {self.page_evictions}")
        print(f"Pages in RAM: {len(self.fifo_queue)}")
        print(f"Free frames: {len(self.physical_memory.free_list)}")
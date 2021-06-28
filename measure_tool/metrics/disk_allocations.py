from collections import namedtuple
from sortedcontainers import SortedDict
from wildfrag.data import Volume
from wildfrag.util import parse_and_normalize_block_ranges
import unittest


Allocation = namedtuple("Allocation", ["end", "file", "part", "alloc_type"])
ALLOC_FILE = 1


class DiskAllocations:
    """ A class to help keep track of the placement of files on a disk. """

    """
    An example of a possible value of `allocations`:
        allocations: {
            0: { end: 64, file: 1, part: 0, alloc_type: ALLOC_FILE },
            64: { end: 96, file: 21, part: 0, alloc_type: ALLOC_FILE },
            1028: { end: 1528, file: 1, part: 1, alloc_type: ALLOC_FILE }
        }
    """
    allocations: SortedDict

    def __init__(self):
        self.allocations = SortedDict()

    def __iter__(self):
        return self.allocations.__iter__()

    def __getitem__(self, alloc_start):
        return self.allocations.get(alloc_start)

    def add(self, range_begin, range_end, file, part, alloc_type=ALLOC_FILE):
        """ Add an allocation. """
        assert (range_begin < range_end)
        assert (not self.is_range_occupied(range_begin, range_end))

        self.allocations[range_begin] = \
            Allocation(range_end, file, part, alloc_type)

    def find_allocation(self, byte: int):
        """ Find the allocation that the parameter `byte` is inside of. """

        # Find either the allocation whose range_begin is `byte` or the nearest
        # allocation that begins below `byte`.
        found = self.allocations.bisect_right(byte) - 1
        if found == -1:
            return None
        allocation = self.allocations.peekitem(index=found)

        # Fail if `byte` is outside of the range of the found allocation...
        if byte >= allocation[1].end:
            return None

        return allocation

    def find_in_range(self, range_begin, range_end):
        """ Find an allocation within the given range.
        Returns None or the last allocation within the range.
        """
        # Find the allocation whose range_begin is the nearest below `range_end`
        found = self.allocations.bisect_left(range_end) - 1
        if found == -1:
            return None
        allocation = self.allocations.peekitem(index=found)

        # Fail if the found allocation does not overlap the given range.
        if allocation[0] < range_begin and allocation[1].end <= range_begin:
            return None

        return allocation

    def is_allocated(self, byte: int):
        """ Check whether the parameter `byte` is already allocated. """
        return self.find_allocation(byte) is not None

    def is_range_occupied(self, range_begin, range_end):
        """ Check if the parameter range is already (partially) allocated """
        return self.find_in_range(range_begin, range_end) is not None


def get_disk_allocations(volume: Volume):
    """ Create a DiskAllocations datastructure from a given Volume """
    allocs = DiskAllocations()

    for file_id, file in enumerate(volume.files):
        byte_ranges = parse_and_normalize_block_ranges(file.blocks)
        for part_number, byte_range in enumerate(byte_ranges):
            # Skip empty byte ranges (this actually occurs in WildFrag) and
            # skip ranges that are already occupied (this also actually occurs).
            # Examples of overlapping ranges: file 13005187 and 13171573
            if byte_range[0] != byte_range[1]\
               and not allocs.is_range_occupied(byte_range[0], byte_range[1]):
                allocs.add(byte_range[0], byte_range[1], file_id, part_number)

    return allocs


class __Tests(unittest.TestCase):
    allocs: DiskAllocations

    def setUp(self):
        self.allocs = DiskAllocations()
        self.allocs.add(0, 10, 0, 0)
        self.allocs.add(20, 25, 1, 0)
        self.allocs.add(10, 20, 2, 0)
        self.allocs.add(26, 27, 3, 0)

    def test__is_allocated(self):
        allocs = self.allocs
        self.assertTrue(allocs.is_allocated(0))
        self.assertTrue(allocs.is_allocated(1))
        self.assertTrue(allocs.is_allocated(9))
        self.assertTrue(allocs.is_allocated(10))
        self.assertTrue(allocs.is_allocated(20))
        self.assertFalse(allocs.is_allocated(-1))
        self.assertFalse(allocs.is_allocated(25))
        self.assertFalse(allocs.is_allocated(27))

    def test__find_in_range(self):
        allocs = self.allocs
        found = allocs.find_in_range(1, 20)
        self.assertEqual(2, found[1].file)



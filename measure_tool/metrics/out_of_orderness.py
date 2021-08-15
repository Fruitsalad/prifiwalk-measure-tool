from wildfrag.data import *
from wildfrag.util import *
import unittest


def count_out_of_order_gaps(file: File):
    # Parse the block ranges...
    assert (file.blocks is not None)
    block_ranges = parse_and_normalize_block_ranges(file.blocks)
    assert (len(block_ranges) > 1)
    assert (len(block_ranges) == file.num_gaps + 1)

    # Count the amount of out-of-order blocks...
    out_of_order_total = 0

    for i in range(1, len(block_ranges)):
        this_range = block_ranges[i]
        prev_range = block_ranges[i - 1]
        is_out_of_order = (this_range[0] < prev_range[1])

        if is_out_of_order:
            out_of_order_total += 1

    return out_of_order_total


def calc_aggregate_out_of_orderness(volume: Volume):
    gaps_total = 0
    out_of_order_gaps_total = 0

    for file in volume.files:
        if file.num_gaps is None or file.num_gaps == 0:
            continue
        gaps_total += file.num_gaps
        out_of_order_gaps_total += count_out_of_order_gaps(file)

    if gaps_total == 0:
        return 0
    return out_of_order_gaps_total / gaps_total


def calc_out_of_orderness(file: File):
    if file.num_gaps is None or file.num_gaps == 0:
        return 0

    return count_out_of_order_gaps(file) / file.num_gaps


class __Tests(unittest.TestCase):
    def test__count_out_of_order_blocks(self):
        blocks = "10 - 50 160 - 161 120 - 130 85 - 86"

        now = datetime.datetime.now()
        file = File(
            id=1,
            volume_id=1,
            extension="txt",
            extension_len=3,
            mtime=now,
            ctime=now,
            atime=now,
            crtime=now,
            size=100,
            blocks=blocks,
            num_blocks=3,
            num_gaps=3,
            sum_gaps_bytes=100,
            sum_gaps_blocks=4,
            fragmented=True,
            backward=True,
            num_backward=2,
            resident=False,
            fs_compressed=False,
            sparse=False,
            linearconsecutive=False,
            hardlink_id=None,
            num_hardlink=None,
            fs_seq=0,
            fs_nlink=0,
            fs_inode=0
        )

        self.assertEqual(2, count_out_of_order_gaps(file))


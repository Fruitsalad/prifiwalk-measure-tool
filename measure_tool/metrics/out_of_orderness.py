from wildfrag.data import *
from wildfrag.util import *


def count_out_of_order_blocks(file: File):
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
        is_out_of_order = (this_range[0] > prev_range[1])

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
        out_of_order_gaps_total += count_out_of_order_blocks(file)

    if gaps_total == 0:
        return 0
    return out_of_order_gaps_total / gaps_total


def calc_out_of_orderness(file: File):
    if file.num_gaps is None or file.num_gaps == 0:
        return 0

    return count_out_of_order_blocks(file) / file.num_gaps

from measure_tool.wildfrag_data import *


def __get_false(*ignored):
    return False


def calc_aggregate_layout_score(volume: Volume, is_ignored=__get_false):
    """
    The aggregate layout score is the fraction of blocks of a filesystem that are
    fragmented, ignoring files of one block (or less) and the first block of each
    file.
    1 means the filesystem is laid out perfectly.
    0 means the filesystem is absolutely completely fragmented.
    Most of the time the score is either 1 or close to 1.
    :param is_ignored: Lambda function that determines whether a file will
                       be ignored or not.
    """
    max_gaps_total = 0  # The largest possible amount of gaps on this filesystem
    gaps_total = 0

    for file in volume.files:
        if not is_ignored(file) \
           and file.num_blocks is not None \
           and file.num_blocks > 1:
            max_gaps_total += file.num_blocks - 1
            gaps_total += file.num_gaps

    return 1 - gaps_total / max_gaps_total


def calc_layout_score(file: File):
    """
    The fraction of blocks of a file that are fragmented, ignoring the first
    block.
    """
    if file.num_blocks is None or file.num_blocks < 2:
        return 1

    return 1 - file.num_gaps / (file.num_blocks - 1)



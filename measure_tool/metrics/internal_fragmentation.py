from wildfrag.data import *


def calc_avg_internal_frag(files: list):
    file: File
    sum_internal_frag = 0
    fraggable_file_count = 0

    for file in files:
        if file.num_blocks is not None and file.num_blocks > 1:
            fraggable_file_count += 1
            internal_frag = file.num_gaps / (file.num_blocks - 1)
            sum_internal_frag += internal_frag

    return sum_internal_frag / fraggable_file_count
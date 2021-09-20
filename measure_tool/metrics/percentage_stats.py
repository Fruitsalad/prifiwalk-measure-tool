from dataclasses import dataclass, field
from metrics.out_of_orderness import count_out_of_order_gaps


@dataclass
class VolumeStats:
    # Note: Type annotations are not optional here.
    # dataclass-csv doesn't recognize variables without a type annotation (for
    # some reason) and won't include them in the .csv if you leave it out.
    total_files: int = 0
    fraggable_files: int = 0
    fragmented_files: int = 0
    empty_files: int = 0
    resident_files: int = 0
    sparse_files: int = 0
    compressed_files: int = 0
    hardlinks: int = 0
    files_with_blocks: int = 0
    files_without_blocks: int = 0
    total_blocks: int = 0
    num_gaps: int = 0
    sum_gap_sizes: int = 0
    backwards_gaps: int = 0
    sum_file_sizes: int = 0

    def pretty_print(self):
        # To be honest the outputs of this aren't all that pretty.
        return (f"{self.total_files=}\n"
                f"{self.fraggable_files=}\n"
                f"{self.fragmented_files=}\n"
                f"{self.empty_files=}\n"
                f"{self.resident_files=}\n"
                f"{self.sparse_files=}\n"
                f"{self.compressed_files=}\n"
                f"{self.hardlinks=}\n"
                f"{self.files_with_blocks=}\n"
                f"{self.files_without_blocks=}\n"
                f"{self.total_blocks=}\n"
                f"{self.num_gaps=}\n"
                f"{self.sum_gap_sizes=}\n"
                f"{self.backwards_gaps=}\n"
                f"{self.sum_file_sizes=}\n")


def calc_various_stats(files):
    """ Derives VolumeStats from the given collection of files.
        Return both a VolumeStats for the whole system and a dictionary
        of VolumeStats for each individual filetype. """
    filetypes = {"[filtered]": VolumeStats()}
    all_files = VolumeStats()
    all_files.total_files = len(files)

    for file in files:
        filetype = file.extension
        if filetype not in filetypes or filetypes[filetype] is not VolumeStats:
            filetypes[filetype] = VolumeStats()
        this_type = filetypes[filetype]

        this_type.total_files += 1

        if file.size is not None:
            all_files.sum_file_sizes += file.size
            this_type.sum_file_sizes += file.size

        if file.fragmented:
            all_files.fragmented_files += 1
            this_type.fragmented_files += 1

        if file.sparse:
            all_files.sparse_files += 1
            this_type.sparse_files += 1

        if file.size is not None and file.size == 0:
            all_files.empty_files += 1
            this_type.empty_files += 1

        if file.fs_compressed:
            all_files.compressed_files += 1
            this_type.compressed_files += 1

        if file.hardlink_id is not None:
            all_files.hardlinks += 1
            this_type.hardlinks += 1

        if file.resident:
            all_files.resident_files += 1
            this_type.resident_files += 1
            all_files.files_without_blocks += 1
            this_type.files_without_blocks += 1
        elif file.num_blocks is None or file.num_blocks == 0:
            all_files.files_without_blocks += 1
            this_type.files_without_blocks += 1
        else:
            all_files.files_with_blocks += 1
            this_type.files_with_blocks += 1
            all_files.total_blocks += file.num_blocks
            this_type.total_blocks += file.num_blocks
            if file.num_blocks > 1:
                all_files.fraggable_files += 1
                this_type.fraggable_files += 1
            if file.num_gaps >= 1:
                all_files.num_gaps += file.num_gaps
                this_type.num_gaps += file.num_gaps
                all_files.sum_gap_sizes += file.sum_gaps_bytes
                this_type.sum_gap_sizes += file.sum_gaps_bytes
                out_of_order_gaps = count_out_of_order_gaps(file)
                all_files.backwards_gaps += out_of_order_gaps
                this_type.backwards_gaps += out_of_order_gaps

    return all_files, filetypes

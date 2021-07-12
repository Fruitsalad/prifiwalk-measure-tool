from dataclasses import dataclass, field
from metrics.out_of_orderness import count_out_of_order_blocks


@dataclass
class VolumeStats:
    total_files: int = 0
    fraggable_files = 0
    fragmented_files = 0
    empty_files = 0
    resident_files = 0
    sparse_files = 0
    compressed_files = 0
    hardlinks = 0
    files_with_blocks = 0
    files_without_blocks = 0
    total_blocks = 0
    num_gaps = 0
    sum_gap_sizes = 0
    backwards_gaps = 0
    out_of_order_gaps = 0
    
    def add(self, other):
        self.total_files += other.total_files
        self.fraggable_files = other.fraggable_files
        self.fragmented_files = other.fragmented_files
        self.empty_files = other.empty_files
        self.resident_files = other.resident_files
        self.sparse_files = other.sparse_files
        self.compressed_files = other.compressed_files
        self.hardlinks = other.hardlinks
        self.files_with_blocks = other.files_with_blocks
        self.files_without_blocks = other.files_without_blocks
        self.total_blocks = other.total_blocks
        self.num_gaps = other.num_gaps
        self.sum_gap_sizes = other.sum_gap_sizes
        self.backwards_gaps = other.backwards_gaps

    def pretty_print(self):
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
                f"{self.backwards_gaps=}\n")


def calc_various_stats(files):
    filetypes = {"[filtered]": VolumeStats()}
    all_files = VolumeStats()
    all_files.total_files = len(files)

    for file in files:
        filetype = file.extension
        if filetype not in filetypes or filetypes[filetype] is not VolumeStats:
            filetypes[filetype] = VolumeStats()
        this_type = filetypes[filetype]

        this_type.total_files += 1

        if file.fragmented:
            all_files.fragmented_files += 1
            this_type.fragmented_files += 1

        if file.sparse:
            all_files.sparse_files += 1
            this_type.sparse_files += 1

        if file.size is None or file.size == 0:
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
                out_of_order_gaps = count_out_of_order_blocks(file)
                all_files.backwards_gaps += out_of_order_gaps
                this_type.backwards_gaps += out_of_order_gaps

    return all_files, filetypes




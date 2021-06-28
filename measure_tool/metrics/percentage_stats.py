from dataclasses import dataclass, field


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

    def stringify(self):
        return (f"{self.total_files=}\n"
                f"{self.fraggable_files =}\n"
                f"{self.fragmented_files =}\n"
                f"{self.empty_files =}\n"
                f"{self.resident_files =}\n"
                f"{self.sparse_files =}\n"
                f"{self.compressed_files =}\n"
                f"{self.hardlinks =}\n"
                f"{self.files_with_blocks =}\n"
                f"{self.files_without_blocks =}\n"
                f"{self.total_blocks =}\n")


def calc_various_stats(files):
    filetypes = {"[filtered]": VolumeStats}
    all_files = VolumeStats
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

    return all_files, filetypes




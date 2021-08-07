import datetime
from dataclasses import dataclass, field


@dataclass
class System:
    id: int
    start_run: datetime
    end_run: datetime
    os: str

    devices: list = field(default_factory=list)


@dataclass
class StorageDevice:
    id: int
    system_id: int
    model: str
    hwid: str
    size: int
    rotational: bool
    hotplug: bool

    volumes: list = field(default_factory=list)


@dataclass
class Volume:
    id: int
    storage_device_id: int
    fs_type: str
    size: int
    used: int
    free: int
    block_size: int
    flags: str

    files: list = field(default_factory=list)
    notes: list = field(default_factory=list)


# NOTE: Files are different from the raw WildFrag data because the WildFrag
# class normalizes all hardlink references to the same file into one File.
@dataclass
class File:
    id: int
    volume_id: int
    extension: str
    extension_len: int
    mtime: datetime
    ctime: datetime
    atime: datetime
    crtime: datetime
    size: int
    blocks: any
    num_blocks: int
    num_gaps: int
    sum_gaps_bytes: int
    sum_gaps_blocks: int
    fragmented: bool
    backward: bool
    num_backward: int
    resident: bool
    fs_compressed: bool
    sparse: bool
    linearconsecutive: bool
    hardlink_id: int
    num_hardlink: int
    fs_seq: int
    fs_nlink: int
    fs_inode: int


@dataclass
class VolumeNote:
    id: int
    volume_id: int
    note: str

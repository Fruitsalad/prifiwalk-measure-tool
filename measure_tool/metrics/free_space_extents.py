from wildfrag.data import *
from metrics.bins import Bins
from metrics.disk_allocations import get_disk_allocations


def get_free_space_sections(disk_allocations, volume_size):
    """ This assumes that every byte that isn't claimed in disk_allocations is
    free. This assumption isn't true, but it's the best that can be done with
    the available data within the current time constraints. """
    prev_end = 0

    for alloc_start in disk_allocations:
        (alloc_end, _, _, _) = disk_allocations[alloc_start]

        if alloc_start != prev_end:
            yield prev_end, alloc_start

    if prev_end != volume_size:
        yield prev_end, volume_size


def get_free_space_extents(volume: Volume):
    allocations = get_disk_allocations(volume)
    return get_free_space_extents_2(allocations, volume.size)


def get_free_space_extents_2(disk_allocations, volume_size):
    # Categories ranging from 8 KiB to 2 GiB, with one last category for even
    # larger sections.
    categories = [2**x for x in range(13, 32)]
    extents_histogram = Bins(categories)

    for section_start, section_end in \
            get_free_space_sections(disk_allocations, volume_size):
        section_size = section_end - section_start
        extents_histogram.add(section_size)

    return extents_histogram

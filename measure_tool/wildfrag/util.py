def get_each_volume(wildfrag):
    """ Iterate through all the volumes in the given database.
        This returns the datastructures `volume`, `system`, `device`
        and the indices `i_volume`, `i_system`, `i_device` """
    for (i_system,) in wildfrag.retrieve_system_ids():
        system = wildfrag.retrieve_system(i_system)

        for i_device, device in enumerate(system.devices):
            for i_volume, volume in enumerate(device.volumes):
                yield volume, system, device, i_volume, i_system, i_device


def parse_block_ranges(blocks_str: str):
    ranges = []
    current_position = 0

    while True:
        # Find the first and last character of the first number...
        first_number__begin = current_position
        first_number__end = blocks_str.find(" - ", first_number__begin)

        # If there's no " - " to be found anymore, we've reached the end...
        if first_number__end == -1:
            break

        # Find the first and last character of the second number...
        second_number__begin = first_number__end + 3
        second_number__end = blocks_str.find(" ", second_number__begin)

        if second_number__end == -1:
            second_number__end = len(blocks_str)

        # Grab the number strings, convert them and store them...
        first_number = blocks_str[first_number__begin: first_number__end]
        second_number = blocks_str[second_number__begin: second_number__end]
        ranges.append((int(first_number), int(second_number)))

        # Continue on to the next range...
        current_position = second_number__end + 1

    return ranges


def normalize_block_ranges(block_ranges: list):
    """
    Sometimes, two subsequent block ranges in WildFrag's `blocks` string are
    contiguous and could be fused together. This function fuses them together.
    This function edits the list in-place and does not make a copy.
    """
    to_be_removed = []

    # Merge the ranges together...
    for i in range(len(block_ranges)):
        # If this_range and the next range are contiguous...
        i_next = i + 1
        while i_next < len(block_ranges) \
                and block_ranges[i][1] + 1 == block_ranges[i_next][0]:
            # Merge the ranges together...
            block_ranges[i] = (block_ranges[i][0], block_ranges[i_next][1])
            # Mark the next range as dead...
            block_ranges[i_next] = (-2, -2)
            to_be_removed.append(i_next)
            # Check again whether the next range is also contiguous...
            i_next += 1

    # Delete ranges that were merged into other ranges...
    for removed_index in reversed(to_be_removed):
        block_ranges.pop(removed_index)

    return block_ranges


def parse_and_normalize_block_ranges(blocks_str: str):
    """ Tiny helper function. This is usually what you want. """
    return normalize_block_ranges(parse_block_ranges(blocks_str))

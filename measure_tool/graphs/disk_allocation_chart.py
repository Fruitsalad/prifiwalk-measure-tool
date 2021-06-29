from math import floor
import matplotlib.cm
import matplotlib.pyplot as pyplot
from matplotlib.patches import Rectangle


def draw_sampled_disk_allocation_chart(allocations, disk_size, samples=4000):
    """ Draw a disk allocation chart. This takes a number of samples of disk
    allocations and draws a rectangle for each sample. """

    # Note that this does not merge rectangles together when two samples are
    # within the same allocation, so it's not perfectly optimized.

    figure, axes = pyplot.subplots(figsize=(10, 1))
    axes.xaxis.set_visible(False)
    axes.yaxis.set_visible(False)
    axes.set_xlim(0, disk_size)
    colormap = matplotlib.cm.get_cmap("nipy_spectral")  # we use dark colors

    # the size of a single sample in bytes
    sample_size = disk_size / samples

    # For each sample...
    for sample in range(samples):
        location = floor((sample / samples) * disk_size)

        # Find the allocation that occupies the location of this sample...
        found = allocations.find_allocation(location)
        if found is None:
            continue

        # Draw the sample...
        (_, (_, file, part, _)) = found
        # choose a color...
        color_number = (file / 1000) % 1.0
        color = colormap(color_number)
        # draw the rectangle...
        rectangle = Rectangle((location, 0), sample_size, 1,
                              facecolor=color)
        axes.add_patch(rectangle)

    return figure


def draw_complete_disk_allocation_chart(disk_allocations, disk_size):
    """
    This draws a complete disk allocation chart. The problem with that is that
    it will contain several hundreds of thousands of rectangles which will take
    matplotlib quite a while to render. Running this requires about 6 GB of
    memory last I tried.

    In practice, the level of detail of this isn't any better than the sampled
    version, so you should really just use the sampled version.
    """
    figure, axes = pyplot.subplots(figsize=(10, 1))
    axes.xaxis.set_visible(False)
    axes.yaxis.set_visible(False)
    axes.set_xlim(0, disk_size)

    colormap = matplotlib.cm.get_cmap("nipy_spectral")  # we use dark colors

    # For each allocation...
    for alloc_start in disk_allocations:
        (alloc_end, file, part, alloc_type) = disk_allocations[alloc_start]
        alloc_size = alloc_end - alloc_start

        # Choose a color...
        color_number = (file / 1000) % 1.0
        color = colormap(color_number)

        # Draw a rectangle...
        rectangle = Rectangle((alloc_start, 0), alloc_size, 1,
                              facecolor=color)
        axes.add_patch(rectangle)

    return figure

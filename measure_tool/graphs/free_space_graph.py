import matplotlib.pyplot as pyplot
from metrics.bins import Bins
from matplotlib.ticker import PercentFormatter


def draw_free_space_graph(free_space_section_bins: Bins):
    # Determine the total size of the sections in each bin...
    bin_sizes = [0 for _ in free_space_section_bins]

    for bin_number, bin_threshold in enumerate(free_space_section_bins):
        section_sizes = free_space_section_bins[bin_threshold]
        bin_sizes[bin_number] = sum(section_sizes)

    total_free_space = sum(bin_sizes)
    space_fractions = [bin_size / total_free_space for bin_size in bin_sizes]

    # Draw the graph...
    x_ticks = range(0, len(space_fractions))
    x_labels = ["8K", "16K", "32K", "64K", "128K", "256K",
                "512K", "1M", "2M", "4M", "8M", "16M",
                "64M", "128M",
                "256M", "512M", "1G", "2G", ">2G"]

    figure, axes = pyplot.subplots(figsize=(10, 1))
    axes.bar(x_ticks, space_fractions, 0.9)
    axes.set_xticks(x_ticks)
    axes.set_xticklabels(x_labels)
    axes.set_ylabel("Percentage of free space extents")
    axes.set_yscale("log")
    axes.set_ylim(0.001, 1)
    axes.set_title("Free space extent sizes")
    axes.yaxis.set_major_formatter(PercentFormatter(xmax=1, decimals=1))
    axes.grid(which="both", axis="y", color="black", alpha=0.1)

    return figure

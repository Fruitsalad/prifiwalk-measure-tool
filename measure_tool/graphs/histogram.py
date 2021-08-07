import matplotlib.pyplot as pyplot
import csv
from metrics.bins import Bins
from matplotlib.ticker import PercentFormatter


def export_histogram_to_csv(bins: Bins, filename):
    keys = [key for key in bins.bins.keys()]
    bin_sizes = [len(bin) for bin in bins.bins.values()]
    total_size = sum(bin_sizes)
    size_fractions = [bin_size / total_size for bin_size in bin_sizes]

    with open(filename, 'w', newline='') as file:
        writer = csv.writer(file)
        for i in range(0, len(keys)):
            writer.writerow((keys[i], size_fractions[i], bin_sizes[i]))


def draw_histogram(bins: Bins, title=None):
    keys = [key for key in bins.bins.keys()]
    bin_sizes = [len(bin) for bin in bins.bins.values()]
    total_size = sum(bin_sizes)
    size_fractions = [bin_size / total_size for bin_size in bin_sizes]

    # Generate a list of labels...
    labels = ["" for _ in keys]

    if len(labels) > 1:
        labels[0] = f"below\n{keys[0]}"
        labels[-1] = f"{keys[-2]}\nand up"

        for i in range(1, len(labels) - 1):
            labels[i] = f"{keys[i-1]}\nto {keys[i]}"

    # Draw the graph...
    x_ticks = range(0, len(size_fractions))
    x_labels = labels

    figure, axes = pyplot.subplots(figsize=(15, 10))
    axes.bar(x_ticks, size_fractions, 0.9)
    axes.set_xticks(x_ticks)
    axes.set_xticklabels(x_labels)
    axes.set_ylim(0.001, 1)
    if title is not None:
        axes.set_title(title)
    axes.yaxis.set_major_formatter(PercentFormatter(xmax=1, decimals=1))
    axes.grid(which="both", axis="y", color="black", alpha=0.1)

    return figure


def draw_histogram_from_dict(dict, title=None):
    raw_values = [x for x in dict.values()]
    labels = [x for x in dict.keys()]

    total = sum(raw_values)
    values = [x / total for x in raw_values]

    # Draw the graph...
    x_ticks = range(0, len(values))
    x_labels = labels

    figure, axes = pyplot.subplots(figsize=(15, 10))
    axes.bar(x_ticks, values, 0.9)
    axes.set_xticks(x_ticks)
    axes.set_xticklabels(x_labels)
    axes.set_ylim(0.001, 1)
    if title is not None:
        axes.set_title(title)
    axes.yaxis.set_major_formatter(PercentFormatter(xmax=1, decimals=1))
    axes.grid(which="both", axis="y", color="black", alpha=0.1)


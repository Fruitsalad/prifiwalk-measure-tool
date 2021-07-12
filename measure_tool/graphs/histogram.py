import matplotlib.pyplot as pyplot
from metrics.bins import Bins
from matplotlib.ticker import PercentFormatter


def draw_histogram(bins: Bins, title=None):
    raw_data = [len(x) for x in bins.bins.values()]
    keys = [x for x in bins.bins.keys()]
    labels = ["" for _ in keys]

    # Set the last label to "≥x"
    if len(labels) > 1:
        labels[0] = f"below\n{keys[0]}"
        labels[-1] = f"{keys[-2]}\nand up"

        for i in range(1, len(labels) - 1):
            labels[i] = f"{keys[i-1]}\nto {keys[i]}"

    total = sum(raw_data)
    data = [x / total for x in raw_data]

    # Draw the graph...
    x_ticks = range(0, len(data))
    x_labels = labels

    figure, axes = pyplot.subplots(figsize=(15, 10))
    axes.bar(x_ticks, data, 0.9)
    axes.set_xticks(x_ticks)
    axes.set_xticklabels(x_labels)
    axes.set_ylim(0.001, 1)
    if title is not None:
        axes.set_title(title)
    axes.yaxis.set_major_formatter(PercentFormatter(xmax=1, decimals=1))
    axes.grid(which="both", axis="y", color="black", alpha=0.1)

    return figure

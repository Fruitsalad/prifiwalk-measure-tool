import argparse
import csv

from wildfrag.util import *
from wildfrag.wildfrag import WildFrag
from metrics.bins import *


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('dbfile')
    args = parser.parse_args()
    wildfrag = WildFrag(args.dbfile)
    sizes = [0.001] + [2**i for i in range(9, 40)]

    amount_of_volumes = 0
    filesize_bins = CounterBins(sizes)

    for volume, _, _, _, _, _ in get_each_volume(wildfrag):
        if volume.size > 25_000_000_000 and volume.fs_type == "ntfs":
            amount_of_volumes += 1
            for file in volume.files:
                if file.size is not None:
                    filesize_bins.add(file.size)

    for bin in filesize_bins:
        filesize_bins.bins[bin][0] /= amount_of_volumes
    print(filesize_bins.pretty_print())

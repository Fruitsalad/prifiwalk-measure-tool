import argparse
from os import makedirs

import gc

from dataclass_csv import DataclassWriter

from wildfrag.wildfrag import WildFrag
from metrics.out_of_orderness import *
from metrics.disk_allocations import *
from metrics.percentage_stats import *
from metrics.free_space_extents import *
from metrics.internal_fragmentation import *
from graphs.disk_allocation_chart import *
from graphs.histogram import *


VolumeTriplet = namedtuple("VolumeTriplet", ["system", "device", "volume"])

MODE_STATISTICS = "statistics"
MODE_CSV = "csv"

parser = argparse.ArgumentParser()
args = None
is_measuring_filetype_stats = True


def parse_args():
    parser.add_argument('mode',
                        help='Determines the mode of operation. ' +
                             f'"{MODE_STATISTICS}" to print statistics' +
                             f'"{MODE_CSV}" to generate CSV files',
                        type=str)
    parser.add_argument('dbfile',
                        help='The path to the database file ' +
                             'generated by PriFiwalk.')
    parser.add_argument('--filestats',
                        help='Enables saving filetype statistics. ' +
                             'This is not supported by all modes of operation.',
                        dest='filestats',
                        action='store_true',
                        default=False)
    return parser.parse_args()


def get_each_volume(wildfrag):
    """ Iterate through all the volumes in the given database.
        This returns the datastructures `volume`, `system`, `device`
        and the indices `i_volume`, `i_system`, `i_device` """
    for (i_system,) in wildfrag.retrieve_system_ids():
        system = wildfrag.retrieve_system(i_system)

        for i_device, device in enumerate(system.devices):
            for i_volume, volume in enumerate(device.volumes):
                yield volume, system, device, i_volume, i_system, i_device


def draw_many_disk_allocation_charts(
        volumes: list, names=None, folder="./disk allocations"
):
    """ Draw a disk allocation chart for each given volume. """
    # This function is unused but I can't bring myself to delete it.

    if names is None:
        names = []

    for i, volume in enumerate(volumes):
        allocs = get_disk_allocations(volume)
        figure = draw_sampled_disk_allocation_chart(allocs, volume.size, 2000)

        if i < len(names):
            name = names[i]
        else:
            name = f"chart_{i}"

        file = f"{folder}/{name}"

        pyplot.savefig(file)


def calc_aggregate_layout_score_2(stats: VolumeStats):
    # Note: `_2` to prevent collision with the function in `layout_score.py`
    if stats.total_blocks <= stats.files_with_blocks:
        return 1
    return 1.0 - (stats.num_gaps / (stats.total_blocks - stats.files_with_blocks))


def calc_aggregate_out_of_orderness(stats: VolumeStats):
    if stats.num_gaps == 0:
        return 0
    return stats.backwards_gaps / stats.num_gaps


def calc_avg_out_of_orderness(files: list):
    sum_ooo = 0
    fragmented_files = 0

    for file in files:
        if file.num_gaps is not None and file.num_gaps > 1:
            fragmented_files += 1
            ooo = file.num_backward / file.num_gaps
            sum_ooo += ooo

    if fragmented_files == 0:
        return 0

    return sum_ooo / fragmented_files


def derive_fullness(volume):
    # We used to estimate the fullness when volume.used was None, but the
    # estimates turned out to be rather inaccurate (4 GB inaccurate on average)
    assert volume.used is not None
    return volume.used / volume.size


def print_statistics(wildfrag):
    """ Print a bunch of statistics on the commandline.
        If you want to import the outputs into Excel or Calc you should
        paste it into a code editor and run a regex to filter out
        the variable names. """
    for volume, _, _, i_vol, i_sys, i_dev in get_each_volume(wildfrag):
        size_in_GB = volume.size / 1_000_000_000
        fullness = derive_fullness(volume)

        # Generate statistics...
        general_stats, filetype_stats = calc_various_stats(volume.files)
        layout_score = calc_aggregate_layout_score_2(general_stats)
        aggregate_ooo = calc_aggregate_out_of_orderness(general_stats)
        average_ooo = calc_avg_out_of_orderness(volume.files)
        avg_internal_frag = calc_avg_internal_frag(volume.files)

        gap_size_avg = 0
        if general_stats.num_gaps != 0:
            gap_size_avg = general_stats.sum_gap_sizes / general_stats.num_gaps

        assert volume.size != 0
        normalized_gap_size_avg = gap_size_avg / volume.size

        print(f"Volume {i_vol} (System {i_sys}, device {i_dev})")
        print(f"{size_in_GB=}")
        print(f"{fullness=}")
        print(f"{layout_score=}")
        print(f"{aggregate_ooo=}")
        print(f"{normalized_gap_size_avg=}")
        print(f"{average_ooo=}")
        print(f"{avg_internal_frag=}")

        print(general_stats.pretty_print())
        if is_measuring_filetype_stats:
            for filetype, stats in filetype_stats.items():
                print(stats.pretty_print())

        gc.collect()


def generate_csv_files(wildfrag):
    # A "unique" identifier for each run of the program, so that old files
    # aren't overwritten when you run the program a second time.
    run_uid = f"{datetime.datetime.now():%y-%-m-%-d-%-H-%M-%S}"

    main_dir = f"./results/{run_uid}/"
    makedirs(main_dir, exist_ok=True)
    # Todo: filetype statistics

    main_csv_path = f"{main_dir}/main.csv"
    misc_csv_path = f"{main_dir}/misc.csv"

    with open(main_csv_path, 'w') as main_csv_file, \
         open(misc_csv_path, 'w') as misc_csv_file:
        main_csv = csv.writer(main_csv_file)

        main_csv.writerow(["volume", "system", "device", "HDD", "fs type",
                           "size in GB", "fullness",
                           "aggregate layout score", "aggregate out of orderness",
                           "gap size average",
                           "normalized gap size average",
                           "average internal fragmentation",
                           "average out of orderness"])

        misc_stats_list = []

        for volume, system, device, _, _, _ in get_each_volume(wildfrag):
            # Generate statistics...
            size_in_GB = volume.size / 1_000_000_000
            fullness = derive_fullness(volume)
            misc_stats, filetype_stats = calc_various_stats(volume.files)
            layout_score = calc_aggregate_layout_score_2(misc_stats)
            aggregate_ooo = calc_aggregate_out_of_orderness(misc_stats)
            average_ooo = calc_avg_out_of_orderness(volume.files)
            avg_internal_frag = calc_avg_internal_frag(volume.files)

            gap_size_avg = 0
            if misc_stats.num_gaps != 0:
                gap_size_avg = misc_stats.sum_gap_sizes / misc_stats.num_gaps

            assert volume.size != 0
            normalized_gap_size_avg = gap_size_avg / volume.size

            is_hdd = (device.rotational == 1)

            # Store data...
            main_csv.writerow(
                (volume.id, system.id, device.id, is_hdd, volume.fs_type,
                 size_in_GB, fullness, layout_score,
                 aggregate_ooo, gap_size_avg, normalized_gap_size_avg,
                 avg_internal_frag, average_ooo)
            )
            misc_stats_list.append(misc_stats)

        misc_csv = DataclassWriter(misc_csv_file, misc_stats_list, VolumeStats)
        misc_csv.write()


if __name__ == '__main__':
    args = parse_args()
    is_measuring_filetype_stats = args.filestats

    if args.mode == MODE_STATISTICS:
        # Note: simplifying this code by moving the "wildfrag = ..." line up is
        # not desirable, because then an "invalid database file" error could
        # be shown when there's be an "invalid mode of operation" error.
        # I'd prefer to show "invalid mode" first and "invalid database" second.
        wildfrag = WildFrag(args.dbfile)
        print_statistics(wildfrag)
    elif args.mode == MODE_CSV:
        wildfrag = WildFrag(args.dbfile)
        generate_csv_files(wildfrag)
    else:
        print("Error: You did not provide a valid argument for the mode of " +
              "operation.")
        print("Use \"-h\" as an argument for help.")


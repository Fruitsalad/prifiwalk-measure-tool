import argparse
import datetime
from os import mkdir, makedirs

from matplotlib import pyplot
import gc

from dataclass_csv import DataclassWriter

from wildfrag.wildfrag import WildFrag
from metrics.layout_score import *
from metrics.out_of_orderness import *
from metrics.disk_allocations import *
from metrics.percentage_stats import *
from metrics.free_space_extents import *
from graphs.disk_allocation_chart import *
from graphs.free_space_graph import *
from graphs.histogram import *


VolumeTriplet = namedtuple("VolumeTriplet", ["system", "device", "volume"])

MODE_HISTOGRAMS = "histograms"
MODE_STATISTICS = "statistics"
MODE_CSV = "csv"

parser = argparse.ArgumentParser()
args = None
is_measuring_filetype_stats = True


def parse_args():
    parser.add_argument('mode',
                        help='Determines the mode of operation. ' +
                             f'"{MODE_HISTOGRAMS}" to generate histograms, ' +
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
    for (i_system,) in wildfrag.retrieve_system_ids():
        system = wildfrag.retrieve_system(i_system)

        for i_device, device in enumerate(system.devices):
            for i_volume, volume in enumerate(device.volumes):
                yield volume, system, device, i_volume, i_system, i_device


def find_worst_layout_score(wildfrag):
    worst_layout_score = 2
    wls_vol = VolumeTriplet(0, 0, 0)  # wls = worst layout score

    for vol, sys, dev, i_vol, i_sys, i_dev in get_each_volume(wildfrag):
        size_in_GB = vol.size / 1000000000
        layout_score = calc_aggregate_layout_score(vol)
        oooness = calc_aggregate_out_of_orderness(vol)
        fullness = vol.used / vol.size

        is_worst = layout_score < worst_layout_score

        print(f"SYS {i_sys:<3d} DEV {i_dev} VOL {i_vol}  "
              f"SIZE {size_in_GB:8.3f} GB   "
              f"FULLNESS {fullness*100:8.3f}%"
              f"LAYOUT SCORE {layout_score:8.5f}   "
              f"OUT OF ORDERNESS {oooness:8.5f} " +
              (" <- worst so far " if is_worst else ""))

        if is_worst:
            worst_layout_score = layout_score
            wls_vol = VolumeTriplet(i_sys, i_dev, i_vol)

    print(f"WORST LAYOUT SCORE {worst_layout_score}  "
          f"ON SYS {wls_vol.system} DEV {wls_vol.device} VOL {wls_vol.volume}")


def draw_many_disk_allocation_charts(
        volumes: list, names=None, folder="./disk allocations"
):
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


def get_volume(wildfrag, system, device, volume):
    return wildfrag.retrieve_system(system).devices[device].volumes[volume]


def get_size_category(size_in_GB):
    if size_in_GB < 2:
        return "xxxs"
    elif size_in_GB < 25:
        return "xxs"
    elif size_in_GB < 100:
        return "xs"
    elif size_in_GB < 400:
        return "s"
    elif size_in_GB < 800:
        return "m"
    elif size_in_GB < 1600:
        return "l"

    return "xl"


def get_fullness_category(fullness):
    if fullness < 0.05:
        return "0.00-0.05"
    elif fullness < 0.35:
        return "0.05-0.35"
    elif fullness < 0.85:
        return "0.35-0.85"
    return "0.85-1.00"


def calc_aggregate_layout_score_2(stats):
    if stats.total_blocks <= stats.files_with_blocks:
        return 1
    return 1.0 - (stats.num_gaps / (stats.total_blocks - stats.files_with_blocks))


def calc_out_of_orderness(stats):
    if stats.num_gaps == 0:
        return 0
    return stats.backwards_gaps / stats.num_gaps


class SizeCat:
    def __init__(self):
        self.layout_scores = []
        self.ooo_scores = []
        self.gap_size_avgs = []
        self.norm_gap_size_avgs = []
        self.fullness_cats = {}


class FullnessCat:
    def __init__(self):
        self.layout_scores = []
        self.ooo_scores = []
        self.gap_size_avgs = []
        self.norm_gap_size_avgs = []


def derive_fullness(volume):
    if volume.used is not None:
        return volume.used / volume.size
    else:
        # This is not perfectly accurate, since it's only counting files
        # and not filesystem metadata, but it's the best we can do and probably
        # not all that bad.
        sum_file_sizes = 0
        for file in volume.files:
            if file.size is not None:
                sum_file_sizes += file.size
        return sum_file_sizes / volume.size


def print_statistics(wildfrag):
    for volume, _, _, i_vol, i_sys, i_dev in get_each_volume(wildfrag):
        size_in_GB = volume.size / 1_000_000_000
        fullness = derive_fullness(volume)

        # Generate statistics...
        general_stats, filetype_stats = calc_various_stats(volume.files)
        layout_score = calc_aggregate_layout_score_2(general_stats)
        out_of_orderness = calc_out_of_orderness(general_stats)

        gap_size_avg = 0
        if general_stats.num_gaps != 0:
            gap_size_avg = general_stats.sum_gap_sizes / general_stats.num_gaps

        assert volume.size != 0
        normalized_gap_size_avg = gap_size_avg / volume.size

        print(f"Volume {i_vol} (System {i_sys}, device {i_dev})")
        print("Size in GB, fullness, layout score, out of orderness, normalized gap size avg.:")
        print(size_in_GB)  # Putting each result on its own line makes it
        print(fullness)  # easier to copy paste them into LibreOffice Calc
        print(layout_score)
        print(out_of_orderness)
        print(normalized_gap_size_avg)

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
                           "aggregate layout score", "out of orderness",
                           "gap size average",
                           "normalized gap size average"])

        misc_stats_list = []

        for volume, system, device, _, _, _ in get_each_volume(wildfrag):
            # Generate statistics...
            size_in_GB = volume.size / 1_000_000_000
            fullness = derive_fullness(volume)
            misc_stats, filetype_stats = calc_various_stats(volume.files)
            layout_score = calc_aggregate_layout_score_2(misc_stats)
            out_of_orderness = calc_out_of_orderness(misc_stats)

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
                 out_of_orderness, gap_size_avg, normalized_gap_size_avg)
            )
            misc_stats_list.append(misc_stats)

        misc_csv = DataclassWriter(misc_csv_file, misc_stats_list, VolumeStats)
        misc_csv.write()


def generate_histograms(wildfrag):
    size_cats = {}

    # A "unique" identifier for each run of the program, so that old files
    # aren't overwritten when you run the program a second time.
    run_uid = f"{datetime.datetime.now():%y-%-m-%-d-%-H-%M-%S}"

    main_dir = f"./results/{run_uid}/"
    makedirs(main_dir, exist_ok=True)

    # Derive data...
    for volume, _, _, _, _, _ in get_each_volume(wildfrag):
        __derive_volume_statistics(volume, main_dir, size_cats)

    # Turn the data into histograms...
    for s_cat, s_data in size_cats.items():
        __generate_histogram_files(s_data, f"{main_dir}/{s_cat}")
        for f_cat, f_data in s_data.fullness_cats.items():
            __generate_histogram_files(f_data, f"{main_dir}/{s_cat}/{f_cat}")

    __create_size_and_fullness_histograms(size_cats, main_dir)


def __create_size_and_fullness_histograms(size_cats, main_dir):
    size_hist = {"xxxs": 0, "xxs": 0, "xs": 0, "s": 0, "m": 0, "l": 0, "xl": 0}

    for size_category, data in size_cats.items():
        size_hist[size_category] = len(data.layout_scores)

        fullness_hist = {"0.00-0.05": 0, "0.05-0.35": 0, "0.35-0.85": 0, "0.85-1.00": 0}
        for fullness_category, fullness_data in data.fullness_cats.items():
            fullness_hist[fullness_category] = len(fullness_data.layout_scores)

        figure = draw_histogram_from_dict(fullness_hist,
                       title="Histogram of fullness across filesystems")
        pyplot.savefig(f"{main_dir}/{size_category}/fullness_hist")
        pyplot.close(figure)

    figure = draw_histogram_from_dict(size_hist,
                                      title="Histogram of filesystem sizes")
    pyplot.savefig(f"{main_dir}/size_hist")
    pyplot.close(figure)


def __derive_volume_statistics(volume, main_dir, size_cats):
    """
    Derives a bunch of statistics from a volume, writes all statistics to a
    folder somewhere in main_dir and also saves the statistics to the
    appropriate size category in size_cats (for example, all volumes between
    400 GB and 800 GB have their statistics saved to the same category)
    """
    # (This function does a lot of different things and could probably be broken
    # up into multiple functions, but that's not a priority right now)

    size_in_GB = volume.size / 1_000_000_000
    size_category = get_size_category(size_in_GB)
    fullness = derive_fullness(volume)
    fullness_category = get_fullness_category(fullness)

    # Generate statistics...
    general_stats, filetype_stats = calc_various_stats(volume.files)
    layout_score = calc_aggregate_layout_score_2(general_stats)
    out_of_orderness = calc_out_of_orderness(general_stats)

    gap_size_avg = 0
    if general_stats.num_gaps != 0:
        gap_size_avg = general_stats.sum_gap_sizes / general_stats.num_gaps

    assert volume.size != 0
    normalized_gap_size_avg = gap_size_avg / volume.size

    # Write to file...
    volume_dir = f"{main_dir}/{size_category}/" + \
                 f"{fullness_category}/{volume.id}"
    makedirs(f"{volume_dir}", exist_ok=True)

    with open(f"{volume_dir}/stats", "x") as file:
        file.write(VolumeStats.pretty_print(general_stats))

    if is_measuring_filetype_stats:
        makedirs(f"{volume_dir}/filetypes", exist_ok=True)

        for filetype, stats in filetype_stats.items():
            with open(f"{volume_dir}/filetypes/type_{filetype}", "x") as file:
                file.write(VolumeStats.pretty_print(stats))

    # Add this volume's results to the data of its categories...
    # Note: cat = category
    if size_category not in size_cats:
        size_cats[size_category] = SizeCat()

    if fullness_category not in size_cats[size_category].fullness_cats:
        size_cats[size_category].fullness_cats[fullness_category] \
            = FullnessCat()

    size_cat_data = size_cats[size_category]
    fullness_data = size_cat_data.fullness_cats[fullness_category]

    size_cat_data.layout_scores.append(layout_score)
    fullness_data.layout_scores.append(layout_score)
    size_cat_data.ooo_scores.append(out_of_orderness)
    fullness_data.ooo_scores.append(out_of_orderness)
    size_cat_data.gap_size_avgs.append(gap_size_avg)
    fullness_data.gap_size_avgs.append(gap_size_avg)
    size_cat_data.norm_gap_size_avgs.append(normalized_gap_size_avg)
    fullness_data.norm_gap_size_avgs.append(normalized_gap_size_avg)

    # allocs = get_disk_allocations(volume)
    # free_space_extents = get_free_space_extents_2(allocs, volume.size)
    # -> extent size histogram -> numeric statistics
    # del allocs
    # del free_space_extents
    gc.collect()


def __generate_histogram_files(data, dir):
    """
    Generate a collection of histograms from `data` and save them to the folder
    `dir`. The parameter `data` can be either a SizeCat or a FullnessCat.
    """
    OOO_BIN_COUNT = 20
    NORM_GAP_BIN_COUNT = 20
    LAYOUT_SCORE_BIN_COUNT = 20

    layout_score_bins = ([0.001] +
                         [x / LAYOUT_SCORE_BIN_COUNT
                          for x in range(1, LAYOUT_SCORE_BIN_COUNT + 1)] +
                         [100])
    layout_score_bins_2 = [0.9, 0.99, 0.999, 0.9999,
                           0.99999, 0.999999, 1.0, 100]
    ooo_bins = ([0.001] +
                [x / OOO_BIN_COUNT for x in range(1, OOO_BIN_COUNT + 1)] +
                [100])
    norm_gap_bins = ([0.001] +
                     [x / NORM_GAP_BIN_COUNT
                      for x in range(1, NORM_GAP_BIN_COUNT + 1)] +
                     [100])

    layout_score_histogram = Bins(layout_score_bins)
    layout_score_histogram_2 = Bins(layout_score_bins_2)
    ooo_score_histogram = Bins(ooo_bins)
    norm_gap_size_avg_histogram = Bins(norm_gap_bins)

    for layout_score in data.layout_scores:
        layout_score_histogram.add(layout_score)
        layout_score_histogram_2.add(layout_score)
    for ooo_score in data.ooo_scores:
        ooo_score_histogram.add(ooo_score)
    for norm_gap_size_avg in data.norm_gap_size_avgs:
        norm_gap_size_avg_histogram.add(norm_gap_size_avg)

    with open(f"{dir}/layout_score", "x") as file:
        file.write(layout_score_histogram.pretty_print())
    with open(f"{dir}/out_of_orderness", "x") as file:
        file.write(ooo_score_histogram.pretty_print())
    with open(f"{dir}/normalized_gap_size_average", "x") as file:
        file.write(norm_gap_size_avg_histogram.pretty_print())

    def save(filename, histogram):
        pyplot.savefig(f"{dir}/{filename}")
        pyplot.close(histogram)  # Save some memory

    save("layout_score_hist",
         draw_histogram(layout_score_histogram,
                        title="Histogram of aggregate layout scores"))
    export_histogram_to_csv(layout_score_histogram, f"{dir}/layout.csv")

    save("layout_score_hist_2",
         draw_histogram(layout_score_histogram_2,
                        title="Histogram of aggregate layout scores"))
    export_histogram_to_csv(layout_score_histogram_2, f"{dir}/layout_2.csv")

    save("ooo_score_hist",
         draw_histogram(ooo_score_histogram,
                        title="Histogram of average out-of-orderedness"))
    export_histogram_to_csv(ooo_score_histogram, f"{dir}/ooo.csv")

    save("norm_gap_size_avg_hist",
         draw_histogram(norm_gap_size_avg_histogram,
                        title="Histogram of normalized average gap sizes"))
    export_histogram_to_csv(norm_gap_size_avg_histogram, f"{dir}/gap_size.csv")


if __name__ == '__main__':
    args = parse_args()
    is_measuring_filetype_stats = args.filestats

    if args.mode == MODE_HISTOGRAMS:
        # Note: simplifying this code by moving the "wildfrag = ..." line up is
        # not desirable, because then an "invalid database file" error could
        # be shown when there's be an "invalid mode of operation" error.
        # I'd prefer to show "invalid mode" first and "invalid database" second.
        wildfrag = WildFrag(args.dbfile)
        generate_histograms(wildfrag)
    elif args.mode == MODE_STATISTICS:
        wildfrag = WildFrag(args.dbfile)
        print_statistics(wildfrag)
    elif args.mode == MODE_CSV:
        wildfrag = WildFrag(args.dbfile)
        generate_csv_files(wildfrag)
    else:
        print("Error: You did not provide a valid argument for the mode of " +
              "operation.")
        print("Use \"-h\" as an argument for help.")


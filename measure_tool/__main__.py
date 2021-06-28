import argparse
import datetime
from os import mkdir, makedirs

from matplotlib import pyplot
import gc

from wildfrag.wildfrag import WildFrag
from metrics.layout_score import *
from metrics.out_of_orderness import *
from metrics.disk_allocations import *
from metrics.percentage_stats import *
from graphs.free_space_graph import *
from metrics.free_space_extents import *
from graphs.disk_allocation_chart import draw_sampled_disk_allocation_chart


args = None
VolumeTriplet = namedtuple("VolumeTriplet", ["system", "device", "volume"])


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('dbfile')
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


if __name__ == '__main__':
    args = parse_args()
    wildfrag = WildFrag(args.dbfile)

    # A "unique" identifier for each run of the program, so that old files aren't
    # overwritten when you run the program a second time.
    run_uid = f"{datetime.datetime.now():%y-%-m-%-d-%-H-%M-%S}"

    makedirs(f"./results/{run_uid}/filetypes", exist_ok=True)

    """
    volumes = [
        get_volume(wildfrag, 16, 0, 0),
        get_volume(wildfrag, 1, 0, 0),
        get_volume(wildfrag, 1, 1, 0)
    ]

    for volume in volumes:
        free_space_extents = get_free_space_extents(volumes[0])
        draw_free_space_graph(free_space_extents)
        #draw_many_disk_allocation_charts(volumes)
    """

    all_file_stats = VolumeStats()
    filetype_stats = {}

    with open(f"./results/{run_uid}/stats2", "x") as file:
        for volume, _, _, i_vol, i_sys, i_dev in get_each_volume(wildfrag):
            size_in_GB = volume.size / 1000000000
            layout_score = calc_aggregate_layout_score(volume)
            # out_of_orderness = calc_aggregate_out_of_orderness(volume)
            filecount = len(volume.files)

            if volume.used is not None:
                fullness = volume.used / volume.size
            else:
                fullness = -1

            msg = (f"SYS {i_sys:<3d} DEV {i_dev} VOL {i_vol}  "
                   f"SIZE {size_in_GB:8.3f} GB   "
                   f"FULLNESS {fullness*100:8.3f}%    "
                   f"FILECOUNT {filecount:8}    ")
                   #f"LAYOUT SCORE {layout_score:8.5f}   ")
                   #f"OUT OF ORDERNESS {out_of_orderness:8.5f}")
            print(msg)
            file.write(msg + "/n")

            new_all_file_stats, new_type_stats = calc_various_stats(volume.files)
            all_file_stats.add(new_all_file_stats)

            for filetype, new_stats in new_type_stats.items():
                if filetype in filetype_stats:
                    VolumeStats.add(filetype_stats[filetype], new_stats)
                else:
                    filetype_stats[filetype] = new_stats



            """
            name = f"sys {i_sys} dev {i_dev} vol {i_vol}"
            allocs = get_disk_allocations(volume)
            figure = draw_sampled_disk_allocation_chart(allocs, volume.size)
            pyplot.savefig(f"./figures/{name} allocation")
            pyplot.close(figure)
            free_space_extents = get_free_space_extents_2(allocs, volume.size)
            figure = draw_free_space_graph(free_space_extents)
            pyplot.savefig(f"./figures/{name} free space extents")
            pyplot.close(figure)
    
            # This program tends to use way too much memory without this.
            del allocs
            del free_space_extents
            del figure
            gc.collect()
            """

    with open(f"./results/{run_uid}/stats", "x") as file:
        file.write(VolumeStats.stringify(all_file_stats))

    for filetype, stats in filetype_stats.items():
        with open(f"./results/{run_uid}/filetypes/{filetype}", "x") as file:
            file.write(VolumeStats.stringify(stats))

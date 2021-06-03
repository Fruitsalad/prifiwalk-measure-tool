import argparse
from measure_tool.wildfrag import WildFrag
from metrics.layout_score import *
from metrics.out_of_orderness import *


args = None


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('dbfile')
    return parser.parse_args()


def find_worst_layout_score(wildfrag):
    worst_layout_score = 2
    wls_system = 0  # wls: "worst layout score"
    wls_device = 0
    wls_volume = 0

    for (i_system,) in wildfrag.retrieve_system_ids():
        system = wildfrag.retrieve_system(i_system)

        for i_device, device in enumerate(system.devices):
            for i_volume, volume in enumerate(device.volumes):
                size_in_GB = volume.size / 1000000000
                layout_score = calc_aggregate_layout_score(volume)
                oooness = calc_aggregate_out_of_orderness(volume)

                is_worst = layout_score < worst_layout_score

                print(f"SYS {i_system:<3d} DEV {i_device} VOL {i_volume}  "
                      f"SIZE {size_in_GB:8.3f} GB   "
                      f"LAYOUT SCORE {layout_score:8.5f}   "
                      f"OUT OF ORDERNESS {oooness:8.5f} " +
                      (" <- worst so far " if is_worst else ""))

                if is_worst:
                    worst_layout_score = layout_score
                    wls_system = i_system
                    wls_device = i_device
                    wls_volume = i_volume

    print(f"WORST LAYOUT SCORE {worst_layout_score}  "
          f"ON SYS {wls_system} DEV {wls_device} VOL {wls_volume}")


if __name__ == '__main__':
    args = parse_args()
    wildfrag = WildFrag(args.dbfile)
    system = wildfrag.retrieve_system(179)
    volume = system.devices[0].volumes[2]
    layout_score = calc_aggregate_layout_score(volume)
    out_of_orderness = calc_aggregate_out_of_orderness(volume)

    print(f"{layout_score = :<.4}")
    print(f"{out_of_orderness = :<.4}")

    find_worst_layout_score(wildfrag)

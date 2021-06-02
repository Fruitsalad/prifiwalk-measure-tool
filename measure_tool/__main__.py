import argparse
from measure_tool.wildfrag import WildFrag


args = None


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('dbfile')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    wildfrag = WildFrag(args.dbfile)
    system = wildfrag.retrieve_system(1)

    print(system)
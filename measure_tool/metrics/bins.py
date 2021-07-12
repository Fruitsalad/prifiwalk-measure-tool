from sortedcontainers import SortedDict, SortedKeysView
import unittest


class Bins:
    """
    This class groups the numbers that it is given into a number of bins,
    so that numbers of a similar size are in the same bin.

    In the context of the rest of this program, this is used to generate the
    data for histograms.
    """

    # A SortedDict containing all of the bins, with the maximum value + 1 of the
    # bin as the key and a list of elements as its value.
    bins: SortedDict

    def __init__(self, bin_categories: list):
        self.bins = SortedDict()
        for category in bin_categories:
            self.bins[category] = []

    def __iter__(self):
        return self.bins.__iter__()

    def __getitem__(self, key):
        return self.bins.get(key)

    def add(self, value):
        # Find the appropriate bin...
        key_index = self.bins.bisect_right(value)
        if key_index >= len(self.bins):
            key_index = len(self.bins) - 1

        # Put the value in the bin...
        self.bins.peekitem(index=key_index)[1].append(value)

    def pretty_print(self):
        result = ""

        for category, values in self.bins.items():
            result += f"{category} | {len(values)} |   {values}\n"

        return result


class __Tests(unittest.TestCase):
    bins: Bins

    def setUp(self):
        self.bins = Bins([5, 10, 12, 40, 50])
        self.bins.add(4)
        self.bins.add(11)
        self.bins.add(4)
        self.bins.add(12)
        self.bins.add(39)
        self.bins.add(50)
        self.bins.add(100)
        self.bins.add(-100)
        self.bins.add(0)


    def test__pretty_print(self):
        result = self.bins.pretty_print()
        self.assertEqual(result,
"""\
5 | 4 |   [4, 4, -100, 0]
10 | 0 |   []
12 | 1 |   [11]
40 | 2 |   [12, 39]
50 | 2 |   [50, 100]
""")

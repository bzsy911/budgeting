import itertools
import numpy as np


class Map:

    def __init__(self, df):
        self.df = df
        self.loc = self._get_map()
        self.finder = self._get_finder()

    def find(self, val, order=0):
        return self.finder[val][order]

    def get_value_by_intersection(self, row_val, col_val):
        row, _ = self.find(row_val)
        _, col = self.find(col_val)
        return self.loc[(row, col)]

    def get_value_by_direction(self, val, order, direction):
        return self.loc[tuple(map(sum, zip(self.find(val, order), direction)))]

    def get_values_below(self, title, index=0):
        title_loc = self.find(title, index)
        stuff = [[self.loc[(row, title_loc[1])], (row, title_loc[1])] for row in
                 range(title_loc[0] + 1, self.df.shape[0])]
        return list(itertools.dropwhile(lambda x: x[0] is None, stuff[::-1]))[::-1]

    def get_consecutive_value_below(self, title, index=0):
        title_loc = self.find(title, index)
        stuff = [[self.loc[(row, title_loc[1])], (row, title_loc[1])] for row in
                 range(title_loc[0] + 1, self.df.shape[0])]
        return list(itertools.takewhile(lambda x: not np.isnan(x[0]), stuff))

    def _get_map(self):
        row, col = self.df.shape
        return {(i, j): self.df.iloc[i, j] for i in range(row) for j in range(col)}

    def _get_finder(self):
        res = {}
        for loc in self.loc:
            if self.loc[loc] is None:
                continue
            if self.loc[loc] not in res:
                res[self.loc[loc]] = [loc]
            else:
                res[self.loc[loc]].append(loc)
        for val in res:
            res[val].sort()
        return res
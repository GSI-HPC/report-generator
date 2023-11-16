#!/usr/bin/env python3
#
# -*- coding: utf-8 -*-
#
# © Copyright 2023 GSI Helmholtzzentrum für Schwerionenforschung
#
# This software is distributed under
# the terms of the GNU General Public Licence version 3 (GPL Version 3),
# copied verbatim in the file "LICENCE".

from chart.base_chart import BaseChart

import numpy as np
from format import number_format

import matplotlib
# Force matplotlib to not use any X window backend.
matplotlib.use('Agg')


# TODO: One BarChart Implementation should be enough.
#       Use x1_label, x2_label, x1_values, x2_values..
class GroupFilesMigrationBarChart(BaseChart):

    def __init__(self, title, dataset, file_path, fs1_name, fs2_name):

        super(GroupFilesMigrationBarChart, self).__init__(
            title, dataset, file_path,
            x_label='Group',
            y_label='File Count')

        self.fs1_name = fs1_name
        self.fs2_name = fs2_name

    def _draw(self):

        self._sort_dataset(
            key=lambda group_info: group_info.fs1_file_count, reverse=True)

        max_y = float(self.dataset[0].fs1_file_count)

        num_groups = len(self.dataset)

        group_names = list()
        fs1_file_count_values = list()
        fs2_file_count_values = list()

        for group_info_item in self.dataset:

            group_names.append(group_info_item.name)
            fs1_file_count_values.append(group_info_item.fs1_file_count)
            fs2_file_count_values.append(group_info_item.fs2_file_count)

        ind = np.arange(num_groups)  # The x locations for the groups

        bar_width = 0.35  # the width of the bars: can also be len(x) sequence

        p1 = self._ax.bar(ind, fs1_file_count_values, bar_width, color='blue')

        p2 = self._ax.bar(ind + bar_width, fs2_file_count_values,
                          bar_width, color='orange')

        self._ax.set_xticks(ind + bar_width / 2)
        self._ax.set_xticklabels(group_names, rotation=45)

        tick_width_y = max_y / 10

        # requires floating arguments...
        self._ax.set_yticks(np.arange(0, max_y, tick_width_y))

        self._ax.legend((p1[0], p2[0]), (self.fs1_name, self.fs2_name))

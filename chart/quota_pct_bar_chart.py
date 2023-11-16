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

import matplotlib
# Force matplotlib to not use any X window backend.
matplotlib.use('Agg')


class QuotaPctBarChart(BaseChart):

    def __init__(self, title, dataset, file_path):

        super(QuotaPctBarChart, self).__init__(title, dataset, file_path,
                                               x_label='Group',
                                               y_label='Quota Usage (%)')

    def _draw(self):

        num_groups = len(self.dataset)

        self._sort_dataset(lambda group_info: group_info.name)

        group_names = list()
        quota_used_pct_list = list()

        for group_info in self.dataset:

            group_names.append(group_info.name)

            if group_info.quota and group_info.size:
                quota_used_pct = \
                    round((group_info.size / group_info.quota) * 100)

            else:
                quota_used_pct = 0

            quota_used_pct_list.append(quota_used_pct)

        ind = np.arange(num_groups)  # the x locations for the groups

        bar_width = 0.35  # the width of the bars: can also be len(x) sequence

        self._figure.subplots_adjust(top=0.80)

        self._ax.bar(ind, quota_used_pct_list, bar_width, color='blue')

        self._ax.set_xticks(ind)
        self._ax.set_xticklabels(group_names, rotation=45)

        self._ax.set_yticks(np.arange(0, 101, 10))

        x = np.linspace(0, num_groups)
        y = np.linspace(100, 100)

        self._ax.plot(x, y,
                 linewidth=0.8, linestyle='dashed',
                 label='Quota Limit', color='red')

        self._ax.legend()

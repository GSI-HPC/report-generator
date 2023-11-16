#!/usr/bin/env python3
#
# -*- coding: utf-8 -*-
#
# © Copyright 2023 GSI Helmholtzzentrum für Schwerionenforschung
#
# This software is distributed under
# the terms of the GNU General Public Licence version 3 (GPL Version 3),
# copied verbatim in the file "LICENCE".

import pandas as pd

import matplotlib
# Force matplotlib to not use any X window backend.
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from chart.base_chart import BaseChart

class TrendChart(BaseChart):

    def __init__(self, title, dataset, file_path, x_label, y_label):

        if type(dataset) != pd.DataFrame:
            raise RuntimeError('As dataset a Pandas Data Frame is required!')

        if not len(dataset):
            raise RuntimeError('Retrieved an empty Pandas Data Frame!')

        super(TrendChart, self).__init__(title, dataset, file_path, x_label, y_label)

        self.start_date = self.dataset.index.min().strftime('%Y-%m-%d')
        self.end_date = self.dataset.index.max().strftime('%Y-%m-%d')

        # No bright colors.
        self.color_name = 'Dark2'

    def _add_sorted_legend(self, df_tail):
        """
        Adds a sorted legend to the figure sorted by the last values retrieved
        from the given Pandas Data Frame last values.
        :param df_tail: Tail from Pandas Data Frame.
        """

        df_tail_labels = df_tail.columns.values
        df_tail_values = df_tail.values.tolist()[0]
        df_pairs = zip(df_tail_labels, df_tail_values)

        import operator
        sorted_df_pairs = \
            sorted(df_pairs, key=operator.itemgetter(1), reverse=True)

        sorted_labels = [ item[0] for item in sorted_df_pairs ]

        ax_handles, ax_labels = self._ax.get_legend_handles_labels()

        ax_pairs = list(zip(ax_handles, ax_labels))
        ax_pairs.sort(key=lambda ax_pairs: sorted_labels.index(ax_pairs[1]))

        handles, labels = zip(*ax_pairs)

        self._figure.legend(handles=handles, labels=labels, title="Groups",
                            fontsize='small', loc='upper left', handlelength=5)

    def _draw(self):

        line_style_def = ['-', '--', '-.', ':']
        len_lsd = len(line_style_def)
        line_styles = list()

        for i in range(len(self.dataset.keys())):
            line_styles.append(line_style_def[i % len_lsd])

        self._ax.yaxis.set_major_locator(plt.MaxNLocator(12))

        color_map = \
            BaseChart._create_colors(self.color_name, len(self.dataset.keys()))

        self.dataset.plot(ax=self._ax, legend=False, style=line_styles, color=color_map, grid=True)

        sub_title = "Date from %s to %s" % (self.start_date, self.end_date)

        self._ax.set_title(sub_title, fontsize=12)

        self._add_sorted_legend(self.dataset.tail(1))

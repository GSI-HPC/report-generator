#!/usr/bin/env python3
#
# -*- coding: utf-8 -*-
#
# © Copyright 2023 GSI Helmholtzzentrum für Schwerionenforschung
#
# This software is distributed under
# the terms of the GNU General Public Licence version 3 (GPL Version 3),
# copied verbatim in the file "LICENCE".

import abc
import sys
import datetime

import matplotlib
# Force matplotlib to not use any X window backend.
matplotlib.use('Agg')
import matplotlib.pyplot as plt


class BaseChart(object):

    def __init__(self, title, dataset, file_path, x_label='', y_label='', width=20, height=10):

        __metaclass__ = abc.ABCMeta

        super(BaseChart, self).__init__()

        self.title = title
        self.dataset = dataset
        self.file_path = file_path

        self.width = width
        self.height = height

        self.x_label = x_label
        self.y_label = y_label

        self._file_type = 'svg'

        self._figure = None
        self._ax = None

    def create(self):

        self._figure, self._ax = plt.subplots(figsize=(self.width, self.height))

        self._draw()

        self._set_figure_and_axis_attr()
        self._add_creation_text()

        self._save()
        self._close()

    # TODO: Extract that method to proper item class maybe it returns a copy then...
    def _sort_dataset(self, key, reverse=False):

        if isinstance(self.dataset, list):
            self.dataset.sort(key=key, reverse=reverse)
        else:
            raise RuntimeError("Operation not supported for not list type!")

    def _add_creation_text(self):

        self._figure.text(
            0, 0, datetime.datetime.now().strftime('%Y-%m-%d - %X'),
            verticalalignment='bottom', horizontalalignment='left',
                fontsize=8, transform=self._figure.transFigure)

    def _set_figure_and_axis_attr(self):

        self._figure.suptitle(self.title, fontsize=18, fontweight='bold')

        self._ax.set_xlabel(self.x_label)
        self._ax.set_ylabel(self.y_label)

    @staticmethod
    def _create_colors(name, n):

        color_map = matplotlib.cm.get_cmap(name, n)

        return [matplotlib.colors.rgb2hex(color_map(i)[:3]) for i in range(n)]

    @abc.abstractmethod
    def _draw(self):
        raise NotImplementedError(
            "Not implemented method: %s.%s" %
            (self.__class__, sys._getframe().f_code.co_name))

    def _save(self):
        plt.savefig(self.file_path, type=self._file_type)

    def _close(self):
        plt.close(self._figure)

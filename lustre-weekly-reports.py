#!/usr/bin/env python3
#
# -*- coding: utf-8 -*-
#
# © Copyright 2023 GSI Helmholtzzentrum für Schwerionenforschung
#
# This software is distributed under
# the terms of the GNU General Public Licence version 3 (GPL Version 3),
# copied verbatim in the file "LICENCE".

from decimal import Decimal

import configparser
import datetime
import argparse
import logging
import os

from chart.quota_pct_bar_chart import QuotaPctBarChart
from chart.usage_quota_bar_chart import UsageQuotaBarChart
from chart.usage_pie_chart import UsagePieChart
from utils.matplotlib_ import check_matplotlib_version
from utils.rsync_ import transfer_report

import dataset.lfs_dataset_handler as ldh
import dataset.item_handler as ih
import filter.group_filter_handler as gf

def create_weekly_reports(local_mode,
                          chart_dir,
                          file_system,
                          fs_long_name,
                          quota_pct_bar_chart,
                          usage_quota_bar_chart,
                          usage_pie_chart,
                          num_top_groups,
                          storage_multiplier,
                          input_file=None):

    reports_path_list = list()

    group_info_list = None
    storage_total_size = 0

    if local_mode:

        group_info_list = ih.create_dummy_group_info_list()

        if input_file:
            storage_total_size = ldh.lustre_total_size(file_system, input_file) * Decimal(storage_multiplier)
        else:
            storage_total_size = 18458963071860736 * Decimal(storage_multiplier)

    else:

        group_info_list = gf.filter_group_info_items(ldh.create_group_info_list(file_system))

        storage_total_size = ldh.lustre_total_size(file_system) * Decimal(storage_multiplier)

    # QUOTA-PCT-BAR-CHART
    title = "Group Quota Usage on %s" % fs_long_name
    chart_path = chart_dir + os.path.sep + quota_pct_bar_chart
    chart = QuotaPctBarChart(title, group_info_list, chart_path)
    chart.create()

    logging.debug("Created chart: %s" % chart_path)
    reports_path_list.append(chart_path)

    # USAGE-QUOTA-BAR-CHART
    title = "Quota and Disk Space Usage on %s" % fs_long_name
    chart_path = chart_dir + os.path.sep + usage_quota_bar_chart
    chart = UsageQuotaBarChart(title, group_info_list, chart_path)
    chart.create()

    logging.debug("Created chart: %s" % chart_path)
    reports_path_list.append(chart_path)

    # USAGE-PIE-CHART
    title = "Storage Usage on %s" % fs_long_name
    chart_path = chart_dir + os.path.sep + usage_pie_chart
    chart = UsagePieChart(title,
                          group_info_list,
                          chart_path,
                          storage_total_size,
                          num_top_groups)
    chart.create()

    logging.debug("Created chart: %s" % chart_path)
    reports_path_list.append(chart_path)

    return reports_path_list

def main():

    parser = argparse.ArgumentParser(description='Storage Report Generator.')

    parser.add_argument('-f', '--config-file', dest='config_file',
        type=str, required=True, help='Path of the config file.')

    parser.add_argument('-D', '--enable-debug', dest='enable_debug',
        required=False, action='store_true',
        help='Enables logging of debug messages.')

    parser.add_argument('-L', '--enable-local_mode', dest='enable_local_mode',
        required=False, action='store_true',
        help='Enables local_mode program execution.')

    parser.add_argument('-i', '--input-file', dest='input_file',
        type=str, required=False, help='Path of the input file.')

    args = parser.parse_args()

    if not args.enable_local_mode and args.input_file:
        raise RuntimeError("Local mode must be enabled to provide an input file.")

    if args.enable_local_mode and args.input_file:
        if not os.path.isfile(args.input_file):
            raise IOError("The input file does not exist or is not a file: %s" % args.input_file)

    if not os.path.isfile(args.config_file):
        raise IOError("The config file does not exist or is not a file: %s" % args.config_file)

    logging_level = logging.INFO

    if args.enable_debug:
        logging_level = logging.DEBUG

    logging.basicConfig(
        level=logging_level, format='%(asctime)s - %(levelname)s: %(message)s')

    try:

        logging.info('START')

        date_now = datetime.datetime.now()

        check_matplotlib_version()

        logging.debug("Local mode enabled: %s" % args.enable_local_mode)

        config = configparser.ConfigParser()
        config.read(args.config_file)

        transfer_mode = config.get('transfer', 'mode')

        chart_dir = config.get('base_chart', 'report_dir')

        file_system = config.get('storage', 'file_system')
        fs_long_name = config.get('storage', 'fs_long_name')

        quota_pct_bar_chart = config.get('quota_pct_bar_chart', 'filename')
        usage_quota_bar_chart = config.get('usage_quota_bar_chart', 'filename')
        usage_pie_chart = config.get('usage_pie_chart', 'filename')

        num_top_groups = config.getint('usage_pie_chart', 'num_top_groups')
        mul = config.getfloat('usage_pie_chart', 'storage_multiplier')

        chart_path_list = \
            create_weekly_reports(args.enable_local_mode,
                                  chart_dir,
                                  file_system,
                                  fs_long_name,
                                  quota_pct_bar_chart,
                                  usage_quota_bar_chart,
                                  usage_pie_chart,
                                  num_top_groups,
                                  mul,
                                  args.input_file)

        if transfer_mode == 'on':

            for chart_path in chart_path_list:
                transfer_report('weekly', date_now, chart_path, config)

        logging.info('END')

        return 0

    except Exception:
        logging.exception('Caught exception in main')

if __name__ == '__main__':
   main()

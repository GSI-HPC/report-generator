#!/usr/bin/env python3
#
# -*- coding: utf-8 -*-
#
# © Copyright 2023 GSI Helmholtzzentrum für Schwerionenforschung
#
# This software is distributed under
# the terms of the GNU General Public Licence version 3 (GPL Version 3),
# copied verbatim in the file "LICENCE".

import configparser
import logging
import argparse
import time
import sys
import os

import database.disk_space_usage_collect as dsuc
import dataset.lfs_dataset_handler as ldh

def main():

    RUN_MODE = 'collect'

    parser = argparse.ArgumentParser(description='')

    parser.add_argument('--create-table', dest='create_table',
        required=False, action='store_true',
        help='Creates the group quota history table.')

    parser.add_argument('-f', '--config-file', dest='config_file', type=str,
        required=True, help='Path of the config file.')

    parser.add_argument('-i', '--input-file', dest='input_file',
        type=str, required=False, help='Path of the input file.')

    parser.add_argument('-m', '--run-mode', dest='run_mode', type=str,
        default=RUN_MODE, required=False,
        help="Specifies the run mode: 'print' or 'collect' - Default: %s" %
            RUN_MODE)

    parser.add_argument('-D', '--enable-debug', dest='enable_debug',
        required=False, action='store_true',
        help='Enables logging of debug messages.')

    args = parser.parse_args()

    if not os.path.isfile(args.config_file):
        raise IOError("The config file does not exist or is not a file: %s"
            % args.config_file)

    logging_level = logging.INFO

    if args.enable_debug:
        logging_level = logging.DEBUG

    logging.basicConfig(level=logging_level,
                        format='%(asctime)s - %(levelname)s: %(message)s')

    if not (args.run_mode == 'print' or args.run_mode == 'collect'):
        raise RuntimeError("Invalid run mode: %s" % args.run_mode)

    if not args.create_table and not os.path.isfile(args.input_file):
        raise IOError("The input file does not exist or is not a file: %s" % args.input_file)

    input_data = None

    try:
        logging.info('START')

        date_today = time.strftime('%Y-%m-%d')

        config = configparser.ConfigParser()
        config.read(args.config_file)

        if args.create_table:

            dsuc.create_disk_space_usage_table(config)
            logging.info('END')
            sys.exit(0)

        fs = config.get('lustre', 'file_system')

        storage_info_list = None

        if args.input_file:
            storage_info_list = ldh.create_storage_info(fs, args.input_file).values()
        else:
            storage_info_list = ldh.create_storage_info(fs).values()

        if args.run_mode == 'print':

            for item in storage_info_list:

                logging.info("Date: %s - Mounted on: %s - Total: %s - Free: %s - Used: %s - Usage Percentage: %s" \
                    % (date_today,
                      item.mount_point,
                      item.ost.total,
                      item.ost.free,
                      item.ost.used,
                      item.ost.used_percentage()))

        if args.run_mode == 'collect':
            dsuc.store_disk_space_usage(config, date_today, storage_info_list)

        logging.info('END')
        sys.exit(0)

    except Exception:
        logging.exception('Caught exception in main')
        sys.exit(1)

if __name__ == '__main__':
    main()

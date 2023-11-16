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

import database.group_quota_collect as gqc
import dataset.lfs_dataset_handler as ldh

def main():

    # Default run-mode: collect
    RUN_MODE = 'collect'

    parser = argparse.ArgumentParser(description='')

    parser.add_argument('-f', '--config-file', dest='config_file', type=str,
        required=True, help='Path of the config file.')

    parser.add_argument('-i', '--input-file', dest='input_file', type=str,
        required=False, help='Path of the input file.')

    parser.add_argument('-m', '--run-mode', dest='run_mode', type=str,
        default=RUN_MODE, required=False,
        help="Specifies the run mode: 'print' or 'collect' - Default: %s" %
            RUN_MODE)

    parser.add_argument('-D', '--enable-debug', dest='enable_debug',
        required=False, action='store_true',
        help='Enables logging of debug messages.')

    parser.add_argument('--create-table', dest='create_table',
        required=False, action='store_true',
        help='Creates the group quota history table.')

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

    try:
        logging.info('START')

        date_today = time.strftime('%Y-%m-%d')

        config = configparser.ConfigParser()
        config.read(args.config_file)

        if args.create_table:

            gqc.create_group_quota_history_table(config)
            logging.info('END')
            sys.exit(0)

        fs = config.get('lustre', 'file_system')

        group_info_list = None

        if args.input_file:
            group_info_list = ldh.create_group_info_list(fs, args.input_file)
        else:
            group_info_list = ldh.create_group_info_list(fs)

        if args.run_mode == 'print':

            for group_info in group_info_list:

                logging.info("Group: %s - Used: %s - Quota: %s - Files: %s" \
                    % (group_info.name,
                       group_info.size,
                       group_info.quota,
                       group_info.files))

        if args.run_mode == 'collect':
            gqc.store_group_quota(config, date_today, group_info_list)

        logging.info('END')
        sys.exit(0)

    except Exception:
        logging.exception('Caught exception in main')
        sys.exit(1)

if __name__ == '__main__':
    main()

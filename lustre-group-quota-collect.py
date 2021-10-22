#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2018 Gabriele Iannetti <g.iannetti@gsi.de>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#


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

    except Exception as e:

        exc_type, exc_obj, exc_tb = sys.exc_info()
        filename = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]

        error_msg = "Caught exception (%s): %s - %s (line: %s)" % \
                    (exc_type, str(e), filename, exc_tb.tb_lineno)

        logging.error(error_msg)
        sys.exit(1)

if __name__ == '__main__':
    main()

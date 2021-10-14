#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2021 Leandro Ramos Rocha <l.ramosrocha@gsi.de>
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

import database.create_disk_space_usage_table as dsuc

import dataset.lfs_dataset_handler as ldh

from utils.getent_group import get_user_groups


def main():

    # Default run-mode: collect
    run_mode = 'collect'

    parser = argparse.ArgumentParser(description='')

    parser.add_argument('--create-table', dest='create_table',
        required=False, action='store_true',
        help='Creates the group quota history table.')

    parser.add_argument('-f', '--config-file', dest='config_file', type=str,
        required=True, help='Path of the config file.')

    parser.add_argument('-i', '--input-file', dest='input_file',
        type=str, required=False, help='Path of the input file.')

    parser.add_argument('-m', '--run-mode', dest='run_mode', type=str,
        default=run_mode, required=False,
        help="Specifies the run mode: 'print' or 'collect' - Default: %s" %
            run_mode)

    parser.add_argument('-D', '--enable-debug', dest='enable_debug',
        required=False, action='store_true',
        help='Enables logging of debug messages.')

    args = parser.parse_args()

    if not os.path.isfile(args.config_file):
        raise IOError("The config file does not exist or is not a file: %s" 
            % args.config_file)
    
    logging_level = logging.ERROR

    if args.enable_debug:
        logging_level = logging.DEBUG

    logging.basicConfig(level=logging_level,
                        format='%(asctime)s - %(levelname)s: %(message)s')

    if not (args.run_mode == 'print' or args.run_mode == 'collect'):
        raise RuntimeError("Invalid run mode: %s" % args.run_mode)
    else:
        run_mode = args.run_mode

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

        #TODO: call create_lfs_df_input_data

        storage_info_list = ldh.create_storage_info()  #TODO: give result of the above

        if run_mode == 'print':

            for group_info in storage_info_list:

                print("Group: %s - Used: %s - Quota: %s - Files: %s" \
                    % (group_info.name,
                       group_info.size, 
                       group_info.quota, 
                       group_info.files))

        if run_mode == 'collect':
            dsuc.store_disk_space_usage(config, date_today, storage_info_list)

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

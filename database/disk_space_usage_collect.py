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


import enum
import logging
import MySQLdb

from contextlib import closing

def create_disk_space_usage_table(config):
    db = config.get('history', 'database')
    table = config.get('history', 'table')

    with closing(MySQLdb.connect(host=config.get('mysqld', 'host'),
                                 user=config.get('mysqld', 'user'),
                                 passwd=config.get('mysqld', 'password'),
                                 db=db)) as conn:

        with closing(conn.cursor()) as cur:

            conn.autocommit(True)

            sql = "USE " + db

            logging.debug(sql)
            cur.execute(sql)

            sql = """
CREATE TABLE """ + table + """ (
   date date NOT NULL,
   mounted_on varchar(255) NOT NULL DEFAULT 'unknown',
   total bigint(20) unsigned DEFAULT NULL,
   free bigint(20) unsigned DEFAULT '0',
   used bigint(20) unsigned DEFAULT '0',
   used_percentage decimal(5,2) unsigned DEFAULT '0.00',
   PRIMARY KEY (date,mounted_on)
) ENGINE=MyISAM DEFAULT CHARSET=latin1
"""
            logging.debug(sql)
            cur.execute(sql)

def store_disk_space_usage(config, date_today, storage_info_list):

    table = config.get('history', 'table')

    with closing(MySQLdb.connect(host=config.get('mysqld', 'host'),
                                 user=config.get('mysqld', 'user'),
                                 passwd=config.get('mysqld', 'password'),
                                 db=config.get('history', 'database'))) \
                                    as conn:

        with closing(conn.cursor()) as cur:

            sql = "INSERT INTO %s (date, mounted_on, total, free, used, used_percentage) VALUES" \
                % table

            for index, item in enumerate(storage_info_list, start=1):

                sql_end = ","

                if index == len(storage_info_list):
                    sql_end = ";"

                sql += " ('%s', '%s', %s, %s, %s, %s)%s" \
                    % (date_today, item.mount_point, item.ost.total,
                    item.ost.free, item.ost.used, item.ost.used_percentage(), sql_end)

            logging.debug(sql)
            cur.execute(sql)

            if not cur.rowcount:
                raise RuntimeError("Snapshot failed for date: %s." % date_today)

            logging.debug("Inserted rows: %d into table: %s for date: %s" \
                % (cur.rowcount, table, date_today))

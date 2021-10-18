#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2021 Gabriele Iannetti <g.iannetti@gsi.de>
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


import logging
import MySQLdb

from contextlib import closing

def create_group_quota_history_table(config):

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
   gid varchar(127) NOT NULL DEFAULT 'unknown',
   used bigint(20) unsigned DEFAULT NULL,
   quota bigint(20) unsigned DEFAULT '0',
   files bigint(20) unsigned DEFAULT '0',
   PRIMARY KEY (gid,date)
) ENGINE=MyISAM DEFAULT CHARSET=latin1
"""
            logging.debug(sql)
            cur.execute(sql)

def store_group_quota(config, date, group_info_list):

    table = config.get('history', 'table')

    with closing(MySQLdb.connect(host=config.get('mysqld', 'host'),
                                 user=config.get('mysqld', 'user'),
                                 passwd=config.get('mysqld', 'password'),
                                 db=config.get('history', 'database'))) \
                                    as conn:

        with closing(conn.cursor()) as cur:

            sql = "INSERT INTO %s (date, gid, used, quota, files) VALUES" \
                % table
            
            iter_list = iter(group_info_list)

            item = next(iter_list)

            sql += "('%s', '%s', %s, %s, %s)" \
                % (date, item.name, item.size, item.quota, item.files)

            for item in iter_list:
                sql += ", ('%s', '%s', %s, %s, %s)" \
                    % (date, item.name, item.size, item.quota, item.files)

            logging.debug(sql)
            cur.execute(sql)

            if not cur.rowcount:
                raise RuntimeError("Snapshot failed for date: %s." % date)

            logging.debug("Inserted rows: %d into table: %s for date: %s" \
                % (cur.rowcount, table, date))
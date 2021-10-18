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

import unittest
import configparser
import MySQLdb

from database.group_quota_collect import create_group_quota_history_table

class TestDatabaseMethods(unittest.TestCase):

    def test_create_group_quota_history_table(self):
        config = configparser.ConfigParser()
        config.read('Configuration/lustre-group-quota-collect.conf.example')
        with self.assertRaises(MySQLdb.OperationalError) as cm:
            create_group_quota_history_table(config)

if __name__ == '__main__':
    unittest.main()

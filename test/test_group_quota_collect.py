#!/usr/bin/env python3

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

#!/usr/bin/env python3
#
# -*- coding: utf-8 -*-
#
# © Copyright 2023 GSI Helmholtzzentrum für Schwerionenforschung
#
# This software is distributed under
# the terms of the GNU General Public Licence version 3 (GPL Version 3),
# copied verbatim in the file "LICENCE".

import logging
import pandas as pd

THRESHOLD_DAYS = 28

def create_data_frame_weekly(item_dict):

    data_frame = pd.DataFrame()

    for group_name in item_dict:

        if len(item_dict[group_name][0]) >= THRESHOLD_DAYS:

            dates = pd.DatetimeIndex(
                item_dict[group_name][0], dtype='datetime64[ns]')

            date_delta = dates.date[-1] - dates.date[0]

            if date_delta.days >= THRESHOLD_DAYS:

                data_frame[group_name] = \
                    pd.Series(item_dict[group_name][1], index=dates)

                logging.debug("Added group to data frame with data points: " \
                    "'%s' - '%s'" % (group_name, date_delta))

            else:

                logging.warning(
                    "Ignoring group with to small date delta: '%s'"
                        % group_name)

        else:

            logging.warning(
                "Ignoring group with insufficient data points: '%s'"
                    % group_name)

            continue

    if len(data_frame):

        start_date = data_frame.index.min().strftime('%Y-%m-%d')
        end_date = data_frame.index.max().strftime('%Y-%m-%d')

        mean_weekly_summary = data_frame.resample('W').mean()

        return mean_weekly_summary.truncate(before=start_date, after=end_date)

    else:
        return pd.DataFrame()

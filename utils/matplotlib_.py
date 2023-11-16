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
import matplotlib

def check_matplotlib_version():

    mplot_ver = matplotlib.__version__

    logging.debug("Running with matplotlib version: %s" % mplot_ver)

    major_version = int(mplot_ver.split('.')[0])

    # Exclude Version 1 of Matplotlib, since it is not supported!
    if major_version == 1:
        raise RuntimeError("Matplotlib Version 1 is not supported!")

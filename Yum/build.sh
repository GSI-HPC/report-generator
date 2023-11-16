#!/bin/bash
#
# -*- coding: utf-8 -*-
#
# © Copyright 2023 GSI Helmholtzzentrum für Schwerionenforschung
#
# This software is distributed under
# the terms of the GNU General Public Licence version 3 (GPL Version 3),
# copied verbatim in the file "LICENCE".

DIST_PATH=${PWD}/../Pyinstaller/pybuild/dist/

rpmbuild -bb \
    --define "__distdir ${DIST_PATH}"\
    --define "_topdir ${PWD}/rpmbuild"\
    rpmbuild/SPECS/lustre-reports.spec

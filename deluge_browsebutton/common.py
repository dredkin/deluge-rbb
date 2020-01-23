# -*- coding: utf-8 -*-
# Copyright (C) 2020 Your Name <yourname@example.com>
#
# Basic plugin template created by the Deluge Team.
#
# This file is part of MyPlugin and is licensed under GNU GPL 3.0, or later,
# with the additional special exception to link portions of this program with
# the OpenSSL library. See LICENSE for more details.
from __future__ import unicode_literals

import os.path

from pkg_resources import resource_filename

import sys
PY3 =  sys.version_info[0] >= 3

def get_resource(filename):
    if PY3:
        ext = '.ui'
    else:
        ext = '.glade'
    return resource_filename(__package__, os.path.join('data', filename + ext))

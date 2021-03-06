# Copyright 2016 The Fabulous Authors. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
    fabulous.logs
    ~~~~~~~~~~~~~

    Utilities for transient logging.

    This is very useful tool for monitoring what your Python scripts are doing.
    It allows you to have full verbosity without drowning out important error
    messages:

    .. code-block:: python

        import time, logging
        from fabulous import logs
        logs.basicConfig(level='WARNING')

        for n in range(20):
            logging.debug("verbose stuff you don't care about")
            time.sleep(0.1)
        logging.warning("something bad happened!")
        for n in range(20):
            logging.debug("verbose stuff you don't care about")
            time.sleep(0.1)

"""

import sys
import logging

from fabulous import utils


class TransientStreamHandler(logging.StreamHandler):
    """Standard Python logging Handler for Transient Console Logging

    Logging transiently means that verbose logging messages like DEBUG
    will only appear on the last line of your terminal for a short
    period of time and important messages like WARNING will scroll
    like normal text.

    This allows you to log lots of messages without the important
    stuff getting drowned out.

    This module integrates with the standard Python logging module.
    """

    def __init__(self, strm=sys.stderr, level=logging.WARNING):
        logging.StreamHandler.__init__(self, strm)
        if isinstance(level, int):
            self.levelno = level
        else:
            self.levelno = logging._levelNames[level]
        self.need_cr = False
        self.last = ""
        self.parent = logging.StreamHandler

    def close(self):
        if self.need_cr:
            self.stream.write("\n")
            self.need_cr = False
        self.parent.close(self)

    def write(self, data):
        if self.need_cr:
            width = max(min(utils.term.width, len(self.last)), len(data))
            fmt = "\r%-" + str(width) + "s\n" + self.last
        else:
            fmt = "%s\n"
        try:
            self.stream.write(fmt % (data))
        except UnicodeError:
            self.stream.write(fmt % (data.encode("UTF-8")))

    def transient_write(self, data):
        if self.need_cr:
            self.stream.write('\r')
        else:
            self.need_cr = True
        width = utils.term.width
        for line in data.rstrip().split('\n'):
            if line:
                if len(line) > width:
                    line = line[:width - 3] + '...'
                line_width = max(min(width, len(self.last)), len(line))
                fmt = "%-" + str(line_width) + "s"
                self.last = line
                try:
                    self.stream.write(fmt % (line))
                except UnicodeError:
                    self.stream.write(fmt % (line.encode("UTF-8")))
            else:
                self.stream.write('\r')
                self.stream.flush()

    def emit(self, record):
        try:
            msg = self.format(record)
            if record.levelno >= self.levelno:
                self.write(msg)
            else:
                self.transient_write(msg)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)


def basicConfig(level=logging.WARNING, transient_level=logging.NOTSET):
    """Shortcut for setting up transient logging

    I am a replica of ``logging.basicConfig`` which installs a
    transient logging handler to stderr.
    """
    fmt = "%(asctime)s [%(levelname)s] [%(name)s:%(lineno)d] %(message)s"
    logging.root.setLevel(transient_level)  # <--- IMPORTANT
    hand = TransientStreamHandler(level=level)
    hand.setFormatter(logging.Formatter(fmt))
    logging.root.addHandler(hand)

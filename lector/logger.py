# This file is a part of Lector, a Qt based ebook reader
# Copyright (C) 2017-2019 BasioMeusPuga

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import logging

from PyQt5 import QtCore


def init_logging(cli_arguments):
    # This needs a separate 'Lector' in the os.path.join because
    # application name isn't explicitly set in this module
    location_prefix = os.path.join(
        QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.AppDataLocation),
        'Lector')
    os.makedirs(location_prefix, exist_ok=True)
    logger_filename = os.path.join(location_prefix, 'Lector.log')

    log_level = 30  # Warning and above
    # Set log level according to command line arguments
    try:
        if cli_arguments[1] == 'debug':
            log_level = 10  # Debug and above
            print('Debug logging enabled')
            try:
                os.remove(logger_filename)  # Remove old log for clarity
            except FileNotFoundError:
                pass
    except IndexError:
        pass

    # Create logging object
    logging.basicConfig(
        filename=logger_filename,
        filemode='a',
        format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
        datefmt='%Y/%m/%d  %H:%M:%S',
        level=log_level)
    logging.addLevelName(60, 'HAMMERTIME')  ## Messages that MUST be logged

    return logging.getLogger('lector.main')

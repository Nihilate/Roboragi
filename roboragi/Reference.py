# -*- coding: utf-8 -*-

# Copyright (C) 2018  Nihilate
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import sqlite3

sqlConn = sqlite3.connect('reference.db')
sqlCur = sqlConn.cursor()


def is_april_fools_2016(username):
    try:
        query = "SELECT 1 FROM aprilfools2016 WHERE username = ? LIMIT 1"
        sqlCur.execute(query, [username])
        result = sqlCur.fetchone()

        if result:
            return True
        else:
            return False
    except Exception:
        return False


def get_bling(username):
    if is_april_fools_2016(username):
        return '&#32;|&#32;\U0001F4B0'
    else:
        return ''

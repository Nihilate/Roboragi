# -*- coding: utf-8 -*-

import sqlite3

sqlConn = sqlite3.connect('reference.db')
sqlCur = sqlConn.cursor()

def is_april_fools_2016(username):
    try:
        sqlCur.execute("SELECT 1 FROM aprilfools2016 WHERE username = ? LIMIT 1", [username])
        result = sqlCur.fetchone()

        if result:
            return True
        else:
            return False
    except Exception as e:
        return False

def get_bling(username):
    if is_april_fools_2016(username):
        return ' ^(| \U0001F4B0)'
    else:
        return ''

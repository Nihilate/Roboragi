'''
DatabaseHandler.py
Handles all connections to the database. The database runs on PostgreSQL and is
connected to via psycopg2.
'''

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

import traceback
from math import sqrt

import psycopg2

DBNAME = ''
DBUSER = ''
DBPASSWORD = ''
DBHOST = ''

try:
    import Config

    DBNAME = Config.dbname
    DBUSER = Config.dbuser
    DBPASSWORD = Config.dbpassword
    DBHOST = Config.dbhost
except ImportError:
    pass

conn = psycopg2.connect(
    user=DBUSER,
    password=DBPASSWORD,
    host=DBHOST,
    dbname=DBNAME
)
cur = conn.cursor()


def setup():
    """
    Sets up the database and creates the databases if they haven't already been
    made.
    """
    try:
        conn = psycopg2.connect(
            user=DBUSER,
            password=DBPASSWORD,
            host=DBHOST,
            dbname=DBNAME
        )
    except Exception:
        print("Unable to connect to the database")

    cur = conn.cursor()

    # Create requests table
    create_requests_table = """
    CREATE TABLE requests (
        id SERIAL PRIMARY KEY,
        name VARCHAR(320),
        type VARCHAR(16),
        requester VARCHAR(50),
        subreddit VARCHAR(50),
        requesttimestamp TIMESTAMP DEFAULT current_timestamp
    );
    """

    try:
        cur.execute(create_requests_table)
        conn.commit()
    except Exception:
        # traceback.print_exc()
        cur.execute('ROLLBACK')
        conn.commit()

    create_comments_table = """
    CREATE TABLE comments (
        commentid varchar(16) PRIMARY KEY,
        requester varchar(50),
        subreddit varchar(50),
        hadRequest boolean
    );
    """

    # Create comments table
    try:
        cur.execute(create_comments_table)
        conn.commit()
    except Exception:
        # traceback.print_exc()
        cur.execute('ROLLBACK')
        conn.commit()


setup()


# --------------------------------------#

def _percentage(dividend, divisor):
    """ Return a percentage """
    return (float(dividend) / divisor) * 100


def addComment(commentid, requester, subreddit, hadRequest):
    """
    Adds a comment to the "already seen" database. Also handles submissions,
    which have a similar ID structure.
    """

    query = """
    INSERT INTO comments (commentid, requester, subreddit, hadRequest)
    VALUES (%s, %s, %s, %s);
    """
    values = (commentid, requester, subreddit, hadRequest)

    try:
        subreddit = str(subreddit).lower()

        cur.execute(query, values)
        conn.commit()
    except Exception:
        traceback.print_exc()
        cur.execute('ROLLBACK')
        conn.commit()


def commentExists(commentid):
    """
    Returns true if the comment/submission has already been checked.
    """

    query = "SELECT * FROM comments WHERE commentid = %s;"
    values = (commentid,)

    try:
        cur.execute(query, values)
        if (cur.fetchone()) is None:
            conn.commit()
            return False
        else:
            conn.commit()
            return True
    except Exception:
        traceback.print_exc()
        cur.execute('ROLLBACK')
        conn.commit()
        return True


def addRequest(name, rType, requester, subreddit):
    """
    Adds a request to the request-tracking database. rType is either "Anime"
    or "Manga".
    """
    query = """
    INSERT INTO requests (name, type, requester, subreddit)
    VALUES (%s, %s, %s, %s);
    """
    values = (name, rType, requester, subreddit)

    try:
        subreddit = str(subreddit).lower()

        if ('nihilate' not in subreddit):
            cur.execute(query, values)
            conn.commit()
    except Exception:
        # traceback.print_exc()
        cur.execute('ROLLBACK')
        conn.commit()


def getBasicStats(top_media_number=5, top_username_number=5):
    """
    Returns an object which contains data about the overall database stats
    (i.e. ALL subreddits).
    """
    try:
        basicStatDict = {}

        cur.execute("SELECT COUNT(1) FROM comments")
        totalComments = int(cur.fetchone()[0])
        basicStatDict['totalComments'] = totalComments

        cur.execute("SELECT COUNT(1) FROM requests;")
        total = int(cur.fetchone()[0])
        basicStatDict['total'] = total

        cur.execute(
            """
            SELECT COUNT(1)
              FROM (SELECT DISTINCT name
                      FROM requests) AS temp;
            """
        )
        dNames = int(cur.fetchone()[0])
        basicStatDict['uniqueNames'] = dNames

        cur.execute(
            """
            SELECT COUNT(1)
              FROM (SELECT DISTINCT subreddit
                      FROM requests) as temp;
            """
        )
        dSubreddits = int(cur.fetchone()[0])
        basicStatDict['uniqueSubreddits'] = dSubreddits

        meanValue = float(total) / dNames
        basicStatDict['meanValuePerRequest'] = meanValue

        variance = 0
        cur.execute("SELECT name, count(name) FROM requests GROUP by name")
        for entry in cur.fetchall():
            variance += (entry[1] - meanValue) * (entry[1] - meanValue)

        variance = variance / dNames
        stdDev = sqrt(variance)
        basicStatDict['standardDeviation'] = stdDev

        select_top_requests = """
        SELECT name, type, COUNT(name)
          FROM requests
         GROUP BY name, type
         ORDER BY COUNT(name) DESC, name ASC LIMIT %s;
        """
        top_request_values = (top_media_number,)

        cur.execute(select_top_requests, top_request_values)
        topRequests = cur.fetchall()
        basicStatDict['topRequests'] = []
        for request in topRequests:
            basicStatDict['topRequests'].append(request)

        select_top_requesters = """
        SELECT requester, COUNT(requester)
          FROM requests
         GROUP BY requester
         ORDER BY COUNT(requester) DESC, requester ASC LIMIT %s;
        """
        top_requester_values = (top_username_number,)

        cur.execute(select_top_requesters, top_requester_values)
        topRequesters = cur.fetchall()
        basicStatDict['topRequesters'] = []
        for requester in topRequesters:
            basicStatDict['topRequesters'].append(requester)

        conn.commit()
        return basicStatDict

    except Exception:
        traceback.print_exc()
        cur.execute('ROLLBACK')
        conn.commit()
        return None


def getRequestStats(requestName, type):
    """
    Returns an object which contains request-specifc data. Basically just used
    for the expanded comments.
    """
    try:
        basicRequestDict = {}

        requestType = type

        cur.execute("SELECT COUNT(*) FROM requests")
        total = int(cur.fetchone()[0])

        select_request_total = """
        SELECT COUNT(*)
          FROM requests
         WHERE name = %s
           AND type = %s;
        """
        request_total_values = (requestName, requestType)

        cur.execute(select_request_total, request_total_values)
        requestTotal = int(cur.fetchone()[0])
        basicRequestDict['total'] = requestTotal

        if requestTotal == 0:
            return None

        select_unique_subreddits = """
        SELECT COUNT(DISTINCT subreddit)
          FROM requests
         WHERE name = %s
           AND type = %s;
        """
        unique_subreddit_values = (requestName, requestType)

        cur.execute(select_unique_subreddits, unique_subreddit_values)
        dSubreddits = int(cur.fetchone()[0])
        basicRequestDict['uniqueSubreddits'] = dSubreddits

        totalAsPercentage = (float(requestTotal) / total) * 100
        basicRequestDict['totalAsPercentage'] = totalAsPercentage

        conn.commit()
        return basicRequestDict

    except Exception:
        cur.execute('ROLLBACK')
        conn.commit()
        return None


def getUserStats(username, top_media_number=5):
    """
    Returns an object which contains data about the overall database stats
    (i.e. ALL subreddits).
    """
    try:
        basicUserStatDict = {}
        username = str(username).lower()

        select_total_user_comments = """
        SELECT COUNT(1)
          FROM comments
         WHERE LOWER(requester) = %s;
        """
        total_user_comment_values = (username,)

        cur.execute(select_total_user_comments, total_user_comment_values)
        totalUserComments = int(cur.fetchone()[0])
        basicUserStatDict['totalUserComments'] = totalUserComments

        cur.execute("SELECT COUNT(1) FROM comments")
        totalNumComments = int(cur.fetchone()[0])
        basicUserStatDict['totalUserCommentsAsPercentage'] = _percentage(
            totalUserComments,
            totalNumComments
        )

        select_total_user_requests = """
        SELECT COUNT(*)
          FROM requests
         WHERE LOWER(requester) = %s;
        """
        total_user_request_values = (username,)

        cur.execute(select_total_user_requests, total_user_request_values)
        totalUserRequests = int(cur.fetchone()[0])
        basicUserStatDict['totalUserRequests'] = totalUserRequests

        cur.execute("SELECT COUNT(1) FROM requests")
        totalNumRequests = int(cur.fetchone()[0])
        basicUserStatDict['totalUserRequestsAsPercentage'] = _percentage(
            totalUserRequests,
            totalNumRequests
        )

        select_overall_request_rank = """
        SELECT row
          FROM (SELECT requester, COUNT(1), ROW_NUMBER()
                  OVER (ORDER BY count(1) DESC) AS ROW
                  FROM requests
                 GROUP BY requester) AS overallrequestrank
         WHERE LOWER(requester) = %s;
        """
        overall_request_rank_values = (username,)

        cur.execute(select_overall_request_rank, overall_request_rank_values)
        overallRequestRank = int(cur.fetchone()[0])
        basicUserStatDict['overallRequestRank'] = overallRequestRank

        select_unique_requests = """
        SELECT COUNT(DISTINCT (name, type))
          FROM requests
         WHERE LOWER(requester) = %s;
        """
        unique_request_values = (username,)

        cur.execute(select_unique_requests, unique_request_values)
        uniqueRequests = int(cur.fetchone()[0])
        basicUserStatDict['uniqueRequests'] = uniqueRequests

        select_favourite_subreddit_stats = """
        SELECT r.subreddit, COUNT(r.subreddit), total.totalcount
          FROM requests r
               INNER JOIN (SELECT subreddit, COUNT(subreddit) AS totalcount
                             FROM requests
                            GROUP BY subreddit) total
               ON total.subreddit = r.subreddit
         WHERE LOWER(requester) = %s
         GROUP BY r.subreddit, total.totalcount
         ORDER BY COUNT(r.subreddit) DESC LIMIT 1;
        """
        favourite_subreddit_stats_values = (username,)

        cur.execute(
            select_favourite_subreddit_stats,
            favourite_subreddit_stats_values
        )
        favouriteSubredditStats = cur.fetchone()
        favouriteSubreddit = str(favouriteSubredditStats[0])
        favouriteSubredditCount = int(favouriteSubredditStats[1])
        favouriteSubredditOverallCount = int(favouriteSubredditStats[2])
        basicUserStatDict['favouriteSubreddit'] = favouriteSubreddit
        basicUserStatDict['favouriteSubredditCount'] = favouriteSubredditCount
        basicUserStatDict['favouriteSubredditCountAsPercentage'] = (float(
            favouriteSubredditCount) / favouriteSubredditOverallCount) * 100

        select_top_requests = """
        SELECT name, type, COUNT(name)
          FROM requests
         WHERE LOWER(requester) = %s
         GROUP BY name, type
         ORDER BY COUNT(name) DESC, name ASC LIMIT %s;
        """
        top_request_values = (username, top_media_number)

        cur.execute(select_top_requests, top_request_values)
        topRequests = cur.fetchall()
        basicUserStatDict['topRequests'] = []
        for request in topRequests:
            basicUserStatDict['topRequests'].append(request)

        conn.commit()
        return basicUserStatDict

    except Exception:
        cur.execute('ROLLBACK')
        conn.commit()
        return None


def getSubredditStats(
    subredditName,
    top_media_number=5,
    top_username_number=5
):
    """
    Similar to getBasicStats - returns an object which contains data about a
    specific subreddit.
    """
    try:
        basicSubredditDict = {}
        subredditName = subredditName.lower()

        select_total_comments = """
        SELECT COUNT(*)
          FROM comments
         WHERE subreddit = %s;
        """
        total_comments_values = (subredditName,)

        cur.execute(select_total_comments, total_comments_values)
        totalComments = int(cur.fetchone()[0])
        basicSubredditDict['totalComments'] = totalComments

        cur.execute("SELECT COUNT(*) FROM requests;")
        total = int(cur.fetchone()[0])

        select_subreddit_total = """
        SELECT COUNT(*)
          FROM requests
         WHERE subreddit = %s;
        """
        subreddit_total_values = (subredditName,)

        cur.execute(select_subreddit_total, subreddit_total_values)
        sTotal = int(cur.fetchone()[0])
        basicSubredditDict['total'] = sTotal

        if sTotal == 0:
            return None

        select_distinct_names = """
        SELECT COUNT(DISTINCT (name, type))
          FROM requests
         WHERE subreddit = %s;
        """
        distinct_name_values = (subredditName,)

        cur.execute(select_distinct_names, distinct_name_values)
        dNames = int(cur.fetchone()[0])
        basicSubredditDict['uniqueNames'] = dNames

        totalAsPercentage = (float(sTotal) / total) * 100
        basicSubredditDict['totalAsPercentage'] = totalAsPercentage

        meanValue = float(sTotal) / dNames
        basicSubredditDict['meanValuePerRequest'] = meanValue

        variance = 0

        select_subreddit_requests_by_name_and_type = """
        SELECT name, type, COUNT(name)
          FROM requests
         WHERE subreddit = %s
         GROUP BY name, type;
        """
        subreddit_requests_by_name_and_type_values = (subredditName,)

        cur.execute(
            select_subreddit_requests_by_name_and_type,
            subreddit_requests_by_name_and_type_values
        )
        for entry in cur.fetchall():
            variance += (entry[2] - meanValue) * (entry[2] - meanValue)

        variance = variance / dNames
        stdDev = sqrt(variance)
        basicSubredditDict['standardDeviation'] = stdDev

        select_top_requests = """
        SELECT name, type, COUNT(name)
          FROM requests
         WHERE subreddit = %s
         GROUP BY name, type
         ORDER BY COUNT(name) DESC, name ASC LIMIT %s;
        """
        top_requests_values = (subredditName, top_media_number)

        cur.execute(select_top_requests, top_requests_values)
        topRequests = cur.fetchall()
        basicSubredditDict['topRequests'] = []
        for request in topRequests:
            basicSubredditDict['topRequests'].append(request)

        select_top_requesters = """
        SELECT requester, COUNT(requester)
          FROM requests
         WHERE subreddit = %s
         GROUP BY requester
         ORDER BY COUNT(requester) DESC, requester ASC LIMIT %s;
        """
        top_requester_values = (subredditName, top_username_number)

        cur.execute(select_top_requesters, top_requester_values)
        topRequesters = cur.fetchall()
        basicSubredditDict['topRequesters'] = []
        for requester in topRequesters:
            basicSubredditDict['topRequesters'].append(requester)

        conn.commit()

        return basicSubredditDict
    except Exception:
        cur.execute('ROLLBACK')
        conn.commit()
        return None

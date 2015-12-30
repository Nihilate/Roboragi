'''
DatabaseHandler.py
Handles all connections to the database. The database runs on PostgreSQL and is connected to via psycopg2.
'''

import psycopg2
from math import sqrt
import traceback

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

conn = psycopg2.connect("dbname='" + DBNAME + "' user='" + DBUSER + "' host='" + DBHOST + "' password='" + DBPASSWORD + "'")
cur = conn.cursor()

#Sets up the database and creates the databases if they haven't already been made.
def setup():
    try:
        conn = psycopg2.connect("dbname='" + DBNAME + "' user='" + DBUSER + "' host='" + DBHOST + "' password='" + DBPASSWORD + "'")
    except:
        print("Unable to connect to the database")

    cur = conn.cursor()

    #Create requests table
    try:
        cur.execute('CREATE TABLE requests ( id SERIAL PRIMARY KEY, name varchar(320), type varchar(16), requester varchar(50), subreddit varchar(50), requesttimestamp timestamp DEFAULT current_timestamp)')
        conn.commit()
    except Exception as e:
        #traceback.print_exc()
        cur.execute('ROLLBACK')
        conn.commit()

    #Create comments table
    try:
        cur.execute('CREATE TABLE comments ( commentid varchar(16) PRIMARY KEY, requester varchar(50), subreddit varchar(50), hadRequest boolean)')
        conn.commit()
    except Exception as e:
        #traceback.print_exc()
        cur.execute('ROLLBACK')
        conn.commit()

setup()

#--------------------------------------#

# Adds a comment to the "already seen" database. Also handles submissions, which have a similar ID structure.
def addComment(commentid, requester, subreddit, hadRequest):
    try:
        subreddit = str(subreddit).lower()
        
        cur.execute('INSERT INTO comments (commentid, requester, subreddit, hadRequest) VALUES (%s, %s, %s, %s)', (commentid, requester, subreddit, hadRequest))
        conn.commit()
    except Exception as e:
        #traceback.print_exc()
        cur.execute('ROLLBACK')
        conn.commit()

#Returns true if the comment/submission has already been checked.
def commentExists(commentid):
    try:
        cur.execute('SELECT * FROM comments WHERE commentid = %s', (commentid,))
        if (cur.fetchone()) is None:
            conn.commit()
            return False
        else:
            conn.commit()
            return True
    except Exception as e:
        #traceback.print_exc()
        cur.execute('ROLLBACK')
        conn.commit()
        return True
        
#Adds a request to the request-tracking database. rType is either "Anime" or "Manga".
def addRequest(name, rType, requester, subreddit):
    try:
        subreddit = str(subreddit).lower()

        if ('nihilate' not in subreddit):
            cur.execute('INSERT INTO requests (name, type, requester, subreddit) VALUES (%s, %s, %s, %s)', (name, rType, requester, subreddit))
            conn.commit()
    except Exception as e:
        #traceback.print_exc()
        cur.execute('ROLLBACK')
        conn.commit()

#Returns an object which contains data about the overall database stats (i.e. ALL subreddits).
def getBasicStats():
    try:
        basicStatDict = {}

        cur.execute("SELECT COUNT(*) FROM comments")
        totalComments = int(cur.fetchone()[0])
        basicStatDict['totalComments'] = totalComments
        
        cur.execute("SELECT COUNT(*) FROM requests;")
        total = int(cur.fetchone()[0])
        basicStatDict['total'] = total
        
        cur.execute("SELECT COUNT(DISTINCT name) FROM requests;")
        dNames = int(cur.fetchone()[0])
        basicStatDict['uniqueNames'] = dNames

        cur.execute("SELECT COUNT(DISTINCT subreddit) FROM requests;")
        dSubreddits = int(cur.fetchone()[0])
        basicStatDict['uniqueSubreddits'] = dSubreddits

        meanValue = float(total)/dNames
        basicStatDict['meanValuePerRequest'] = meanValue

        variance = 0
        cur.execute("SELECT name, count(name) FROM requests GROUP by name")
        for entry in cur.fetchall():
            variance += (entry[1] - meanValue) * (entry[1] - meanValue)

        variance = variance / dNames
        stdDev = sqrt(variance)
        basicStatDict['standardDeviation'] = stdDev

        cur.execute("SELECT name, type, COUNT(name) FROM requests GROUP BY name, type ORDER BY COUNT(name) DESC, name ASC LIMIT 5")
        topRequests = cur.fetchall()
        basicStatDict['topRequests'] = []
        for request in topRequests:
            basicStatDict['topRequests'].append(request)

        cur.execute("SELECT requester, COUNT(requester) FROM requests GROUP BY requester ORDER BY COUNT(requester) DESC, requester ASC LIMIT 5")
        topRequesters = cur.fetchall()
        basicStatDict['topRequesters'] = []
        for requester in topRequesters:
            basicStatDict['topRequesters'].append(requester)

        conn.commit()
        return basicStatDict
        
    except Exception as e:
        traceback.print_exc()
        cur.execute('ROLLBACK')
        conn.commit()
        return None

#Returns an object which contains request-specifc data. Basically just used for the expanded comments.
def getRequestStats(requestName, isManga):
    try:
        basicRequestDict = {}

        requestType = 'Anime'
        if (isManga):
            requestType = 'Manga'

        cur.execute("SELECT COUNT(*) FROM requests")
        total = int(cur.fetchone()[0])
        
        cur.execute("SELECT COUNT(*) FROM requests WHERE name = %s AND type = %s", (requestName, requestType))
        requestTotal = int(cur.fetchone()[0])
        basicRequestDict['total'] = requestTotal

        if requestTotal == 0:
            return None

        cur.execute("SELECT COUNT(DISTINCT subreddit) FROM requests WHERE name = %s AND type = %s", (requestName, requestType))
        dSubreddits = int(cur.fetchone()[0])
        basicRequestDict['uniqueSubreddits'] = dSubreddits

        totalAsPercentage = (float(requestTotal)/total) * 100
        basicRequestDict['totalAsPercentage'] = totalAsPercentage

        conn.commit()
        return basicRequestDict
        
    except:
        traceback.print_exc()
        cur.execute('ROLLBACK')
        conn.commit()
        return None

#Similar to getBasicStats - returns an object which contains data about a specific subreddit.
def getSubredditStats(subredditName):
    try:
        basicSubredditDict = {}

        cur.execute("SELECT COUNT(*) FROM comments WHERE subreddit = %s", (subredditName,))
        totalComments = int(cur.fetchone()[0])
        basicSubredditDict['totalComments'] = totalComments

        cur.execute("SELECT COUNT(*) FROM requests;")
        total = int(cur.fetchone()[0])
        
        cur.execute("SELECT COUNT(*) FROM requests WHERE subreddit = %s", (subredditName,))
        sTotal = int(cur.fetchone()[0])
        basicSubredditDict['total'] = sTotal

        if sTotal == 0:
            return None

        cur.execute("SELECT COUNT(DISTINCT name) FROM requests WHERE subreddit = %s", (subredditName,))
        dNames = int(cur.fetchone()[0])
        basicSubredditDict['uniqueNames'] = dNames

        totalAsPercentage = (float(sTotal)/total) * 100
        basicSubredditDict['totalAsPercentage'] = totalAsPercentage
        
        meanValue = float(sTotal)/dNames
        basicSubredditDict['meanValuePerRequest'] = meanValue

        variance = 0
        cur.execute("SELECT name, count(name) FROM requests WHERE subreddit = %s GROUP by name", (subredditName,))
        for entry in cur.fetchall():
            variance += (entry[1] - meanValue) * (entry[1] - meanValue)

        variance = variance / dNames
        stdDev = sqrt(variance)
        basicSubredditDict['standardDeviation'] = stdDev

        cur.execute("SELECT name, type, COUNT(name) FROM requests WHERE subreddit = %s GROUP BY name, type ORDER BY COUNT(name) DESC, name ASC LIMIT 5", (subredditName,))
        topRequests = cur.fetchall()
        basicSubredditDict['topRequests'] = []
        for request in topRequests:
            basicSubredditDict['topRequests'].append(request)
        
        cur.execute("SELECT requester, COUNT(requester) FROM requests WHERE subreddit = %s GROUP BY requester ORDER BY COUNT(requester) DESC, requester ASC LIMIT 5", (subredditName,))
        topRequesters = cur.fetchall()
        basicSubredditDict['topRequesters'] = []
        for requester in topRequesters:
            basicSubredditDict['topRequesters'].append(requester)

        conn.commit()
        
        return basicSubredditDict
    except Exception as e:
        traceback.print_exc()
        cur.execute('ROLLBACK')
        conn.commit()
        return None

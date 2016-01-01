'''
AnimeBot.py
Acts as the "main" file and ties all the other functionality together.
'''

import praw
from praw.handlers import MultiprocessHandler
import re
import traceback
import requests
import time

import Search
import CommentBuilder
import DatabaseHandler
import Config

# --- Config Variables ---
USERNAME = ''
PASSWORD = ''
USERAGENT = ''
REDDITAPPID = ''
REDDITAPPSECRET = ''
REFRESHTOKEN = ''
#

try:
    import Config
    USERNAME = Config.username
    PASSWORD = Config.password
    USERAGENT = Config.useragent
    REDDITAPPID = Config.redditappid
    REDDITAPPSECRET = Config.redditappsecret
    REFRESHTOKEN = Config.refreshtoken
except ImportError:
    pass

reddit = praw.Reddit(user_agent=USERNAME)

#There's probably a better way to do this. Might move it to the backend database at some point
subredditlist = 'animenocontext'

#the subreddits where expanded requests are disabled
disableexpanded = []

#Sets up Reddit for PRAW
def setupReddit():
    try:
        print('Setting up Reddit')
        reddit.set_oauth_app_info(client_id=REDDITAPPID, client_secret=REDDITAPPSECRET, redirect_uri='http://127.0.0.1:65010/' 'authorize_callback')
        reddit.refresh_access_information(REFRESHTOKEN)
        print('Reddit successfully set up')
    except Exception as e:
        print('Error with setting up Reddit: ' + str(e))

#The main function
def start():
    print('Starting submission stream:')

    #This opens a constant stream of comments. It will loop until there's a major error (usually this means the Reddit access token needs refreshing)
    submission_stream = praw.helpers.submission_stream(reddit, subredditlist, limit=10, verbosity=0)

    for submission in submission_stream:
        if (DatabaseHandler.commentExists(submission.id)):
            continue

        try:
            if submission.author.name:
                pass
        except:
            if not (DatabaseHandler.commentExists(submission.id)):
                DatabaseHandler.addComment(submission.id, 'Unknown', submission.subreddit, False)

        animeArray = []
        mangaArray = []
        
        #square/round/curly
        for match in re.finditer("(?<=(?<!\[)\[)([^\[\]]*)(?=\](?!\]))|(?<=(?<!\{)\{)([^\{\}]*)(?=\}(?!\}))", submission.title, re.S):
            base = ''
            if match.group(1):
                base = match.group(1)
            elif match.group(2):
                base = match.group(2)
                
            reply = Search.buildAnimeReply(base, False, submission, True)
            if (reply is not None):
                animeArray.append(reply)
            else:
                reply = Search.buildMangaReply(base, False, submission, True)
                if (reply is not None):
                    mangaArray.append(reply)

        #pointed
        for match in re.finditer("(?<=(?<!\<)\<)([^\<\>]*)(?=\>(?!\>))", submission.title, re.S):
            reply = Search.buildMangaReply(match.group(1), False, submission, True)
            if (reply is not None):
                mangaArray.append(reply)

        '''------------------------------------------------------'''
        #Here is where we create the final reply to be posted

        #The final comment reply. We add stuff to this progressively.
        commentReply = ''

        #Basically just to keep track of people posting the same title multiple times (e.g. {Nisekoi}{Nisekoi}{Nisekoi})
        postedAnimeTitles = []
        postedMangaTitles = []

        #Adding all the anime to the final comment. If there's manga too we split up all the paragraphs and indent them in Reddit markup by adding a '>', then recombine them
        for i, animeReply in enumerate(animeArray):
            if not (i is 0):
                commentReply += '\n\n'

            if not (animeReply['title'] in postedAnimeTitles):
                postedAnimeTitles.append(animeReply['title'])
                commentReply += animeReply['comment']
            
        if mangaArray:
            commentReply += '\n\n'

        #Adding all the manga to the final comment
        for i, mangaReply in enumerate(mangaArray):
            if not (i is 0):
                commentReply += '\n\n'
            
            if not (mangaReply['title'] in postedMangaTitles):
                postedMangaTitles.append(mangaReply['title'])
                commentReply += mangaReply['comment']

        #If there are more than 10 requests, shorten them all 
        if not (commentReply is '') and (len(animeArray) + len(mangaArray) >= 10):
            commentReply = re.sub(r"\^\((.*?)\)", "", commentReply, flags=re.M)

        #If there was actually something found, add the signature and post the comment to Reddit. Then, add the comment to the "already seen" database.
        if not (commentReply is ''):
            commentReply += Config.getSignature(submission.permalink)
            
            try:
                submission.add_comment(commentReply)
                print("Comment made.\n")

                try:
                    pass
                    DatabaseHandler.addComment(submission.id, submission.author.name, submission.subreddit, True)
                except:
                    traceback.print_exc()
            except:
                traceback.print_exc()
        else:
            try:
                pass
                DatabaseHandler.addComment(submission.id, submission.author.name, submission.subreddit, False)
            except:
                traceback.print_exc()


# ------------------------------------#
#Here's the stuff that actually gets run

#Initialise Reddit.
setupReddit()

#Loop the comment stream until the Reddit access token expires. Then get a new access token and start the stream again.
while 1:
    try:        
        start()
    except Exception as e:
        pass
        #traceback.print_exc()

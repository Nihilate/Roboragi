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
import Reference

TIME_BETWEEN_PM_CHECKS = 60 #in seconds

try:
    import Config
    USERNAME = Config.username
    PASSWORD = Config.password
    USERAGENT = Config.useragent
    REDDITAPPID = Config.redditappid
    REDDITAPPSECRET = Config.redditappsecret
    REFRESHTOKEN = Config.refreshtoken
    SUBREDDITLIST = Config.get_formatted_subreddit_list()
except ImportError:
    pass

reddit = praw.Reddit(user_agent=USERNAME)

#the subreddits where expanded requests are disabled
disableexpanded = ['animesuggest']

#subreddits I'm actively avoiding
exiled = ['anime']

#Sets up Reddit for PRAW
def setupReddit():
    try:
        print('Setting up Reddit')
        reddit.set_oauth_app_info(client_id=REDDITAPPID, client_secret=REDDITAPPSECRET, redirect_uri='http://127.0.0.1:65010/' 'authorize_callback')
        reddit.refresh_access_information(REFRESHTOKEN)
        print('Reddit successfully set up')
    except Exception as e:
        print('Error with setting up Reddit: ' + str(e))

#function for processing edit requests via pm
def process_pms():
    for msg in reddit.get_unread(limit=None):
        if ((msg.subject == 'username mention') or (msg.subject == 'comment reply' and 'u/roboragi' in msg.body.lower())):
            if (('{' and '}') in msg.body) or (('<' and '>') in msg.body) or ((']' and '[') in msg.body):
                try:
                    if str(msg.subreddit).lower() in exiled:
                        #print('Edit request from exiled subreddit: ' + str(msg.subreddit) + '\n')
                        #msg.mark_as_read()
                        continue

                    mentionedComment = reddit.get_info(thing_id=msg.name)
                    mentionedComment.refresh()

                    replies = mentionedComment.replies

                    ownComments = []
                    commentToEdit = None

                    for reply in replies:
                        if (reply.author.name == 'Roboragi'):
                            ownComments.append(reply)

                    for comment in ownComments:
                        if 'http://www.reddit.com/r/Roboragi/wiki/index' in comment.body:
                            commentToEdit = comment

                    commentReply = process_comment(mentionedComment, True)

                    try:
                        if (commentReply):
                            if commentToEdit:
                                commentToEdit.edit(commentReply)
                                print('Comment edited.\n')
                            else:
                                mentionedComment.reply(commentReply)
                                print('Comment made.\n')
                            
                            msg.mark_as_read()
                            
                            if not (DatabaseHandler.commentExists(mentionedComment.id)):
                                DatabaseHandler.addComment(mentionedComment.id, mentionedComment.author.name, msg.subreddit, True)
                    except praw.errors.Forbidden:
                        print('Edit request from banned subreddit: ' + str(msg.subreddit) + '\n')

                except Exception as e:
                    print(e)

#process dat comment
def process_comment(comment, is_edit=False):
    #Anime/Manga requests that are found go into separate arrays
    animeArray = []
    mangaArray = []
    lnArray = []

    #ignores all "code" markup (i.e. anything between backticks)
    comment.body = re.sub(r"\`[{<\[]+(.*?)[}>\]]+\`", "", comment.body)

    num_so_far = 0

    numOfRequest = 0
    numOfExpandedRequest = 0
    
    #This checks for requests. First up we check all known tags for the !stats request
    if re.search('({!stats.*?}|{{!stats.*?}}|<!stats.*?>|<<!stats.*?>>)', comment.body, re.S) is not None:
        username = re.search('[uU]\/([A-Za-z0-9_-]+?)(>|}|$)', comment.body, re.S)
        subreddit = re.search('[rR]\/([A-Za-z0-9_]+?)(>|}|$)', comment.body, re.S)

        if username:
            commentReply = CommentBuilder.buildStatsComment(username=username.group(1))
        elif subreddit:
            commentReply = CommentBuilder.buildStatsComment(subreddit=subreddit.group(1))
        else:
            commentReply = CommentBuilder.buildStatsComment()
    else:
        
        #The basic algorithm here is:
        #If it's an expanded request, build a reply using the data in the braces, clear the arrays, add the reply to the relevant array and ignore everything else.
        #If it's a normal request, build a reply using the data in the braces, add the reply to the relevant array.

        #Counts the number of expanded results vs total results. If it's not just a single expanded result, they all get turned into normal requests.
        
        forceNormal = False

        for match in re.finditer("\{{2}([^}]*)\}{2}|\<{2}([^>]*)\>{2}|\]{2}([^]]*)\[{2}", comment.body, re.S):
            numOfRequest += 1
            numOfExpandedRequest += 1
            
        for match in re.finditer("(?<=(?<!\{)\{)([^\{\}]*)(?=\}(?!\}))|(?<=(?<!\<)\<)([^\<\>]*)(?=\>(?!\>))|(?<=(?<!\])\](?!\())([^\]\[]*)(?=\[(?!\[))", comment.body, re.S):
            numOfRequest += 1

        if (numOfExpandedRequest >= 1) and (numOfRequest > 1):
            forceNormal = True

        #The final comment reply. We add stuff to this progressively.
        commentReply = ''

        #if (numOfRequest + numOfExpandedRequest) > 25:
        #    commentReply = 'You have tried to request too many things at once. Please reduce the number of requests and try again.'
        #else:

        #Expanded Anime
        for match in re.finditer("\{{2}([^}]*)\}{2}", comment.body, re.S):
            if num_so_far < 30:
                reply = ''

                if (forceNormal) or (str(comment.subreddit).lower() in disableexpanded):
                    reply = Search.buildAnimeReply(match.group(1), False, comment)
                else:
                    reply = Search.buildAnimeReply(match.group(1), True, comment)                    

                if (reply is not None):
                    num_so_far = num_so_far + 1
                    animeArray.append(reply)

        #Normal Anime  
        for match in re.finditer("(?<=(?<!\{)\{)([^\{\}]*)(?=\}(?!\}))", comment.body, re.S):
            if num_so_far < 30:
                reply = Search.buildAnimeReply(match.group(1), False, comment)
                
                if (reply is not None):
                    num_so_far = num_so_far + 1
                    animeArray.append(reply)

        #Expanded Manga
        #NORMAL EXPANDED
        for match in re.finditer("\<{2}([^>]*)\>{2}(?!(:|\>))", comment.body, re.S):
            if num_so_far < 30:
                reply = ''
                
                if (forceNormal) or (str(comment.subreddit).lower() in disableexpanded):
                    reply = Search.buildMangaReply(match.group(1), False, comment)
                else:
                    reply = Search.buildMangaReply(match.group(1), True, comment)

                if (reply is not None):
                    num_so_far = num_so_far + 1
                    mangaArray.append(reply)

        #Normal Manga
        #NORMAL
        for match in re.finditer("(?<=(?<!\<)\<)([^\<\>]+)\>(?!(:|\>))", comment.body, re.S):
            if num_so_far < 30:
                reply = Search.buildMangaReply(match.group(1), False, comment)

                if (reply is not None):
                    num_so_far = num_so_far + 1
                    mangaArray.append(reply)

        #Expanded LN
        for match in re.finditer("\]{2}([^]]*)\[{2}", comment.body, re.S):
            if num_so_far < 30:
                reply = ''

                if (forceNormal) or (str(comment.subreddit).lower() in disableexpanded):
                    reply = Search.buildLightNovelReply(match.group(1), False, comment)
                else:
                    reply = Search.buildLightNovelReply(match.group(1), True, comment)                    

                if (reply is not None):
                    num_so_far = num_so_far + 1
                    lnArray.append(reply)

        #Normal LN  
        for match in re.finditer("(?<=(?<!\])\](?!\())([^\]\[]*)(?=\[(?!\[))", comment.body, re.S):
            if num_so_far < 30:
                reply = Search.buildLightNovelReply(match.group(1), False, comment)
                
                if (reply is not None):
                    num_so_far = num_so_far + 1
                    lnArray.append(reply)
        
        #Here is where we create the final reply to be posted

        #Basically just to keep track of people posting the same title multiple times (e.g. {Nisekoi}{Nisekoi}{Nisekoi})
        postedAnimeTitles = []
        postedMangaTitles = []
        postedLNTitles = []

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

        if lnArray:
            commentReply += '\n\n'

        #Adding all the manga to the final comment
        for i, lnReply in enumerate(lnArray):
            if not (i is 0):
                commentReply += '\n\n'
            
            if not (lnReply['title'] in postedLNTitles):
                postedLNTitles.append(lnReply['title'])
                commentReply += lnReply['comment']

        #If there are more than 10 requests, shorten them all 
        if not (commentReply is '') and (len(animeArray) + len(mangaArray)+ len(lnArray) >= 10):
            commentReply = re.sub(r"\^\((.*?)\)", "", commentReply, flags=re.M)

    #If there was actually something found, add the signature and post the comment to Reddit. Then, add the comment to the "already seen" database.
    if commentReply is not '':
        '''if (comment.author.name == 'treborabc'):
            commentReply = '[No.](https://www.reddit.com/r/anime_irl/comments/4sba1n/anime_irl/d58xkha)'''
        
        if num_so_far >= 30:
            commentReply += "\n\nI'm limited to 30 requests at once and have had to cut off some, sorry for the inconvinience!\n\n"

        commentReply += Config.getSignature(comment.permalink)

        commentReply += Reference.get_bling(comment.author.name)

        total_expected = int(numOfRequest)
        total_found = int(len(animeArray) + len(mangaArray)+ len(lnArray))
        
        if total_found != total_expected:
            commentReply += '&#32;|&#32;('+str(total_found)+'/'+str(total_expected)+')'

        if is_edit:
            return commentReply
        else:
            try:
                comment.reply(commentReply)
                print("Comment made.\n")
            except praw.errors.Forbidden:
                print('Request from banned subreddit: ' + str(comment.subreddit) + '\n')
            except Exception:
                traceback.print_exc()

            comment_author = comment.author.name if comment.author else '!UNKNOWN!'
            
            try:
                DatabaseHandler.addComment(comment.id, comment_author, comment.subreddit, True)
            except:
                traceback.print_exc()
    else:
        try:
            if is_edit:
                return None
            else:
                comment_author = comment.author.name if comment.author else '!UNKNOWN!'
                
                DatabaseHandler.addComment(comment.id, comment_author, comment.subreddit, False)
        except:
            traceback.print_exc()
    

#The main function
def start():
    last_checked_pms = time.time()

    #This opens a constant stream of comments. It will loop until there's a major error (usually this means the Reddit access token needs refreshing)
    comment_stream = praw.helpers.comment_stream(reddit, SUBREDDITLIST, limit=250, verbosity=0)

    for comment in comment_stream:

        # check if it's time to check the PMs
        if (time.time() - last_checked_pms) > TIME_BETWEEN_PM_CHECKS:
            process_pms()
            last_checked_pms = time.time()

        #Is the comment valid (i.e. it's not made by Roboragi and I haven't seen it already). If no, try to add it to the "already seen pile" and skip to the next comment. If yes, keep going.
        if not (Search.isValidComment(comment, reddit)):
            try:
                if not (DatabaseHandler.commentExists(comment.id)):
                    DatabaseHandler.addComment(comment.id, comment.author.name, comment.subreddit, False)
            except:
                pass
            continue

        process_comment(comment)


# ------------------------------------#
#Here's the stuff that actually gets run

#Initialise Reddit.
setupReddit()

#Loop the comment stream until the Reddit access token expires. Then get a new access token and start the stream again.
while 1:
    try:        
        start()
    except Exception as e:
        traceback.print_exc()
        pass

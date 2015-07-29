'''
Search.py
Returns a built comment created from multiple databases when given a search term.
'''

import MAL
import Hummingbird
import Anilist
import MU

import CommentBuilder
import DatabaseHandler

import traceback
import time

USERNAME = ''

try:
    import Config
    USERNAME = Config.username
except ImportError:
    pass

#Builds a manga reply from multiple sources
def buildMangaReply(searchText, isExpanded, baseComment):
    try:
        #Basic breakdown:
        #If Anilist finds something, use it to find the MAL version.
        #If hits either MAL or Ani, use it to find the MU version.
        #If it hits either, add it to the request-tracking DB.
        
        ani = Anilist.getMangaDetails(searchText)
        mal = None
        mu = None
        
        if not (ani is None):
            mal = MAL.getMangaDetails(ani['title_romaji'])

        else:
            mal = MAL.getMangaDetails(searchText)

            if not (mal is None):
                ani = Anilist.getMangaDetails(mal['title'])

        if (ani is not None) or (mal is not None):
            try:
                titleToAdd = ''
                if mal is not None:
                    titleToAdd = mal['title']
                    mu = MU.getMangaURL(mal['title'])
                else:
                    titleToAdd = ani['title_english']
                    mu = MU.getMangaURL(ani['title_romaji'])

                if (str(baseComment.subreddit).lower is not 'nihilate'):
                    DatabaseHandler.addRequest(titleToAdd, 'Manga', baseComment.author.name, baseComment.subreddit)
            except:
                traceback.print_exc()
                pass
            
            return CommentBuilder.buildMangaComment(isExpanded, mal, ani, mu)
    
    except Exception as e:
        traceback.print_exc()
        return None

#Builds an anime reply from multiple sources
def buildAnimeReply(searchText, isExpanded, baseComment):
    try:
        #Basic breakdown:
        #If Anilist finds something, use it to find the HB version.
        #If we can't find it, try with HB and use it to try and "refind" Anilist
        #If we hit HB, we don't need to look for MAL, since we can get the MAL ID from within HB. If we don't hit HB, find MAL on its own.
        #If, at the end, we have something from Anilist, get the full set of Anilist data
        #If it hits anything, add it to the request-tracking DB.
        
        ani = Anilist.getAnimeDetails(searchText)
        hb = None
        mal = None
        
        if (ani is not None):
            hb = Hummingbird.getAnimeDetails(ani['title_romaji'])
        else:
            hb = Hummingbird.getAnimeDetails(searchText)
            if (hb is not None):
               ani = Anilist.getAnimeDetails(hb['title'])
            else:
                mal = MAL.getAnimeDetails(searchText)
                if (mal is not None):
                    hb = Hummingbird.getAnimeDetails(mal['title'])
                    ani = Anilist.getAnimeDetails(mal['title'])

        try:
            if ani is not None:
                aniFull = Anilist.getFullAnimeDetails(ani['id'])
                if aniFull is not None:
                    ani = aniFull
        except:
            pass

        if (ani is not None) or (hb is not None):
            try:
                titleToAdd = ''
                if ani is None:
                    titleToAdd = hb['title']
                else:
                    titleToAdd = ani['title_romaji']

                if (str(baseComment.subreddit).lower is not 'nihilate'):
                    DatabaseHandler.addRequest(titleToAdd, 'Anime', baseComment.author.name, baseComment.subreddit)
            except:
                traceback.print_exc()
                pass
            
            return CommentBuilder.buildAnimeComment(isExpanded, mal, hb, ani)

    except Exception as e:
        traceback.print_exc()
        return None

#Checks if the bot is the parent of this comment.
def isBotAParent(comment, reddit):
    try:
        parentComment = reddit.get_info(thing_id=comment.parent_id)

        if (parentComment.author.name == USERNAME):
            return True
        else:
            return False
            
    except:
        traceback.print_exc()
        return True

#Checks if the comment is valid (i.e. not already seen, not a post by Roboragi and the parent commenter isn't Roboragi)
def isValidComment(comment, reddit):
    try:
        if (DatabaseHandler.commentExists(comment.id)):
            return False

        try:
            if (comment.author.name == USERNAME):
                DatabaseHandler.addComment(comment.id, comment.author.name, comment.subreddit, False)
                return False
        except:
            pass

        if (isBotAParent(comment, reddit)):
            return False

        return True
        
    except:
        traceback.print_exc()
        return False

#Checks if a submission is valid (i.e. not already seen, not a submission by Roboragi). This WAS used before, but I have since removed the functionality it was relevant to.
def isValidSubmission(submission):
    try:
        if (DatabaseHandler.commentExists(submission.id)):
            return False

        try:
            if (submission.author.name == 'Roboragi'):
                DatabaseHandler.addComment(submission.id, submission.author.name, submission.subreddit, False)
                return False
        except:
            pass

        return True
        
    except:
        traceback.print_exc()
        return False

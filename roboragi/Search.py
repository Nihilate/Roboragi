'''
Search.py
Returns a built comment created from multiple databases when given a search term.
'''

import MAL
import AnimePlanet as AniP
import Hummingbird
import Anilist
import MU

import CommentBuilder
import DatabaseHandler

import traceback
import time

import sqlite3
import json

import pprint

USERNAME = ''

try:
    import Config
    USERNAME = Config.username
except ImportError:
    pass

sqlConn = sqlite3.connect('synonyms.db')
sqlCur = sqlConn.cursor()

try:
    sqlCur.execute('SELECT dbLinks FROM synonyms WHERE type = "Manga" and lower(name) = ?', ["despair simulator"])
except sqlite3.Error as e:
    print(e)

#Builds a manga reply from multiple sources
def buildMangaReply(searchText, isExpanded, baseComment, blockTracking=False):
    try:
        ani = None
        mal = None
        mu = None
        ap = None
        
        try:
            sqlCur.execute('SELECT dbLinks FROM synonyms WHERE type = "Manga" and lower(name) = ?', [searchText.lower()])
        except sqlite3.Error as e:
            print(e)

        alternateLinks = sqlCur.fetchone()

        if (alternateLinks):
            synonym = json.loads(alternateLinks[0])
            
            if (synonym['mal']):
                mal = MAL.getMangaDetails(synonym['mal'])
            if (synonym['ani']):
                ani = Anilist.getMangaDetails(synonym['ani'])
            if (synonym['mu']):
                mu = MU.getMangaURL(synonym['mu'])
            if (synonym['ap']):
                ap = AniP.getMangaURL(synonym['ap'])

        else:
            #Basic breakdown:
            #If Anilist finds something, use it to find the MAL version.
            #If hits either MAL or Ani, use it to find the MU version.
            #If it hits either, add it to the request-tracking DB.
            ani = Anilist.getMangaDetails(searchText)
            
            if not (ani is None):
                mal = MAL.getMangaDetails(ani['title_romaji'])

            else:
                mal = MAL.getMangaDetails(searchText)

                if not (mal is None):
                    ani = Anilist.getMangaDetails(mal['title'])    

        #----- Finally... -----#
        if ani or mal:
            try:
                titleToAdd = ''
                if mal:
                    titleToAdd = mal['title']
                else:
                    titleToAdd = ani['title_english']

                
                if not alternateLinks:
                    #MU stuff
                    if mal:
                        mu = MU.getMangaURL(mal['title'])
                    else:
                        mu = MU.getMangaURL(ani['title_romaji'])

                    #Do the anime-planet stuff
                    if mal and not ap:
                        if mal['title'] and not ap:
                            ap = AniP.getMangaURL(mal['title'])
                        if mal['english'] and not ap:
                            ap = AniP.getMangaURL(mal['english'])
                        if mal['synonyms'] and not ap:
                            for synonym in mal['synonyms']:
                                if ap:
                                    break
                                ap = AniP.getMangaURL(synonym)

                    if ani and not ap:
                        if ani['title_english'] and not ap:
                            ap = AniP.getMangaURL(ani['title_english'])
                        if ani['title_romaji'] and not ap:
                            ap = AniP.getMangaURL(ani['title_romaji'])
                        if ani['synonyms'] and not ap:
                            for synonym in ani['synonyms']:
                                if ap:
                                    break
                                ap = AniP.getMangaURL(synonym)

                if (str(baseComment.subreddit).lower is not 'nihilate') and (str(baseComment.subreddit).lower is not 'roboragi') and not blockTracking:
                    DatabaseHandler.addRequest(titleToAdd, 'Manga', baseComment.author.name, baseComment.subreddit)
            except:
                traceback.print_exc()
                pass
        
        return CommentBuilder.buildMangaComment(isExpanded, mal, ani, mu, ap)
        
    except Exception as e:
        traceback.print_exc()
        return None

#Builds a manga search for a specific series by a specific author
def buildMangaReplyWithAuthor(searchText, authorName, isExpanded, baseComment, blockTracking=False):
    try:        
        ani = Anilist.getMangaWithAuthor(searchText, authorName)
        mal = None
        mu = None
        ap = None
        
        if ani:
            mal = MAL.getMangaCloseToDescription(searchText, ani['description'])
            ap = AniP.getMangaURL(ani['title_english'], authorName)
        else:
            ap = AniP.getMangaURL(searchText, authorName)

        mu = MU.getMangaWithAuthor(searchText, authorName)

        if ani:
            try:
                titleToAdd = ''
                if mal is not None:
                    titleToAdd = mal['title']
                else:
                    titleToAdd = ani['title_english']

                if (str(baseComment.subreddit).lower is not 'nihilate') and (str(baseComment.subreddit).lower is not 'roboragi') and not blockTracking:
                    DatabaseHandler.addRequest(titleToAdd, 'Manga', baseComment.author.name, baseComment.subreddit)
            except:
                traceback.print_exc()
                pass
            
            return CommentBuilder.buildMangaComment(isExpanded, mal, ani, mu, ap)
    
    except Exception as e:
        traceback.print_exc()
        return None

#Builds an anime reply from multiple sources
def buildAnimeReply(searchText, isExpanded, baseComment, blockTracking=False):
    try:

        mal = None
        hb = None
        ani = None
        ap = None
        
        try:
            sqlCur.execute('SELECT dbLinks FROM synonyms WHERE type = "Anime" and lower(name) = ?', [searchText.lower()])
        except sqlite3.Error as e:
            print(e)

        alternateLinks = sqlCur.fetchone()

        if (alternateLinks):
            synonym = json.loads(alternateLinks[0])

            if (synonym['mal']):
                mal = MAL.getAnimeDetails(synonym['mal'])
            if (synonym['hb']):
                hb = Hummingbird.getAnimeDetails(synonym['hb'])
            if (synonym['ani']):
                ani = Anilist.getAnimeDetails(synonym['ani'])
            if (synonym['ap']):
                ap = AniP.getAnimeURL(synonym['ap'])
        else:
            #Basic breakdown:
            #If Anilist finds something, use it to find the HB version.
            #If we can't find it, try with HB and use it to try and "refind" Anilist
            #If we hit HB, we don't need to look for MAL, since we can get the MAL ID from within HB. If we don't hit HB, find MAL on its own.
            #If, at the end, we have something from Anilist, get the full set of Anilist data
            #If it hits anything, add it to the request-tracking DB.
            
            ani = Anilist.getAnimeDetails(searchText)
            
            if (ani is not None):
                hb = Hummingbird.getAnimeDetails(ani['title_romaji'])

                if (hb is None):
                    for synonym in ani['synonyms']:
                        hb = Hummingbird.getAnimeDetails(synonym)
                        if hb is not None:
                            break
                    hb = Hummingbird.getAnimeDetails(ani['title_english'])
            else:
                hb = Hummingbird.getAnimeDetails(searchText)
                if (hb is not None):
                   ani = Anilist.getAnimeDetails(hb['title'])

            #Doing MAL stuff
            if not mal:
                if hb:
                    mal = MAL.getAnimeDetails(hb['title'])

                    if not mal and hb['alternate_title']:
                        if (hb['alternate_title']):
                            mal = MAL.getAnimeDetails(hb['alternate_title'])
                        
                if ani and not mal:
                    mal = MAL.getAnimeDetails(ani['title_romaji'])

                    if not mal:
                        mal = MAL.getAnimeDetails(ani['title_english'])

                    if not mal and ani['synonyms']:
                        for synonym in ani['synonyms']:
                            if mal:
                                break
                            mal = MAL.getAnimeDetails(synonym)

                if not mal:
                    mal = MAL.getAnimeDetails(searchText)

                if mal and not hb:
                    hb = Hummingbird.getAnimeDetails(mal['title'])
                    if not hb:
                        hb = Hummingbird.getAnimeDetails(mal['english'])

                if mal and not ani:
                    ani = Anilist.getAnimeDetails(mal['title'])
                    if not ani:
                        ani = Anilist.getAnimeDetails(mal['english'])

        #----- Finally... -----#
        try:
            if ani is not None:
                aniFull = Anilist.getFullAnimeDetails(ani['id'])
                if aniFull is not None:
                    ani = aniFull
        except:
            pass

        if (ani is not None) or (hb is not None) or (mal is not None):
            try:
                titleToAdd = ''
                if mal:
                    titleToAdd = mal['title']
                if hb:
                    titleToAdd = hb['title']
                if ani:
                    titleToAdd = ani['title_romaji']

                #Do Anime-Planet stuff
                if mal and not ap:
                    if mal['title'] and not ap:
                        ap = AniP.getAnimeURL(mal['title'])
                    if mal['english'] and not ap:
                        ap = AniP.getAnimeURL(mal['english'])
                    if mal['synonyms'] and not ap:
                        for synonym in mal['synonyms']:
                            if ap:
                                break
                            ap = AniP.getAnimeURL(synonym)

                if hb and not ap:
                    if hb['title'] and not ap:
                        ap = AniP.getAnimeURL(hb['title'])
                    if hb['alternate_title'] and not ap:
                        ap = AniP.getAnimeURL(hb['alternate_title'])
                
                if ani and not ap:
                    if ani['title_english'] and not ap:
                        ap = AniP.getAnimeURL(ani['title_english'])
                    if ani['title_romaji'] and not ap:
                        ap = AniP.getAnimeURL(ani['title_romaji'])
                    if ani['synonyms'] and not ap:
                        for synonym in ani['synonyms']:
                            if ap:
                                break
                            ap = AniP.getAnimeURL(synonym)

                if (str(baseComment.subreddit).lower is not 'nihilate') and (str(baseComment.subreddit).lower is not 'roboragi') and not blockTracking:
                    DatabaseHandler.addRequest(titleToAdd, 'Anime', baseComment.author.name, baseComment.subreddit)
            except:
                traceback.print_exc()
                pass6
        
        return CommentBuilder.buildAnimeComment(isExpanded, mal, hb, ani, ap)

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
        #traceback.print_exc()
        return False

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

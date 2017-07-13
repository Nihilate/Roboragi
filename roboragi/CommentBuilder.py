'''
CommentBuilder.py
Takes the data given to it by search and formats it into a comment
'''

import re
from os import linesep
import traceback
import DatabaseHandler
import pprint

#Removes the (Source: MAL) or (Written by X) bits from the decriptions in the databases
def cleanupDescription(desc):    
    for match in re.finditer("([\[\<\(](.*?)[\]\>\)])", desc, re.S):
        if 'ource' in match.group(1).lower():
            desc = desc.replace(match.group(1), '')
        if 'MAL' in match.group(1):
            desc = desc.replace(match.group(1), '')

    for match in re.finditer("([\<](.*?)[\>])", desc, re.S):
        if 'br' in match.group(1).lower():
            desc = desc.replace(match.group(1), '')
        
    reply = ''
    for i, line in enumerate(linesep.join([s for s in desc.splitlines() if s]).splitlines()):
        if i is not 0:
            reply += '\n'
        reply += '>' + line + '\n'
    return reply

#Builds an anime comment from MAL/HB/Anilist data
def buildAnimeComment(isExpanded, mal, ani, ap, anidb):
    try:
        comment = ''

        title = None
        jTitle = None

        cType = None

        malURL = None
        aniURL = None
        apURL = ap
        anidbURL = anidb
        
        youtubeTrailer = None

        status = None
        episodes = None
        genres = []

        countdown = None
        nextEpisode = None
        
        desc = None

        if mal:
            desc = mal['synopsis']

            if mal['type']:
                cType = mal['type']
            
            malURL = 'http://myanimelist.net/anime/' + str(mal['id'])

        if ani is not None:
            title = ani['title_romaji']
            aniURL = 'http://anilist.co/anime/' + str(ani['id'])

            try:
                cType = ani['type']
                desc = ani['description']
            except:
                pass

            status = ani['airing_status'].title()

            try:
                if ani['title_japanese'] is not None:
                    jTitle = ani['title_japanese']

                if ani['youtube_id'] is not None:
                    youtubeTrailer = ani['youtube_id']

                if ani['total_episodes'] is not None:
                    if ani['total_episodes'] == 0:
                        episodes = 'Unknown'
                    else:
                        episodes = ani['total_episodes']

                if ani['genres'] is not None:
                    genres = ani['genres']

                if ani['airing'] is not None:
                    countdown = ani['airing']['countdown']
                    nextEpisode = ani['airing']['next_episode']
            except:
                print('No full details for Anilist')

        stats = DatabaseHandler.getRequestStats(title, 'Anime')

        if ani is not None:
            stats = DatabaseHandler.getRequestStats(ani['title_romaji'],'Anime')

        #---------- BUILDING THE COMMENT ----------#
                
        #----- TITLE -----#
        comment += '**' + title.strip() + '** - ('

        #----- LINKS -----#
        urlComments = []

        try:
        	mal_english = mal['english']
        except:
        	pass
        
        if malURL and mal_english:
            urlComments.append('[MAL](' + sanitise_url_for_markdown(malURL) + ' "' + mal_english + '")')
        elif malURL:
        	urlComments.append('[MAL](' + sanitise_url_for_markdown(malURL) + ')')

        if apURL is not None:
            urlComments.append('[A-P](' + sanitise_url_for_markdown(apURL) + ')')
        if ani is not None:
            urlComments.append('[AL](' + sanitise_url_for_markdown(aniURL) + ')')
        if anidbURL is not None:
            urlComments.append('[ADB](' + sanitise_url_for_markdown(anidbURL) + ')')

        for i, link in enumerate(urlComments):
            if i is not 0:
                comment += ', '
            comment += link

        comment += ')'

        #----- JAPANESE TITLE -----#
        if (isExpanded):
            if jTitle is not None:
                comment += '\n\n'
                
                splitJTitle = jTitle.split()
                for i, word in enumerate(splitJTitle):
                    if not (i == 0):
                        comment += ' '
                    comment += '^^' + word

        #----- INFO LINE -----#            
        if (isExpanded):
            comment += '\n\n^('

            if cType:
                comment += '**' + cType + '** | '
            
            comment += '**Status:** ' + status

            if cType != 'Movie':
                comment += ' | **Episodes:** ' + str(episodes)

            comment += ' | **Genres:** '
        else:
            comment += '\n\n^('

            if cType:
                comment += cType + ' | '

            comment += 'Status: ' + status

            if cType != 'Movie':
                comment += ' | Episodes: ' + str(episodes)

            comment += ' | Genres: '

        if not (genres == []):
            for i, genre in enumerate(genres):
                if i is not 0:
                    comment += ', '
                comment += genre
        else:
            comment += 'None'
            
        if (isExpanded) and (stats is not None):
            comment += '  \n**Stats:** ' + str(stats['total']) + ' requests across ' + str(stats['uniqueSubreddits']) + ' subreddit(s)^) ^- ^' + str(round(stats['totalAsPercentage'],3)) + '% ^of ^all ^requests'
        else:
            comment += ')'

        #----- EPISODE COUNTDOWN -----#
        if (countdown is not None) and (nextEpisode is not None):
            #countdown is given to us in seconds
            days, countdown = divmod(countdown, 24*60*60)
            hours, countdown = divmod(countdown, 60*60)
            minutes, countdown = divmod(countdown, 60)
                               
            comment += '\n\n^(Episode ' + str(nextEpisode) + ' airs in ' + str(days) + ' days, ' + str(hours) + ' hours, ' + str(minutes) + ' minutes)'

        #----- DESCRIPTION -----#
        if (isExpanded):
            comment += '\n\n' + cleanupDescription(desc)

        #----- END -----#
        receipt = '(A) Request successful: ' + title + ' - '
        if malURL is not None:
            receipt += 'MAL '
        if apURL is not None:
            receipt += 'AP '
        if ani is not None:
            receipt += 'AL '
        if anidbURL is not None:
            receipt += 'ADB '
        print(receipt)

        #We return the title/comment separately so we can track if multiples of the same comment have been requests (e.g. {Nisekoi}{Nisekoi}{Nisekoi})
        dictToReturn = {}
        dictToReturn['title'] = title
        dictToReturn['comment'] = comment

        return dictToReturn
    except:
        traceback.print_exc()
        return None

#Builds a manga comment from MAL/Anilist/MangaUpdates data
def buildMangaComment(isExpanded, mal, ani, mu, ap):
    try:
        comment = ''

        title = None
        jTitle = None

        cType = None

        malURL = None
        aniURL = None
        muURL = mu
        apURL = ap

        status = None
        chapters = None
        volumes = None
        genres = []
        
        desc = None

        if not (mal is None):
            title = mal['title']
            malURL = 'http://myanimelist.net/manga/' + str(mal['id'])
            desc = mal['synopsis']
            status = mal['status']

            cType = mal['type']

            try:
                if (int(mal['chapters']) == 0):
                    chapters = 'Unknown'
                else:
                    chapters = mal['chapters']
            except:
                chapters = 'Unknown'

            try:
                if (int(mal['volumes']) == 0):
                    volumes = 'Unknown'
                else:
                    volumes = mal['volumes']
            except:
                volumes = 'Unknown'

        if ani is not None:
            if title is None:
                title = ani['title_english']
            aniURL = 'http://anilist.co/manga/' + str(ani['id'])
            
            if ani['description']:
                desc = ani['description']
            
            try:
                status = ani['publishing_status'].title()
            except:
                pass

            cType = ani['type']

            try:
                if ani['title_japanese'] is not None:
                    jTitle = ani['title_japanese']

                if ani['total_chapters'] is not None:
                    if ani['total_chapters'] == 0:
                        chapters = 'Unknown'
                    else:
                        chapters = ani['total_chapters']
                else:
                    volumes = 'Unknown'

                if ani['total_volumes'] is not None:
                    if ani['total_volumes'] == 0:
                        volumes = 'Unknown'
                    else:
                        volumes = ani['total_volumes']
                else:
                    volumes = 'Unknown'

                if ani['genres'] is not None:
                    genres = ani['genres']

            except Exception as e:
                print(e)

        stats = DatabaseHandler.getRequestStats(title,'Manga')
        
        #---------- BUILDING THE COMMENT ----------#
                
        #----- TITLE -----#
        comment += '**' + title.strip() + '** - ('

        #----- LINKS -----#
        urlComments = []
        
        try:
        	mal_english = mal['english']
        except:
        	pass
        
        if malURL and mal_english:
            urlComments.append('[MAL](' + sanitise_url_for_markdown(malURL) + ' "' + mal_english + '")')
        elif malURL:
        	urlComments.append('[MAL](' + sanitise_url_for_markdown(malURL) + ')')

        if apURL is not None:
            urlComments.append('[A-P](' + sanitise_url_for_markdown(apURL) + ')')
        if aniURL is not None:
            urlComments.append('[AL](' + sanitise_url_for_markdown(aniURL) + ')')
        if muURL is not None:
            urlComments.append('[MU](' + sanitise_url_for_markdown(muURL) + ')')

        for i, link in enumerate(urlComments):
            if i is not 0:
                comment += ', '
            comment += link

        comment += ')'

        #----- JAPANESE TITLE -----#
        if (isExpanded):
            if jTitle is not None:
                comment += '\n\n'
                
                splitJTitle = jTitle.split()
                for i, word in enumerate(splitJTitle):
                    if not (i == 0):
                        comment += ' '
                    comment += '^^' + word

        #----- INFO LINE -----#
        
        if (isExpanded):
            comment += '\n\n^('

            if cType:
                if cType == 'Novel':
                    cType = 'Light Novel'
                    
                comment += '**' + cType + '** | '

            comment += '**Status:** ' + status

            if (cType != 'Light Novel'):
                if str(volumes) is not 'Unknown':
                    comment += ' | **Volumes:** ' + str(volumes)
                if str(chapters) is not 'Unknown':
                    comment += ' | **Chapters:** ' + str(chapters)
            else:
                if str(volumes) is not 'Unknown':
                    comment += ' | **Volumes:** ' + str(volumes)

            if genres:
                comment += ' | **Genres:** '
        else:
            comment += '\n\n^('

            if cType:
                if cType == 'Novel':
                    cType = 'Light Novel'
                    
                comment += cType + ' | '

            comment += 'Status: ' + status

            if (cType != 'Light Novel'):
                if str(volumes) is not 'Unknown':
                    comment += ' | Volumes: ' + str(volumes)
                if str(chapters) is not 'Unknown':
                    comment += ' | Chapters: ' + str(chapters)
            else:
                if str(volumes) is not 'Unknown':
                    comment += ' | Volumes: ' + str(volumes)

            if genres:
                comment += ' | Genres: '

        if genres:
            for i, genre in enumerate(genres):
                if i is not 0:
                    comment += ', '
                comment += genre
            
        if (isExpanded) and (stats is not None):
            comment += '  \n**Stats:** ' + str(stats['total']) + ' requests across ' + str(stats['uniqueSubreddits']) + ' subreddit(s)^) ^- ^' + str(round(stats['totalAsPercentage'],3)) + '% ^of ^all ^requests'
        else:
            comment += ')'

        #----- DESCRIPTION -----#
        if (isExpanded):
            comment += '\n\n' + cleanupDescription(desc)

        #----- END -----#
        receipt = '(M) Request successful: ' + title + ' - '
        if malURL is not None:
            receipt += 'MAL '
        if ap is not None:
            receipt += 'AP '
        if ani is not None:
            receipt += 'AL '
        if muURL is not None:
            receipt += 'MU '
        print(receipt)

        dictToReturn = {}
        dictToReturn['title'] = title
        dictToReturn['comment'] = comment
        
        return dictToReturn
    except:
        #traceback.print_exc()
        return None

#Builds a manga comment from MAL/Anilist/MangaUpdates data
def buildLightNovelComment(isExpanded, mal, ani, nu, lndb):
    try:
        comment = ''

        title = None
        jTitle = None

        cType = None

        malURL = None
        aniURL = None
        nuURL = nu
        lndbURL = lndb

        status = None
        chapters = None
        volumes = None
        genres = []
        
        desc = None

        if not (mal is None):
            title = mal['title']
            malURL = 'http://myanimelist.net/manga/' + str(mal['id'])
            desc = mal['synopsis']
            status = mal['status']

            cType = mal['type']

            try:
                if (int(mal['chapters']) == 0):
                    chapters = 'Unknown'
                else:
                    chapters = mal['chapters']
            except:
                chapters = 'Unknown'

            try:
                if (int(mal['volumes']) == 0):
                    volumes = 'Unknown'
                else:
                    volumes = mal['volumes']
            except:
                volumes = 'Unknown'

        if ani is not None:
            if title is None:
                title = ani['title_english']
            aniURL = 'http://anilist.co/manga/' + str(ani['id'])
            desc = ani['description']

            try:
                status = ani['publishing_status'].title()
            except:
                pass

            cType = ani['type']

            try:
                if ani['title_japanese'] is not None:
                    jTitle = ani['title_japanese']

                if ani['total_chapters'] is not None:
                    if ani['total_chapters'] == 0:
                        chapters = 'Unknown'
                    else:
                        chapters = ani['total_chapters']
                else:
                    volumes = 'Unknown'

                if ani['total_volumes'] is not None:
                    if ani['total_volumes'] == 0:
                        volumes = 'Unknown'
                    else:
                        volumes = ani['total_volumes']
                else:
                    volumes = 'Unknown'

                if ani['genres'] is not None:
                    genres = ani['genres']

            except Exception as e:
                print(e)

        stats = DatabaseHandler.getRequestStats(title,'LN')
        
        #---------- BUILDING THE COMMENT ----------#
                
        #----- TITLE -----#
        comment += '**' + title.strip() + '** - ('

        #----- LINKS -----#
        urlComments = []
        
        try:
        	mal_english = mal['english']
        except:
        	pass
        
        if malURL and mal_english:
            urlComments.append('[MAL](' + sanitise_url_for_markdown(malURL) + ' "' + mal_english + '")')
        elif malURL:
        	urlComments.append('[MAL](' + sanitise_url_for_markdown(malURL) + ')')
        	
        if aniURL is not None:
            urlComments.append('[AL](' + sanitise_url_for_markdown(aniURL) + ')')
        if nuURL is not None:
            urlComments.append('[NU](' + sanitise_url_for_markdown(nuURL) + ')')
        if lndbURL is not None:
            urlComments.append('[LNDB](' + sanitise_url_for_markdown(lndbURL) + ')')

        for i, link in enumerate(urlComments):
            if i is not 0:
                comment += ', '
            comment += link

        comment += ')'

        #----- JAPANESE TITLE -----#
        if (isExpanded):
            if jTitle is not None:
                comment += '\n\n'
                
                splitJTitle = jTitle.split()
                for i, word in enumerate(splitJTitle):
                    if not (i == 0):
                        comment += ' '
                    comment += '^^' + word

        #----- INFO LINE -----#
        
        if (isExpanded):
            comment += '\n\n^('

            if cType:
                if cType == 'Novel':
                    cType = 'Light Novel'
                    
                comment += '**' + cType + '** | '

            comment += '**Status:** ' + status

            if (cType != 'Light Novel'):
                if str(volumes) is not 'Unknown':
                    comment += ' | **Volumes:** ' + str(volumes)
                if str(chapters) is not 'Unknown':
                    comment += ' | **Chapters:** ' + str(chapters)
            else:
                if str(volumes) is not 'Unknown':
                    comment += ' | **Volumes:** ' + str(volumes)

            if genres:
                comment += ' | **Genres:** '
        else:
            comment += '\n\n^('

            if cType:
                if cType == 'Novel':
                    cType = 'Light Novel'
                    
                comment += cType + ' | '

            comment += 'Status: ' + status

            if (cType != 'Light Novel'):
                if str(volumes) is not 'Unknown':
                    comment += ' | Volumes: ' + str(volumes)
                if str(chapters) is not 'Unknown':
                    comment += ' | Chapters: ' + str(chapters)
            else:
                if str(volumes) is not 'Unknown':
                    comment += ' | Volumes: ' + str(volumes)

            if genres:
                comment += ' | Genres: '

        if genres:
            for i, genre in enumerate(genres):
                if i is not 0:
                    comment += ', '
                comment += genre
            
        if (isExpanded) and (stats is not None):
            comment += '  \n**Stats:** ' + str(stats['total']) + ' requests across ' + str(stats['uniqueSubreddits']) + ' subreddit(s)^) ^- ^' + str(round(stats['totalAsPercentage'],3)) + '% ^of ^all ^requests'
        else:
            comment += ')'

        #----- DESCRIPTION -----#
        if (isExpanded):
            comment += '\n\n' + cleanupDescription(desc)

        #----- END -----#
        receipt = '(LN) Request successful: ' + title + ' - '
        if malURL is not None:
            receipt += 'MAL '
        if ani is not None:
            receipt += 'AL '
        if nuURL is not None:
            receipt += 'MU '
        if lndbURL is not None:
            receipt += 'LNDB '
        print(receipt)

        dictToReturn = {}
        dictToReturn['title'] = title
        dictToReturn['comment'] = comment
        
        return dictToReturn
    except:
        traceback.print_exc()
        return None

def sanitise_url_for_markdown(url):
	return url.replace('(', '\(').replace(')', '\)')

#Builds a stats comment
def buildStatsComment(subreddit=None, username=None):
    try:
        statComment = ''
        receipt = '(S) Request successful: Stats'
        
        if username:
            userStats = DatabaseHandler.getUserStats(username)
            
            if userStats:
                statComment += 'Some stats on /u/' + username + ':\n\n'
                statComment += '- **' + str(userStats['totalUserComments']) + '** total comments searched (' + str(round(userStats['totalUserCommentsAsPercentage'], 3)) + '% of all comments)\n'
                statComment += '- **' + str(userStats['totalUserRequests']) + '** requests made (' + str(round(userStats['totalUserRequestsAsPercentage'], 3)) + '% of all requests and #' + str(userStats['overallRequestRank']) + ' overall)\n'
                statComment += '- **' + str(userStats['uniqueRequests']) + '** unique anime/manga requested\n'
                statComment += '- **/r/' + str(userStats['favouriteSubreddit']) + '** is their favourite subreddit with ' + str(userStats['favouriteSubredditCount']) + ' requests (' + str(round(userStats['favouriteSubredditCountAsPercentage'], 3)) + '% of the subreddit\'s requests)\n'
                statComment += '\n'
                statComment += 'Their most frequently requested anime/manga overall are:\n\n'
                
                for i, request in enumerate(userStats['topRequests']):
                    statComment += str(i + 1) + '. **' + str(request[0]) + '** (' + str(request[1]) + ' - ' + str(request[2]) + ' requests)  \n'
            else:
                statComment += '/u/' + str(username) + ' hasn\'t used Roboragi yet.'
                
            receipt += ' - /u/' + username
        elif subreddit:
            subreddit = str(subreddit)
            subredditStats = DatabaseHandler.getSubredditStats(subreddit.lower())
            
            if subredditStats:
                statComment += '**/r/' + subreddit +' Stats**\n\n'
                
                statComment += 'I\'ve searched through ' + str(subredditStats['totalComments'])
                statComment += ' unique comments on /r/' + subreddit
                statComment += ' and fulfilled a total of ' + str(subredditStats['total']) + ' requests, '
                statComment += 'representing ' + str(round(subredditStats['totalAsPercentage'], 2)) + '% of all requests. '
                statComment += 'A total of ' + str(subredditStats['uniqueNames']) + ' unique anime/manga have been requested here, '
                statComment += 'with a mean value of ' + str(round(subredditStats['meanValuePerRequest'], 3)) + ' requests/show'
                statComment += ' and a standard deviation of ' + str(round(subredditStats['standardDeviation'], 3)) + '.'

                statComment += '\n\n'

                statComment += 'The most frequently requested anime/manga on this subreddit are:\n\n'

                for i, request in enumerate(subredditStats['topRequests']):
                    statComment += str(i + 1) + '. **' + str(request[0]) + '** (' + str(request[1]) + ' - ' + str(request[2]) + ' requests)\n'

                statComment += '\n'

                statComment += 'The most frequent requesters on this subreddit are:\n\n'
                for i, requester in enumerate(subredditStats['topRequesters']):
                    statComment += str(i + 1) + '. /u/' + str(requester[0]) + ' (' + str(requester[1]) + ' requests)\n'
                
            else:
                statComment += 'There have been no requests on /r/' + str(subreddit) + ' yet.'
               
            receipt += ' - /r/' + subreddit
        else:
            basicStats = DatabaseHandler.getBasicStats()
            
            #The overall stats section
            statComment += '**Overall Stats**\n\n'

            statComment += 'I\'ve searched through ' + str(basicStats['totalComments'])
            statComment += ' unique comments and fulfilled a total of ' + str(basicStats['total'])
            statComment += ' requests across ' + str(basicStats['uniqueSubreddits']) + ' unique subreddit(s). '
            statComment += 'A total of ' + str(basicStats['uniqueNames'])
            statComment += ' unique anime/manga have been requested, with a mean value of ' + str(round(basicStats['meanValuePerRequest'],3))
            statComment += ' requests/show and a standard deviation of ' + str(round(basicStats['standardDeviation'], 3)) + '.'

            statComment += '\n\n'

            statComment += 'The most frequently requested anime/manga overall are:\n\n'

            for i, request in enumerate(basicStats['topRequests']):
                statComment += str(i + 1) + '. **' + str(request[0]) + '** (' + str(request[1]) + ' - ' + str(request[2]) + ' requests)\n'

            statComment += '\n'

            statComment += 'The most frequent requesters overall are:  \n'
            for i, requester in enumerate(basicStats['topRequesters']):
                statComment += str(i + 1) + '. /u/' + str(requester[0]) + ' (' + str(requester[1]) + ' requests)  \n'
                
            receipt += ' - Basic'
            
        print(receipt)
        
        return statComment
    except:
        traceback.print_exc()
        return None

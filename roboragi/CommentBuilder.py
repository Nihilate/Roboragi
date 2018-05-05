'''
CommentBuilder.py
Takes the data given to it by search and formats it into a comment
'''

import re
from os import linesep
import traceback
import DatabaseHandler
import pprint
import datetime

#Removes the (Source: MAL) or (Written by X) bits from the decriptions in the databases
def cleanupDescription(desc):    
    for match in re.finditer("([\[\<\(](.*)[\]\>\)])", desc, re.S):
        if 'ource' in match.group(1).lower():
            desc = desc.replace(match.group(1), '')
        if 'MAL' in match.group(1):
            desc = desc.replace(match.group(1), '')
        if '[From' in match.group(1):
            desc = desc.replace(match.group(1), '')
        if 'taken from' in match.group(1):
            desc = desc.replace(match.group(1), '')

    for match in re.finditer("([\<](.*?)[\>])", desc, re.S):
        if 'br' in match.group(1).lower():
            desc = desc.replace(match.group(1), '')
        if 'i' == match.group(1).lower():
            desc = desc.replace(match.group(1), '')
        if 'b' == match.group(1).lower():
            desc = desc.replace(match.group(1), '')
        
    reply = ''
    for i, line in enumerate(linesep.join([s for s in desc.splitlines() if s]).splitlines()):
        if i is not 0:
            reply += '\n'
        reply += '>' + line + '\n'
    return reply

#Builds an anime comment from MAL/HB/Anilist data
def buildAnimeComment(isExpanded, mal, ani, ap, anidb, kit):
    try:
        comment = ''

        title = None
        jTitle = None

        cType = None

        malURL = None
        aniURL = None
        apURL = ap
        anidbURL = anidb

        status = None
        episodes = None
        genres = []

        countdown = None
        nextEpisode = None
        
        desc = None

        release_year = None

        if ani:
            aniURL = 'http://anilist.co/anime/' + str(ani['id'])

            title = ani['title_romaji'] if 'title_romaji' in ani else ani['title_english']
            desc = ani['description'] if 'description' in ani else None
            status = ani['airing_status'].title() if 'airing_status' in ani else None
            cType = ani['type'] if 'type' in ani else None

            jTitle = ani['title_japanese'] if 'title_japanese' in ani else None
            genres = ani['genres'] if 'genres' in ani else None

            try:
                year_str = str(ani['start_date_fuzzy']) if 'start_date_fuzzy' in ani else None
                if year_str:
                    release_year = year_str[:4]
            except:
                pass

            episodes = ani['total_episodes'] if 'total_episodes' in ani else None
            if episodes == 0:
                episodes = None

            if ani['airing']:
                countdown = ani['airing']['countdown']
                nextEpisode = ani['airing']['next_episode']

        if kit:
            kitURL = kit['url']

            if not title:
                title = kit['title_romaji'] if 'title_romaji' in kit else kit['title_english']
            if not desc:
                desc = kit['description'] if 'description' in kit else None
            if not cType:
                cType = kit['type'].title() if 'type' in kit else None

            try:
                year_str = str(kit['startDate']) if 'startDate' in kit else None
                if year_str:
                    release_year = year_str[:4]
            except:
                pass

            if not episodes:
                episodes = kit['episode_count'] if 'episode_count' in kit else None
                if episodes == 0:
                    episodes = None

        if mal:
            malURL = 'http://myanimelist.net/anime/' + str(mal['id'])

            if not title:
                title = mal['title'] if 'title' in mal else mal['english']
            if not desc:
                desc = mal['synopsis'] if 'synopsis' in mal else None
            if not status:
                status = mal['status'] if 'status' in mal else None
            if not cType:
                cType = mal['type'] if 'type' in mal else None

        stats = DatabaseHandler.getRequestStats(title, 'Anime')

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
        if kit is not None:
            urlComments.append('[KIT](' + sanitise_url_for_markdown(kitURL) + ')')
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

            if release_year:
                 comment += '**' + release_year + '** | '
            
            comment += '**Status:** ' + status

            if cType != 'Movie' and episodes:
                comment += ' | **Episodes:** ' + str(episodes)
        else:
            comment += '\n\n^('

            if cType:
                comment += cType + ' | '

            comment += 'Status: ' + status

            if cType != 'Movie' and episodes:
                comment += ' | Episodes: ' + str(episodes)

        if genres:
            if (isExpanded):
                comment += ' | **Genres:** '
            else:
                comment += ' | Genres: '

            for i, genre in enumerate(genres):
                if i is not 0:
                    comment += ', '
                comment += genre

        comment += ')'
            
        if (isExpanded) and (stats is not None):
            comment += '  \n^(**Stats:** ' + str(stats['total']) + ' requests across ' + str(stats['uniqueSubreddits']) + ' subreddits - ' + str(round(stats['totalAsPercentage'],3)) + '% of all requests)'


        #----- EPISODE COUNTDOWN -----#
        if (countdown is not None) and (nextEpisode is not None):
            current_utc_time = datetime.datetime.utcnow()
            air_time_in_utc = current_utc_time + datetime.timedelta(0,countdown)
            formatted_time = air_time_in_utc.strftime('%Y%m%dT%H%M')

            #countdown is given to us in seconds
            days, countdown = divmod(countdown, 24*60*60)
            hours, countdown = divmod(countdown, 60*60)
            minutes, countdown = divmod(countdown, 60)

            comment += '\n\n^[Episode&#32;' + str(nextEpisode) + '&#32;airs&#32;in&#32;' + str(days) + '&#32;days,&#32;' + str(hours) + '&#32;hours,&#32;' + str(minutes) + '&#32;minutes](https://www.timeanddate.com/worldclock/fixedtime.html?iso='+ formatted_time +')'

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
        if kit is not None:
            receipt += 'KIT '
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
def buildMangaComment(isExpanded, mal, ani, mu, ap, kit):
    try:
        comment = ''

        title = None
        jTitle = None

        cType = None

        malURL = None
        aniURL = None
        muURL = mu
        apURL = ap
        kitURL = None

        status = None
        chapters = None
        volumes = None
        genres = []
        
        desc = None

        if ani:
            aniURL = 'http://anilist.co/manga/' + str(ani['id'])

            title = ani['title_romaji'] if 'title_romaji' in ani else ani['title_english']
            desc = ani['description'] if 'description' in ani else None
            status = ani['publishing_status'].title() if 'publishing_status' in ani else None
            cType = ani['type'] if 'type' in ani else None

            jTitle = ani['title_japanese'] if 'title_japanese' in ani else None
            genres = ani['genres'] if 'genres' in ani else None

            chapters = ani['total_chapters'] if 'total_chapters' in ani else None
            if chapters == 0:
                chapters = None
            volumes = ani['total_volumes'] if 'total_volumes' in ani else None
            if volumes == 0:
                volumes = None

        if kit:
            kitURL = kit['url']

            if not title:
                title = kit['title_romaji'] if 'title_romaji' in kit else kit['title_english']
            if not desc:
                desc = kit['description'] if 'description' in kit else None
            if not cType:
                cType = kit['type'].title() if 'type' in kit else None

            if not chapters:
                chapters = kit['chapter_count'] if 'chapter_count' in kit else None
                if chapters == 0:
                    chapters = None
            if not volumes:
                volumes = kit['volume_count'] if 'volume_count' in kit else None
                if volumes == 0:
                    volumes = None

        if mal:
            malURL = 'http://myanimelist.net/manga/' + str(mal['id'])

            if not title:
                title = mal['title'] if 'title' in mal else mal['english']
            if not desc:
                desc = mal['synopsis'] if 'synopsis' in mal else None
            if not status:
                status = mal['status'] if 'status' in mal else None
            if not cType:
                cType = mal['type'] if 'type' in mal else None

            if not chapters:
                try:
                    if (int(mal['chapters']) == 0):
                        chapters = 'Unknown'
                    else:
                        chapters = mal['chapters']
                except:
                    chapters = None

            if not volumes:
                try:
                    if (int(mal['volumes']) == 0):
                        volumes = 'Unknown'
                    else:
                        volumes = mal['volumes']
                except:
                    volumes = 'Unknown'


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
        if kitURL is not None:
            urlComments.append('[KIT](' + sanitise_url_for_markdown(kitURL) + ')')
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
                if volumes and str(volumes) is not 'Unknown':
                    comment += ' | **Volumes:** ' + str(volumes)
                if chapters and str(chapters) is not 'Unknown':
                    comment += ' | **Chapters:** ' + str(chapters)
            else:
                if volumes and str(volumes) is not 'Unknown':
                    comment += ' | **Volumes:** ' + str(volumes)
        else:
            comment += '\n\n^('

            if cType:
                if cType == 'Novel':
                    cType = 'Light Novel'
                    
                comment += cType + ' | '

            comment += 'Status: ' + status

            if (cType != 'Light Novel'):
                if volumes and str(volumes) is not 'Unknown':
                    comment += ' | Volumes: ' + str(volumes)
                if chapters and str(chapters) is not 'Unknown':
                    comment += ' | Chapters: ' + str(chapters)
            else:
                if volumes and str(volumes) is not 'Unknown':
                    comment += ' | Volumes: ' + str(volumes)

        if genres:
            if (isExpanded):
                comment += ' | **Genres:** '
            else:
                comment += ' | Genres: '

            for i, genre in enumerate(genres):
                if i is not 0:
                    comment += ', '
                comment += genre

        comment += ')'
            
        if (isExpanded) and (stats is not None):
            comment += '  \n^(**Stats:** ' + str(stats['total']) + ' requests across ' + str(stats['uniqueSubreddits']) + ' subreddits - ' + str(round(stats['totalAsPercentage'],3)) + '% of all requests)'
            

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
        if kit is not None:
            receipt += 'KIT '
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
def buildLightNovelComment(isExpanded, mal, ani, nu, lndb, kit):
    try:
        comment = ''

        title = None
        jTitle = None

        cType = None

        malURL = None
        aniURL = None
        nuURL = nu
        lndbURL = lndb
        kitURL = None

        status = None
        chapters = None
        volumes = None
        genres = []
        
        desc = None

        if ani:
            aniURL = 'http://anilist.co/manga/' + str(ani['id'])

            title = ani['title_romaji'] if 'title_romaji' in ani else ani['title_english']
            desc = ani['description'] if 'description' in ani else None
            status = ani['publishing_status'].title() if 'publishing_status' in ani and ani['publishing_status'] else None
            cType = ani['type'] if 'type' in ani else None

            jTitle = ani['title_japanese'] if 'title_japanese' in ani else None
            genres = ani['genres'] if 'genres' in ani else None

            chapters = ani['total_chapters'] if 'total_chapters' in ani else None
            if chapters == 0:
                chapters = None
            volumes = ani['total_volumes'] if 'total_volumes' in ani else None
            if volumes == 0:
                volumes = None

        if kit:
            kitURL = kit['url']

            if not title:
                title = kit['title_romaji'] if 'title_romaji' in kit else kit['title_english']
            if not desc:
                desc = kit['description'] if 'description' in kit else None
            if not cType:
                cType = kit['type'].title() if 'type' in kit else None

            if not chapters:
                chapters = kit['chapter_count'] if 'chapter_count' in kit else None
                if chapters == 0:
                    chapters = None
            if not volumes:
                volumes = kit['volume_count'] if 'volume_count' in kit else None
                if volumes == 0:
                    volumes = None

        if mal:
            malURL = 'http://myanimelist.net/manga/' + str(mal['id'])

            if not title:
                title = mal['title'] if 'title' in mal else mal['english']
            if not desc:
                desc = mal['synopsis'] if 'synopsis' in mal else None
            if not status:
                status = mal['status'] if 'status' in mal else None
            if not cType:
                cType = mal['type'] if 'type' in mal else None

            if not chapters:
                try:
                    if (int(mal['chapters']) == 0):
                        chapters = 'Unknown'
                    else:
                        chapters = mal['chapters']
                except:
                    chapters = None

            if not volumes:
                try:
                    if (int(mal['volumes']) == 0):
                        volumes = 'Unknown'
                    else:
                        volumes = mal['volumes']
                except:
                    volumes = 'Unknown'

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
        if kitURL is not None:
            urlComments.append('[KIT](' + sanitise_url_for_markdown(kitURL) + ')')
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
                if volumes and str(volumes) is not 'Unknown':
                    comment += ' | **Volumes:** ' + str(volumes)
                if chapters and str(chapters) is not 'Unknown':
                    comment += ' | **Chapters:** ' + str(chapters)
            else:
                if volumes and str(volumes) is not 'Unknown':
                    comment += ' | **Volumes:** ' + str(volumes)
        else:
            comment += '\n\n^('

            if cType:
                if cType == 'Novel':
                    cType = 'Light Novel'
                    
                comment += cType + ' | '

            comment += 'Status: ' + status

            if (cType != 'Light Novel'):
                if volumes and str(volumes) is not 'Unknown':
                    comment += ' | Volumes: ' + str(volumes)
                if chapters and str(chapters) is not 'Unknown':
                    comment += ' | Chapters: ' + str(chapters)
            else:
                if volumes and str(volumes) is not 'Unknown':
                    comment += ' | Volumes: ' + str(volumes)

        if genres:
            if (isExpanded):
                comment += ' | **Genres:** '
            else:
                comment += ' | Genres: '

            for i, genre in enumerate(genres):
                if i is not 0:
                    comment += ', '
                comment += genre

        comment += ')'
        
        if (isExpanded) and (stats is not None):
            comment += '  \n^(**Stats:** ' + str(stats['total']) + ' requests across ' + str(stats['uniqueSubreddits']) + ' subreddits - ' + str(round(stats['totalAsPercentage'],3)) + '% of all requests)'

        #----- DESCRIPTION -----#
        if (isExpanded):
            comment += '\n\n' + cleanupDescription(desc)

        #----- END -----#
        receipt = '(LN) Request successful: ' + title + ' - '
        if malURL is not None:
            receipt += 'MAL '
        if ani is not None:
            receipt += 'AL '
        if kit is not None:
            receipt += 'KIT '
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
        #traceback.print_exc()
        return None

#Builds an anime comment from MAL/HB/Anilist data
def buildVisualNovelComment(isExpanded, vndb):
    try:
        comment = ''

        urls = []
        if vndb['url']:
            urls.append('[VNDB]({0})'.format(vndb['url']))
        if vndb['wikipedia_url']:
            urls.append('[Wiki]({0})'.format(vndb['wikipedia_url']))

        formatted_links = ''
        for i, link in enumerate(urls):
            if i is not 0:
                formatted_links += ', '
            formatted_links += link

        if not isExpanded:
            template = '**{title}** - {links}\n\n^({type}{released}{length})'
            formatted = template.format(title=vndb['title'],
                links='({})'.format(formatted_links),
                type='VN',
                released = ' | Released: ' + vndb['release_year'] if vndb['release_year'] else '',
                length = ' | Length: ' + vndb['length'] if vndb['length'] else '')

            comment = formatted
        else:
            stats = DatabaseHandler.getRequestStats(vndb['title'],'VN')
            if stats:
                formatted_stats = '**Stats:** ' + str(stats['total']) + ' requests across ' + str(stats['uniqueSubreddits']) + ' subreddit(s)^) ^- ^' + str(round(stats['totalAsPercentage'],3)) + '% ^of ^all ^requests'
            else:
                formatted_stats = None

            template = '**{title}** - {links}\n\n^({type}{released}{length}){stats}\n\n{desc}'
            formatted = template.format(title=vndb['title'],
                links='({})'.format(formatted_links),
                type='**VN**',
                released = ' | **Released:** ' + vndb['release_year'] if vndb['release_year'] else '',
                length = ' | **Length:** ' + vndb['length'] if vndb['length'] else '',
                stats = '  \n^(' + formatted_stats if formatted_stats else '',
                desc=cleanupDescription(vndb['description']))

            comment = formatted

        #----- END -----#
        receipt = '(VN) Request successful: ' + vndb['title'] + ' - '
        if vndb:
            receipt += 'VNDB'
        print(receipt)

        #We return the title/comment separately so we can track if multiples of the same comment have been requests (e.g. {Nisekoi}{Nisekoi}{Nisekoi})
        dictToReturn = {}
        dictToReturn['title'] = vndb['title']
        dictToReturn['comment'] = comment

        return dictToReturn
    except:
        traceback.print_exc()
        return None

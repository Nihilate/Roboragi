"""
Anilist.py
Handles all of the connections to Anilist.
"""

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

import difflib
import traceback

import requests

req = requests.Session()

uri = 'https://graphql.anilist.co'

search_query = '''query ($search: String, $type: MediaType) {
  Page {
    media(search: $search, type: $type) {
      id
      idMal
      title {
        romaji
        english
        native
      }
      type
      status
      format
      episodes
      chapters
      volumes
      description
      startDate {
          year
          month
          day
      }
      endDate {
          year
          month
          day
      }
      genres
      synonyms
      nextAiringEpisode {
        airingAt
        timeUntilAiring
        episode
      }
    }
  }
}'''

id_query = '''query ($id: Int) {
  Page {
    media(id: $id) {
      id
      idMal
      title {
        romaji
        english
        native
      }
      type
      status
      format
      episodes
      chapters
      volumes
      description
      startDate {
          year
          month
          day
      }
      endDate {
          year
          month
          day
      }
      genres
      synonyms
      nextAiringEpisode {
        airingAt
        timeUntilAiring
        episode
      }
    }
  }
}'''


def morph_to_v1(raw):
    raw_results = raw["data"]["Page"]["media"]
    morphed_results = []

    for raw_result in raw_results:
        try:
            airing = dict(
                countdown=raw_result["nextAiringEpisode"]["timeUntilAiring"],
                next_episode=raw_result["nextAiringEpisode"]["episode"],
            ) if raw_result["nextAiringEpisode"] else None
            morphed = dict(
                id=raw_result["id"],
                id_mal=raw_result["idMal"],
                title_romaji=raw_result["title"]["romaji"],
                title_english=raw_result["title"]["english"],
                title_japanese=raw_result["title"]["native"],
                type=map_media_format(raw_result["format"]),
                start_date_fuzzy=raw_result["startDate"]["year"],
                end_date_fuzzy=raw_result["endDate"]["year"],
                description=raw_result["description"],
                genres=raw_result["genres"],
                synonyms=raw_result["synonyms"],
                total_episodes=raw_result["episodes"],
                total_chapters=raw_result["chapters"],
                total_volumes=raw_result["volumes"],
                airing_status=map_media_status(raw_result["status"]),
                publishing_status=map_media_status(raw_result["status"]),
                airing=airing,
            )

            morphed_results.append(morphed)
        except Exception as e:
            print(e)

    return morphed_results


def map_media_format(media_format):
    mapped_formats = {
        'TV': 'TV',
        'TV_SHORT': 'TV Short',
        'MOVIE': 'Movie',
        'SPECIAL': 'Special',
        'OVA': 'OVA',
        'ONA': 'ONA',
        'MUSIC': 'Music',
        'MANGA': 'Manga',
        'NOVEL': 'Novel',
        'ONE_SHOT': 'One Shot',
    }
    return mapped_formats[media_format]


def map_media_status(media_status):
    mapped_status = {
        'FINISHED': 'Finished',
        'RELEASING': 'Releasing',
        'NOT_YET_RELEASED': 'Not Yet Released',
        'CANCELLED': 'Special'
    }
    return mapped_status[media_status]


def getSynonyms(request):
    synonyms = []
    synonyms.extend(request.get('synonyms'))
    return synonyms


def getTitles(request):
    titles = []
    titles.append(request.get('title_english'))
    titles.append(request.get('title_romaji'))
    return titles


def detailsBySearch(searchText, mediaType):
    try:
        search_variables = {
            'search': searchText,
            'type': mediaType
        }

        payload = {'query': search_query, 'variables': search_variables}
        request = req.post(uri, json=payload)
        req.close()

        return morph_to_v1(request.json())

    except Exception:
        traceback.print_exc()
        req.close()
        return None


def detailsById(idToFind):
    try:
        id_variables = {
            'id': int(idToFind)
        }

        payload = {'query': id_query, 'variables': id_variables}
        request = req.post(uri, json=payload)
        req.close()

        return morph_to_v1(request.json())[0]

    except Exception:
        traceback.print_exc()
        req.close()
        return None


def getAnimeDetails(searchText):
    """
    Returns the closest anime (as a Json-like object) it can find using the
    given searchtext
    """
    try:
        results = detailsBySearch(searchText, 'ANIME')

        # Of the given list of shows, we try to find the one we think is
        # closest to our search term
        closest_anime = getClosestAnime(searchText, results)

        if closest_anime:
            return closest_anime
        else:
            return None

    except Exception:
        traceback.print_exc()
        req.close()
        return None


def getAnimeDetailsById(animeID):
    """
    Returns the anime details based on an id
    """
    try:
        return detailsById(animeID)
    except Exception:
        return None


def getClosestAnime(searchText, animeList):
    """
    Given a list, it finds the closest anime series it can.
    """
    try:
        animeNameList = []
        animeNameListNoSyn = []

        # For each anime series, add all the titles/synonyms to an array and
        # do a fuzzy string search to find the one
        # closest to our search text.  We also fill out an array that doesn't
        # contain the synonyms. This is to protect
        # against shows with multiple adaptations and similar synonyms
        # (e.g. Haiyore Nyaruko-San)
        for anime in animeList:
            if 'title_english' in anime and anime['title_english']:
                animeNameList.append(anime['title_english'].lower())
                animeNameListNoSyn.append(anime['title_english'].lower())

            if 'title_romaji' in anime and anime['title_romaji']:
                animeNameList.append(anime['title_romaji'].lower())
                animeNameListNoSyn.append(anime['title_romaji'].lower())

            if 'synonyms' in anime and anime['synonyms']:
                for synonym in anime['synonyms']:
                    animeNameList.append(synonym.lower())

        try:
            matches = difflib.get_close_matches(
                word=searchText.lower(),
                possibilities=animeNameList,
                n=1,
                cutoff=0.95,
            )
            closestNameFromList = matches[0]
        except Exception:
            closestNameFromList = None

        if closestNameFromList:
            closestNameFromList = closestNameFromList.lower()
            for anime in animeList:
                title_english = (anime.get('title_english') or '').lower()
                title_romaji = (anime.get('title_romaji') or '').lower()
                if title_english == closestNameFromList:
                    return anime
                elif title_romaji == closestNameFromList:
                    return anime
                else:
                    for synonym in anime['synonyms']:
                        synonym = synonym.lower()
                        if (synonym == closestNameFromList) and (
                                synonym not in animeNameListNoSyn):
                            return anime

        return None
    except Exception:
        traceback.print_exc()
        return None


def getLightNovelDetails(searchText):
    return getMangaDetails(searchText, True)


def getMangaDetails(searchText, isLN=False):
    """
    Returns the closest manga series given a specific search term
    """
    try:
        results = detailsBySearch(searchText, 'MANGA')

        closestManga = getClosestManga(searchText, results, isLN)

        if closestManga:
            return closestManga
        else:
            return None

    except Exception:
        return None


def getMangaDetailsById(mangaId):
    """
    Returns the closest manga series given an id
    """
    try:
        return detailsById(mangaId)
    except Exception:
        return None


def getClosestManga(searchText, mangaList, isLN=False):
    """
    Used to determine the closest manga to a given search term in a list
    """
    try:
        mangaNameList = []

        for manga in mangaList:
            if isLN and 'novel' not in manga['type'].lower():
                mangaList.remove(manga)
            elif not isLN and 'novel' in manga['type'].lower():
                mangaList.remove(manga)

        for manga in mangaList:
            title_english = manga.get('title_english')
            title_romaji = manga.get('title_romaji')
            if title_english:
                mangaNameList.append(title_english.lower())
            if title_romaji:
                mangaNameList.append(title_romaji.lower())

            for synonym in manga['synonyms']:
                mangaNameList.append(synonym.lower())

        try:
            matches = difflib.get_close_matches(
                word=searchText.lower(),
                possibilities=mangaNameList,
                n=1,
                cutoff=0.90,
            )
            closestNameFromList = matches[0]
        except Exception:
            closestNameFromList = None

        if closestNameFromList:
            closestNameFromList = closestNameFromList.lower()
            for manga in mangaList:
                if not ('one shot' in manga['type'].lower()):
                    title_english = (manga.get('title_english') or '').lower()
                    title_romaji = (manga.get('title_romaji') or '').lower()
                    if title_english == closestNameFromList:
                        return manga
                    if title_romaji == closestNameFromList:
                        return manga

            for manga in mangaList:
                for synonym in manga['synonyms']:
                    if synonym.lower() == closestNameFromList:
                        return manga

        return None
    except Exception:
        traceback.print_exc()
        return None

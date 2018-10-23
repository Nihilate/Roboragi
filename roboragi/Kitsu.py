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

import requests

AUTH_URL = 'https://kitsu.io/api/oauth/'
BASE_URL = 'https://kitsu.io/api/edge/'
ANIME_SEARCH_FILTER = 'anime?filter[text]='
MANGA_SEARCH_FILTER = 'manga?filter[text]='
ANIME_GET_FILTER = 'anime?filter[slug]='
MANGA_GET_FILTER = 'manga?filter[slug]='

ENGLISH_LANGUAGE_CODES = ['en', 'en_us']
ROMAJI_LANGUAGE_CODES = ['en_jp']
JAPANESE_LANGUAGE_CODES = ['ja_jp']

session = requests.Session()
session.headers = {
    'Accept': 'application/vnd.api+json',
    'Content-Type': 'application/vnd.api+json'
}


def search(endpoint, search_term, parser, use_first_result=False):
    try:
        response = session.get(BASE_URL + endpoint + search_term, timeout=4)
        response.raise_for_status()

        results = parser(response.json()['data'])

        if not results:
            return None

        if use_first_result:
            return results[0]
        else:
            closest_result = get_closest(results, search_term)
            return closest_result
    except Exception:
        return None
    finally:
        session.close()


def get_closest(results, search_term):
    name_list = []

    for result in results:
        title_and_synonyms = get_titles(result) | get_synonyms(result)
        synonyms = [synonym.lower() for synonym in title_and_synonyms]
        if synonyms:
            name_list.extend(synonyms)

    matches = difflib.get_close_matches(
        word=search_term.lower(),
        possibilities=name_list,
        n=1,
        cutoff=0.90
    )
    closest_name_from_list = matches[0].lower()

    for result in results:
        if result['title_romaji']:
            if result['title_romaji'].lower() == closest_name_from_list:
                return result
        elif result['title_english']:
            if result['title_english'].lower() == closest_name_from_list:
                return result
        else:
            for synonym in result['synonyms']:
                if synonym.lower() == closest_name_from_list:
                    return result


def search_anime(search_term):
    return search(ANIME_SEARCH_FILTER, search_term, parse_anime)


def search_manga(search_term):
    return search(MANGA_SEARCH_FILTER, search_term, parse_manga)


def search_light_novel(search_term):
    return search(MANGA_SEARCH_FILTER, search_term, parse_light_novel)


def get_anime(search_term):
    try:
        return search(ANIME_GET_FILTER, search_term, parse_anime, True)
    except Exception:
        return None


def get_manga(search_term):
    try:
        return search(MANGA_GET_FILTER, search_term, parse_manga, True)
    except Exception:
        return None


def get_light_novel(search_term):
    try:
        return search(MANGA_GET_FILTER, search_term, parse_light_novel, True)
    except Exception:
        return None


def parse_anime(results):
    anime_list = []

    for entry in results:
        try:
            id_ = entry['id']
            slug = entry['attributes']['slug']
            url = f"https://kitsu.io/anime/{slug}"
            title_romaji = get_title_by_language_codes(
                titles=entry['attributes']['titles'],
                language_codes=ROMAJI_LANGUAGE_CODES
            )
            title_english = get_title_by_language_codes(
                titles=entry['attributes']['titles'],
                language_codes=ENGLISH_LANGUAGE_CODES
            )
            title_japanese = get_title_by_language_codes(
                titles=entry['attributes']['titles'],
                language_codes=JAPANESE_LANGUAGE_CODES
            )

            if entry['attributes']['abbreviatedTitles']:
                synonyms = set(entry['attributes']['abbreviatedTitles'])
            else:
                synonyms = set()

            if entry['attributes']['episodeCount']:
                episode_count = int(entry['attributes']['episodeCount'])
            else:
                episode_count = None

            type_ = entry['attributes']['showType']
            description = entry['attributes']['synopsis']
            nsfw = entry['attributes']['nsfw']

            anime = dict(
                id=id_,
                url=url,
                title_romaji=title_romaji,
                title_english=title_english,
                title_japanese=title_japanese,
                synonyms=synonyms,
                episode_count=episode_count,
                type=type_,
                description=description,
                nsfw=nsfw,
            )

            anime_list.append(anime)
        except AttributeError:
            pass

    return anime_list


def parse_manga(results):
    manga_list = []

    for entry in results:
        try:
            type_ = entry['attributes']['mangaType']
            # Avoid all the processsing below if the type is "novel".
            if type_.lower() == 'novel':
                continue

            id_ = entry['id']
            slug = entry['attributes']['slug']
            url = f"https://kitsu.io/manga/{slug}"
            title_romaji = get_title_by_language_codes(
                titles=entry['attributes']['titles'],
                language_codes=ROMAJI_LANGUAGE_CODES
            )
            title_english = get_title_by_language_codes(
                titles=entry['attributes']['titles'],
                language_codes=ENGLISH_LANGUAGE_CODES
            )

            if entry['attributes']['abbreviatedTitles']:
                synonyms = set(entry['attributes']['abbreviatedTitles'])
            else:
                synonyms = set()

            if entry['attributes']['volumeCount']:
                volume_count = int(entry['attributes']['volumeCount'])
            else:
                volume_count = None

            if entry['attributes']['chapterCount']:
                chapter_count = int(entry['attributes']['chapterCount'])
            else:
                chapter_count = None

            description = entry['attributes']['synopsis']

            manga = dict(
                id=id_,
                url=url,
                title_romaji=title_romaji,
                title_english=title_english,
                synonyms=synonyms,
                volume_count=volume_count,
                chapter_count=chapter_count,
                type=entry['attributes']['mangaType'],
                description=description,
            )

            manga_list.append(manga)
        except AttributeError:
            pass

    return manga_list


def parse_light_novel(results):
    ln_list = []

    for entry in results:
        try:
            type_ = entry['attributes']['mangaType']
            # Avoid all the processsing below if the type is not "novel".
            if type_.lower() != 'novel':
                continue

            id_ = entry['id']
            slug = entry['attributes']['slug']
            url = f"https://kitsu.io/manga/{slug}"
            title_romaji = get_title_by_language_codes(
                titles=entry['attributes']['titles'],
                language_codes=ROMAJI_LANGUAGE_CODES
            )
            title_english = get_title_by_language_codes(
                titles=entry['attributes']['titles'],
                language_codes=ENGLISH_LANGUAGE_CODES
            )

            if entry['attributes']['abbreviatedTitles']:
                synonyms = set(entry['attributes']['abbreviatedTitles'])
            else:
                synonyms = set()

            if entry['attributes']['volumeCount']:
                volume_count = int(entry['attributes']['volumeCount'])
            else:
                volume_count = None

            if entry['attributes']['chapterCount']:
                chapter_count = int(entry['attributes']['chapterCount'])
            else:
                chapter_count = None

            description = entry['attributes']['synopsis']

            ln = dict(
                id=id_,
                url=url,
                title_romaji=title_romaji,
                title_english=title_english,
                synonyms=synonyms,
                volume_count=volume_count,
                chapter_count=chapter_count,
                type=type_,
                description=description,
            )

            ln_list.append(ln)
        except AttributeError:
            pass

    return ln_list


def get_synonyms(result):
    synonyms = set()
    synonyms.update(result['synonyms'])
    return synonyms


def get_titles(result):
    titles = set()
    titles.add(result['title_romaji']) if result['title_romaji'] else None
    titles.add(result['title_english']) if result['title_english'] else None
    return titles


def get_title_by_language_codes(titles, language_codes):
    for language_code in language_codes:
        if language_code in titles:
            return titles[language_code]
    return None

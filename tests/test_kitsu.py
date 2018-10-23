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

import pytest

from roboragi.Kitsu import (
    get_synonyms,
    get_titles,
    get_title_by_language_codes,
    ENGLISH_LANGUAGE_CODES,
    ROMAJI_LANGUAGE_CODES,
    JAPANESE_LANGUAGE_CODES
)

BRITISH_ENGLISH_TITLES = dict(en='British English Title')
AMERICAN_ENGLISH_TITLES = dict(en_us='American English Title')
ALL_ENGLISH_TITLES = dict(**BRITISH_ENGLISH_TITLES, **AMERICAN_ENGLISH_TITLES)

ROMAJI_TITLES = dict(en_jp='Rōmaji Title')
JAPANESE_TITLES = dict(ja_jp='日本のタイトル')

ALL_LANGUAGE_TITLES = dict(
    **ALL_ENGLISH_TITLES,
    **ROMAJI_TITLES,
    **JAPANESE_TITLES,
)


def test_get_synonyms_dedupes_synonyms():
    given = dict(synonyms=[
        'Samurai Champloo',
        'Samurai Champloo',
        'One Punch Man',
        'One Punch Man'
    ])
    expected = set(('Samurai Champloo', 'One Punch Man'))

    assert get_synonyms(result=given) == expected


def test_get_titles_dedupes_titles():
    given = dict(
        title_english='Samurai Champloo',
        title_romaji='Samurai Champloo',
    )
    expected = set(('Samurai Champloo',))

    assert get_titles(result=given) == expected


def test_get_titles_can_ignore_missing_english_titles():
    given = dict(
        title_english=None,
        title_romaji='Samurai Champloo'
    )
    expected = set(('Samurai Champloo',))

    assert get_titles(result=given) == expected


def test_get_titles_can_ignore_missing_romaji_titles():
    given = dict(
        title_english='Samurai Champloo',
        title_romaji=None,
    )
    expected = set(('Samurai Champloo',))

    assert get_titles(result=given) == expected


def test_get_titles_returns_empty_set_with_no_titles():
    given = dict(title_english=None, title_romaji=None)
    expected = set()

    assert get_titles(result=given) == expected


@pytest.mark.parametrize('language_codes,titles,expected', [
    (ENGLISH_LANGUAGE_CODES, BRITISH_ENGLISH_TITLES, BRITISH_ENGLISH_TITLES['en']),  # noqa: E501
    (ENGLISH_LANGUAGE_CODES, AMERICAN_ENGLISH_TITLES, AMERICAN_ENGLISH_TITLES['en_us']),  # noqa: E501
    (ROMAJI_LANGUAGE_CODES, ROMAJI_TITLES, ROMAJI_TITLES['en_jp']),
    (JAPANESE_LANGUAGE_CODES, JAPANESE_TITLES, JAPANESE_TITLES['ja_jp']),
])
def test_title_extraction_single_titles(language_codes, titles, expected):
    actual = get_title_by_language_codes(titles, language_codes)
    assert actual == expected


@pytest.mark.parametrize('language_codes,titles,expected', [
    (ENGLISH_LANGUAGE_CODES, ALL_LANGUAGE_TITLES, ALL_LANGUAGE_TITLES['en']),
    (ROMAJI_LANGUAGE_CODES, ALL_LANGUAGE_TITLES, ALL_LANGUAGE_TITLES['en_jp']),
    (JAPANESE_LANGUAGE_CODES, ALL_LANGUAGE_TITLES, ALL_LANGUAGE_TITLES['ja_jp']),  # noqa: E501
])
def test_title_extraction_multiple_titles(language_codes, titles, expected):
    actual = get_title_by_language_codes(titles, language_codes)
    assert actual == expected


@pytest.mark.parametrize('language_codes', [
    ENGLISH_LANGUAGE_CODES,
    ROMAJI_LANGUAGE_CODES,
    JAPANESE_LANGUAGE_CODES,
])
def test_title_extraction_no_titles(language_codes):
    assert get_title_by_language_codes({}, language_codes) is None


def test_title_extraction_prefers_british_over_american_english():
    expected = ALL_ENGLISH_TITLES['en']
    actual = get_title_by_language_codes(
        titles=ALL_ENGLISH_TITLES,
        language_codes=ENGLISH_LANGUAGE_CODES
    )
    assert actual == expected

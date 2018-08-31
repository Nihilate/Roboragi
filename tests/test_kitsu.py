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

from roboragi.Kitsu import get_title_by_language_codes, ENGLISH_LANGUAGE_CODES, ROMAJI_LANGUAGE_CODES, JAPANESE_LANGUAGE_CODES


@pytest.mark.parametrize('language_codes,titles,expected', [
    (ENGLISH_LANGUAGE_CODES, {'en': 'English'}, 'English'),
    (ENGLISH_LANGUAGE_CODES, {'en_us': 'American English'}, 'American English'),
    (ROMAJI_LANGUAGE_CODES, {'en_jp': 'Romaji'}, 'Romaji'),
    (JAPANESE_LANGUAGE_CODES, {'ja_jp': 'Japanese'}, 'Japanese'),
    (ENGLISH_LANGUAGE_CODES, {'en': 'English', 'en_us': 'American English'}, 'English'),
    (ENGLISH_LANGUAGE_CODES, {'en': 'English', 'en_us': 'American English', 'en_jp': 'Romaji', 'ja_jp': 'Japanese'}, 'English'),
    (ROMAJI_LANGUAGE_CODES, {'en': 'English', 'en_us': 'American English', 'en_jp': 'Romaji', 'ja_jp': 'Japanese'}, 'Romaji'),
    (JAPANESE_LANGUAGE_CODES, {'en': 'English', 'en_us': 'American English', 'en_jp': 'Romaji', 'ja_jp': 'Japanese'}, 'Japanese'),
    (ENGLISH_LANGUAGE_CODES, {}, None),
    (ROMAJI_LANGUAGE_CODES, {}, None),
    (JAPANESE_LANGUAGE_CODES, {}, None),
])
def test_title_extraction(language_codes, titles, expected):
    actual = get_title_by_language_codes(titles, language_codes)
    assert actual == expected


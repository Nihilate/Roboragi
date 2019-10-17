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

import re

from typing import Dict, Tuple, Pattern, ValuesView, Generator


def _patterns(
    tag_characters: Dict[str, Tuple[str, str]], expanded: bool = False
) -> Dict[str, Pattern[str]]:
    """ Generate compiled regexes from a set of tag characters. """
    n: int = 2 if expanded else 1
    template: str = r"(?<![\w\{left}])\{left}{{{n}}}(?!\{left})(\S(?:[^\{left}\{right}]*\S)?)(?<!\{right})\{right}{{{n}}}(?![\{right}\w])"  # noqa: E501
    return {
        name: re.compile(
            template.format(left=chars[0], right=chars[1], n=n)
        )  # noqa: E501
        for name, chars in tag_characters.items()
    }


def _all_patterns(
    patterns: ValuesView[Pattern[str]], flags: int = re.M
) -> Pattern[str]:
    """ Generate a single compiled regex from all the given patterns. """
    all_patterns: str = "|".join("(?:" + r.pattern + ")" for r in patterns)
    return re.compile(pattern=all_patterns, flags=flags)


USERNAME_PATTERN: Pattern[str] = re.compile(
    pattern=r"[uU]\/([A-Za-z0-9_-]+?)(>|}|$)", flags=re.S
)

SUBREDDIT_PATTERN: Pattern[str] = re.compile(
    pattern=r"[rR]\/([A-Za-z0-9_]+?)(>|}|$)", flags=re.S
)

TAG_CHARACTERS: Dict[str, Tuple[str, str]] = {
    "anime": ("{", "}"),
    "manga": ("<", ">"),
    "light_novel": ("]", "["),
    "visual_novel": ("|", "|"),
}
REGULAR_PATTERNS: Dict[str, Pattern[str]] = _patterns(TAG_CHARACTERS)
REGULAR_PATTERNS["all"] = _all_patterns(REGULAR_PATTERNS.values())
EXPANDED_PATTERNS: Dict[str, Pattern[str]] = _patterns(TAG_CHARACTERS, expanded=True)
EXPANDED_PATTERNS["all"] = _all_patterns(EXPANDED_PATTERNS.values())


def _find(string: str, pattern: Pattern[str]):
    for matches in pattern.finditer(string):
        for match in matches.groups():
            if match is not None:
                yield match


def find_requests(type: str, string: str, expanded: bool = False) -> Generator:
    patterns: Dict[
        str, Pattern[str]
    ] = EXPANDED_PATTERNS if expanded else REGULAR_PATTERNS
    try:
        return _find(string, patterns[type])
    except KeyError:
        raise ValueError("invalid request type: {type}".format(type=type))

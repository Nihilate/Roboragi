import re


def _patterns(tag_characters, expanded=False):
    """ Generate compiled regexes from a set of tag characters. """
    n = 2 if expanded else 1
    template = r'(?<![\S\{left}])\{left}{{{n}}}(?!\{left})(\S(?:[^\{left}\{right}]*\S)?)(?<!\{right})\{right}{{{n}}}(?![\S\{right}\(])'  # noqa: E501
    return {name: re.compile(template.format(left=chars[0], right=chars[1], n=n))  # noqa: E501
            for name, chars in tag_characters.items()}


def _all_patterns(patterns, flags=re.M):
    """ Generate a single compiled regex from all the given patterns. """
    patterns = '|'.join('(?:' + r.pattern + ')' for r in patterns)
    return re.compile(pattern=patterns, flags=flags)


USERNAME_PATTERN = re.compile(
    pattern=r'[uU]\/([A-Za-z0-9_-]+?)(>|}|$)',
    flags=re.S
)

SUBREDDIT_PATTERN = re.compile(
    pattern=r'[rR]\/([A-Za-z0-9_]+?)(>|}|$)',
    flags=re.S
)

TAG_CHARACTERS = {
    'anime': ('{', '}'),
    'manga': ('<', '>'),
    'light_novel': (']', '['),
    'visual_novel': ('|', '|'),
}
REGULAR_PATTERNS = _patterns(TAG_CHARACTERS)
REGULAR_PATTERNS['all'] = _all_patterns(REGULAR_PATTERNS.values())
EXPANDED_PATTERNS = _patterns(TAG_CHARACTERS, expanded=True)
EXPANDED_PATTERNS['all'] = _all_patterns(EXPANDED_PATTERNS.values())


def _find(string, pattern):
    for matches in pattern.finditer(string):
        for match in matches.groups():
            if match is not None:
                yield match


def find_requests(type, string, expanded=False):
    patterns = EXPANDED_PATTERNS if expanded else REGULAR_PATTERNS
    try:
        return _find(string, patterns[type])
    except KeyError:
        raise ValueError("invalid request type: {type}".format(type=type))

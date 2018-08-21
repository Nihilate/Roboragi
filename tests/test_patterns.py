import pytest

from roboragi.patterns import find_requests


@pytest.mark.parametrize('given,expected', [
    ('{K}', ['K']),
    ('{Bakemonogatari}', ['Bakemonogatari']),
    ('{Steins;Gate}', ['Steins;Gate']),
    ('{Kill la Kill}', ['Kill la Kill']),
    ('{ヒナまつり}', ['ヒナまつり']),
    ('{Re:Zero} {No Game No Life}', ['Re:Zero', 'No Game No Life']),
    ('{Gunbuster}, {Diebuster}', ['Gunbuster', 'Diebuster']),
    ('{Nisekoi}: Words Go Here', ['Nisekoi']),
    ('', []),
    ('{}', []),
    ('{ }', []),
    ('{  }', []),
    ('{trailing_whitespace }', []),
    ('{ leading_whitespace}', []),
    ('{ wrapping_whitespace }', []),
    ('no_whitespace{before}', []),
    ('{{extended}}', []),
    ('{{partial_before}', []),
    ('{partial_after}}', []),
    ('{nested{after}}', []),
    ('{{nested}before}', []),
])
def test_regular_anime(given, expected):
    actual = list(find_requests('anime', given))
    assert actual == expected


@pytest.mark.parametrize('given,expected', [
    ('{{K}}', ['K']),
    ('{{Bakemonogatari}}', ['Bakemonogatari']),
    ('{{Steins;Gate}}', ['Steins;Gate']),
    ('{{Kill la Kill}}', ['Kill la Kill']),
    ('{{ヒナまつり}}', ['ヒナまつり']),
    ('{{Re:Zero}} {{No Game No Life}}', ['Re:Zero', 'No Game No Life']),
    ('{{Gunbuster}}, {{Diebuster}}', ['Gunbuster', 'Diebuster']),
    ('{{Nisekoi}}: Words Go Here', ['Nisekoi']),
    ('', []),
    ('{{}}', []),
    ('{{ }}', []),
    ('{{  }}', []),
    ('{{trailing_whitespace }}', []),
    ('{{ leading_whitespace}}', []),
    ('{{ wrapping_whitespace }}', []),
    ('no_whitespace{{before}}', []),
    ('{regular}', []),
    ('{{{{partial_before}}', []),
    ('{{partial_after}}}}', []),
    ('{{nested{{after}}}}', []),
    ('{{{{nested}}before}}}', []),
])
def test_expanded_anime(given, expected):
    actual = list(find_requests('anime', given, expanded=True))
    assert actual == expected


@pytest.mark.parametrize('given,expected', [
    ('<K>', ['K']),
    ('<Bakemonogatari>', ['Bakemonogatari']),
    ('<Steins;Gate>', ['Steins;Gate']),
    ('<Kill la Kill>', ['Kill la Kill']),
    ('<ヒナまつり>', ['ヒナまつり']),
    ('<Re:Zero> <No Game No Life>', ['Re:Zero', 'No Game No Life']),
    ('<Gunbuster>, <Diebuster>', ['Gunbuster', 'Diebuster']),
    ('<Nisekoi>: Words Go Here', ['Nisekoi']),
    ('', []),
    ('<>', []),
    ('< >', []),
    ('<  >', []),
    ('<trailing_whitespace >', []),
    ('< leading_whitespace>', []),
    ('< wrapping_whitespace >', []),
    ('no_whitespace<before>', []),
    ('<<extended>>', []),
    ('<<partial_before>', []),
    ('<partial_after>>', []),
    ('<nested<after>>', []),
    ('<<nested>before>', []),
])
def test_regular_manga(given, expected):
    actual = list(find_requests('manga', given))
    assert actual == expected


@pytest.mark.parametrize('given,expected', [
    ('<<K>>', ['K']),
    ('<<Bakemonogatari>>', ['Bakemonogatari']),
    ('<<Steins;Gate>>', ['Steins;Gate']),
    ('<<Kill la Kill>>', ['Kill la Kill']),
    ('<<ヒナまつり>>', ['ヒナまつり']),
    ('<<Re:Zero>> <<No Game No Life>>', ['Re:Zero', 'No Game No Life']),
    ('<<Gunbuster>>, <<Diebuster>>', ['Gunbuster', 'Diebuster']),
    ('<<Nisekoi>>: Words Go Here', ['Nisekoi']),
    ('', []),
    ('<<>>', []),
    ('<< >>', []),
    ('<<  >>', []),
    ('<<trailing_whitespace >>', []),
    ('<< leading_whitespace>>', []),
    ('<< wrapping_whitespace >>', []),
    ('no_whitespace<<before>>', []),
    ('<regular>', []),
    ('<<<<partial_before>>', []),
    ('<<partial_after>>>>', []),
    ('<<nested<<after>>>>', []),
    ('<<<<nested>>before>>', []),
])
def test_expanded_manga(given, expected):
    actual = list(find_requests('manga', given, expanded=True))
    assert actual == expected


@pytest.mark.parametrize('given,expected', [
    (']K[', ['K']),
    (']Bakemonogatari[', ['Bakemonogatari']),
    (']Steins;Gate[', ['Steins;Gate']),
    (']Kill la Kill[', ['Kill la Kill']),
    (']ヒナまつり[', ['ヒナまつり']),
    (']Re:Zero[ ]No Game No Life[', ['Re:Zero', 'No Game No Life']),
    (']Gunbuster[, ]Diebuster[', ['Gunbuster', 'Diebuster']),
    (']Nisekoi[: Words Go Here', ['Nisekoi']),
    ('', []),
    ('][', []),
    ('] [', []),
    (']  [', []),
    (']trailing_whitespace [', []),
    ('] leading_whitespace[', []),
    ('] wrapping_whitespace [', []),
    ('no_whitespace]before[', []),
    (']]extended[[', []),
    (']]partial_before[', []),
    (']partial_after[[', []),
    (']nested]after[[', []),
    (']]nested[before[', []),
])
def test_regular_light_novel(given, expected):
    actual = list(find_requests('light_novel', given))
    assert actual == expected


@pytest.mark.parametrize('given,expected', [
    (']]K[[', ['K']),
    (']]Bakemonogatari[[', ['Bakemonogatari']),
    (']]Steins;Gate[[', ['Steins;Gate']),
    (']]Kill la Kill[[', ['Kill la Kill']),
    (']]ヒナまつり[[', ['ヒナまつり']),
    (']]Re:Zero[[ ]]No Game No Life[[', ['Re:Zero', 'No Game No Life']),
    (']]Gunbuster[[, ]]Diebuster[[', ['Gunbuster', 'Diebuster']),
    (']]Nisekoi[[: Words Go Here', ['Nisekoi']),
    ('', []),
    (']][[', []),
    (']] [[', []),
    (']]  [[', []),
    (']]trailing_whitespace [[', []),
    (']] leading_whitespace[[', []),
    (']] wrapping_whitespace [[', []),
    ('no_whitespace]]before[[', []),
    (']regular[', []),
    (']]]]partial_before[[', []),
    (']]partial_after[[[[', []),
    (']]nested]]after[[[[', []),
    (']]]]nested[[before[[', []),
])
def test_expanded_light_novel(given, expected):
    actual = list(find_requests('light_novel', given, expanded=True))
    assert actual == expected


@pytest.mark.parametrize('given,expected', [
    ('|K|', ['K']),
    ('|Bakemonogatari|', ['Bakemonogatari']),
    ('|Steins;Gate|', ['Steins;Gate']),
    ('|Kill la Kill|', ['Kill la Kill']),
    ('|ヒナまつり|', ['ヒナまつり']),
    ('|Re:Zero| |No Game No Life|', ['Re:Zero', 'No Game No Life']),
    ('|Gunbuster|, |Diebuster|', ['Gunbuster', 'Diebuster']),
    ('|Nisekoi|: Words Go Here', ['Nisekoi']),
    ('', []),
    ('||', []),
    ('| |', []),
    ('|  |', []),
    ('|trailing_whitespace |', []),
    ('| leading_whitespace|', []),
    ('| wrapping_whitespace |', []),
    ('no_whitespace|before|', []),
    ('||extended||', []),
    ('||partial_before|', []),
    ('|partial_after||', []),
    ('|nested|after||', []),
    ('||nested|before|', []),
])
def test_regular_visual_novel(given, expected):
    actual = list(find_requests('visual_novel', given))
    assert actual == expected


@pytest.mark.parametrize('given,expected', [
    ('||K||', ['K']),
    ('||Bakemonogatari||', ['Bakemonogatari']),
    ('||Steins;Gate||', ['Steins;Gate']),
    ('||Kill la Kill||', ['Kill la Kill']),
    ('||ヒナまつり||', ['ヒナまつり']),
    ('||Re:Zero|| ||No Game No Life||', ['Re:Zero', 'No Game No Life']),
    ('||Gunbuster||, ||Diebuster||', ['Gunbuster', 'Diebuster']),
    ('||Nisekoi||: Words Go Here', ['Nisekoi']),
    ('', []),
    ('||||', []),
    ('|| ||', []),
    ('||  ||', []),
    ('||trailing_whitespace ||', []),
    ('|| leading_whitespace||', []),
    ('|| wrapping_whitespace ||', []),
    ('no_whitespace||before||', []),
    ('|regular|', []),
    ('||||partial_before||', []),
    ('||partial_after||||', []),
    ('||nested||after||||', []),
    ('||||nested||before||', []),
])
def test_expanded_visual_novel(given, expected):
    actual = list(find_requests('visual_novel', given, expanded=True))
    assert actual == expected


def test_all_regular_patterns():
    given = ('This is an **example** [Markdown] comment.\n'
             'Here are some requests:\n'
             '{anime 1} {anime2}\n'
             '<manga 1> <manga2>\n'
             ']light novel 1[ ]light_novel2[\n'
             '|visual novel 1| |visual_novel2|\n\n'
             '[Markdown]: https://commonmark.org/')
    expected = [
        'anime 1',
        'anime2',
        'manga 1',
        'manga2',
        'light novel 1',
        'light_novel2',
        'visual novel 1',
        'visual_novel2',
    ]
    actual = list(find_requests('all', given))
    assert actual == expected


def test_all_extended_patterns():
    given = ('This is an **example** [Markdown] comment.\n'
             'Here are some requests:\n'
             '{{anime 1}} {{anime2}}\n'
             '<<manga 1>> <<manga2>>\n'
             ']]light novel 1[[ ]]light_novel2[[\n'
             '||visual novel 1|| ||visual_novel2||\n\n'
             '[Markdown]: https://commonmark.org/')
    expected = [
        'anime 1',
        'anime2',
        'manga 1',
        'manga2',
        'light novel 1',
        'light_novel2',
        'visual novel 1',
        'visual_novel2',
    ]
    actual = list(find_requests('all', given, expanded=True))
    assert actual == expected

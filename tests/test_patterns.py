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

from roboragi.patterns import find_requests


@pytest.mark.parametrize(
    "given,expected",
    [
        ("{K}", ["K"]),
        ("{Bakemonogatari}", ["Bakemonogatari"]),
        ("{Steins;Gate}", ["Steins;Gate"]),
        ("{Kill la Kill}", ["Kill la Kill"]),
        ("{ヒナまつり}", ["ヒナまつり"]),
        ("{Re:Zero} {No Game No Life}", ["Re:Zero", "No Game No Life"]),
        ("{Gunbuster}, {Diebuster}", ["Gunbuster", "Diebuster"]),
        ("{Nisekoi}: Words Go Here", ["Nisekoi"]),
        ("", []),
        ("{}", []),
        ("{ }", []),
        ("{  }", []),
        ("{trailing_whitespace }", []),
        ("{ leading_whitespace}", []),
        ("{ wrapping_whitespace }", []),
        ("words{before}", []),
        ("**{bold_markdown}**", ["bold_markdown"]),
        ("{{extended}}", []),
        ("{{partial_before}", []),
        ("{partial_after}}", []),
        ("{nested{after}}", []),
        ("{{nested}before}", []),
    ],
)
def test_regular_anime(given, expected):
    actual = list(find_requests("anime", given))
    assert actual == expected


@pytest.mark.parametrize(
    "given,expected",
    [
        ("{{K}}", ["K"]),
        ("{{Bakemonogatari}}", ["Bakemonogatari"]),
        ("{{Steins;Gate}}", ["Steins;Gate"]),
        ("{{Kill la Kill}}", ["Kill la Kill"]),
        ("{{ヒナまつり}}", ["ヒナまつり"]),
        ("{{Re:Zero}} {{No Game No Life}}", ["Re:Zero", "No Game No Life"]),
        ("{{Gunbuster}}, {{Diebuster}}", ["Gunbuster", "Diebuster"]),
        ("{{Nisekoi}}: Words Go Here", ["Nisekoi"]),
        ("", []),
        ("{{}}", []),
        ("{{ }}", []),
        ("{{  }}", []),
        ("{{trailing_whitespace }}", []),
        ("{{ leading_whitespace}}", []),
        ("{{ wrapping_whitespace }}", []),
        ("words{{before}}", []),
        ("**{{bold_markdown}}**", ["bold_markdown"]),
        ("{regular}", []),
        ("{{{{partial_before}}", []),
        ("{{partial_after}}}}", []),
        ("{{nested{{after}}}}", []),
        ("{{{{nested}}before}}}", []),
    ],
)
def test_expanded_anime(given, expected):
    actual = list(find_requests("anime", given, expanded=True))
    assert actual == expected


@pytest.mark.parametrize(
    "given,expected",
    [
        ("<K>", ["K"]),
        ("<Bakemonogatari>", ["Bakemonogatari"]),
        ("<Steins;Gate>", ["Steins;Gate"]),
        ("<Kill la Kill>", ["Kill la Kill"]),
        ("<ヒナまつり>", ["ヒナまつり"]),
        ("<Re:Zero> <No Game No Life>", ["Re:Zero", "No Game No Life"]),
        ("<Gunbuster>, <Diebuster>", ["Gunbuster", "Diebuster"]),
        ("<Nisekoi>: Words Go Here", ["Nisekoi"]),
        ("", []),
        ("<>", []),
        ("< >", []),
        ("<  >", []),
        ("<trailing_whitespace >", []),
        ("< leading_whitespace>", []),
        ("< wrapping_whitespace >", []),
        ("words<before>", []),
        ("**<bold_markdown>**", ["bold_markdown"]),
        ("<<extended>>", []),
        ("<<partial_before>", []),
        ("<partial_after>>", []),
        ("<nested<after>>", []),
        ("<<nested>before>", []),
    ],
)
def test_regular_manga(given, expected):
    actual = list(find_requests("manga", given))
    assert actual == expected


@pytest.mark.parametrize(
    "given,expected",
    [
        ("<<K>>", ["K"]),
        ("<<Bakemonogatari>>", ["Bakemonogatari"]),
        ("<<Steins;Gate>>", ["Steins;Gate"]),
        ("<<Kill la Kill>>", ["Kill la Kill"]),
        ("<<ヒナまつり>>", ["ヒナまつり"]),
        ("<<Re:Zero>> <<No Game No Life>>", ["Re:Zero", "No Game No Life"]),
        ("<<Gunbuster>>, <<Diebuster>>", ["Gunbuster", "Diebuster"]),
        ("<<Nisekoi>>: Words Go Here", ["Nisekoi"]),
        ("", []),
        ("<<>>", []),
        ("<< >>", []),
        ("<<  >>", []),
        ("<<trailing_whitespace >>", []),
        ("<< leading_whitespace>>", []),
        ("<< wrapping_whitespace >>", []),
        ("words<<before>>", []),
        ("**<<bold_markdown>>**", ["bold_markdown"]),
        ("<regular>", []),
        ("<<<<partial_before>>", []),
        ("<<partial_after>>>>", []),
        ("<<nested<<after>>>>", []),
        ("<<<<nested>>before>>", []),
    ],
)
def test_expanded_manga(given, expected):
    actual = list(find_requests("manga", given, expanded=True))
    assert actual == expected


@pytest.mark.parametrize(
    "given,expected",
    [
        ("]K[", ["K"]),
        ("]Bakemonogatari[", ["Bakemonogatari"]),
        ("]Steins;Gate[", ["Steins;Gate"]),
        ("]Kill la Kill[", ["Kill la Kill"]),
        ("]ヒナまつり[", ["ヒナまつり"]),
        ("]Re:Zero[ ]No Game No Life[", ["Re:Zero", "No Game No Life"]),
        ("]Gunbuster[, ]Diebuster[", ["Gunbuster", "Diebuster"]),
        ("]Nisekoi[: Words Go Here", ["Nisekoi"]),
        ("", []),
        ("][", []),
        ("] [", []),
        ("]  [", []),
        ("]trailing_whitespace [", []),
        ("] leading_whitespace[", []),
        ("] wrapping_whitespace [", []),
        ("words]before[", []),
        ("**]bold_markdown[**", ["bold_markdown"]),
        ("]]extended[[", []),
        ("]]partial_before[", []),
        ("]partial_after[[", []),
        ("]nested]after[[", []),
        ("]]nested[before[", []),
    ],
)
def test_regular_light_novel(given, expected):
    actual = list(find_requests("light_novel", given))
    assert actual == expected


@pytest.mark.parametrize(
    "given,expected",
    [
        ("]]K[[", ["K"]),
        ("]]Bakemonogatari[[", ["Bakemonogatari"]),
        ("]]Steins;Gate[[", ["Steins;Gate"]),
        ("]]Kill la Kill[[", ["Kill la Kill"]),
        ("]]ヒナまつり[[", ["ヒナまつり"]),
        ("]]Re:Zero[[ ]]No Game No Life[[", ["Re:Zero", "No Game No Life"]),
        ("]]Gunbuster[[, ]]Diebuster[[", ["Gunbuster", "Diebuster"]),
        ("]]Nisekoi[[: Words Go Here", ["Nisekoi"]),
        ("", []),
        ("]][[", []),
        ("]] [[", []),
        ("]]  [[", []),
        ("]]trailing_whitespace [[", []),
        ("]] leading_whitespace[[", []),
        ("]] wrapping_whitespace [[", []),
        ("words]]before[[", []),
        ("**]]bold_markdown[[**", ["bold_markdown"]),
        ("]regular[", []),
        ("]]]]partial_before[[", []),
        ("]]partial_after[[[[", []),
        ("]]nested]]after[[[[", []),
        ("]]]]nested[[before[[", []),
    ],
)
def test_expanded_light_novel(given, expected):
    actual = list(find_requests("light_novel", given, expanded=True))
    assert actual == expected


@pytest.mark.parametrize(
    "given,expected",
    [
        ("|K|", ["K"]),
        ("|Bakemonogatari|", ["Bakemonogatari"]),
        ("|Steins;Gate|", ["Steins;Gate"]),
        ("|Kill la Kill|", ["Kill la Kill"]),
        ("|ヒナまつり|", ["ヒナまつり"]),
        ("|Re:Zero| |No Game No Life|", ["Re:Zero", "No Game No Life"]),
        ("|Gunbuster|, |Diebuster|", ["Gunbuster", "Diebuster"]),
        ("|Nisekoi|: Words Go Here", ["Nisekoi"]),
        ("", []),
        ("||", []),
        ("| |", []),
        ("|  |", []),
        ("|trailing_whitespace |", []),
        ("| leading_whitespace|", []),
        ("| wrapping_whitespace |", []),
        ("words|before|", []),
        ("**|bold_markdown|**", ["bold_markdown"]),
        ("||extended||", []),
        ("||partial_before|", []),
        ("|partial_after||", []),
        ("|nested|after||", []),
        ("||nested|before|", []),
    ],
)
def test_regular_visual_novel(given, expected):
    actual = list(find_requests("visual_novel", given))
    assert actual == expected


@pytest.mark.parametrize(
    "given,expected",
    [
        ("||K||", ["K"]),
        ("||Bakemonogatari||", ["Bakemonogatari"]),
        ("||Steins;Gate||", ["Steins;Gate"]),
        ("||Kill la Kill||", ["Kill la Kill"]),
        ("||ヒナまつり||", ["ヒナまつり"]),
        ("||Re:Zero|| ||No Game No Life||", ["Re:Zero", "No Game No Life"]),
        ("||Gunbuster||, ||Diebuster||", ["Gunbuster", "Diebuster"]),
        ("||Nisekoi||: Words Go Here", ["Nisekoi"]),
        ("", []),
        ("||||", []),
        ("|| ||", []),
        ("||  ||", []),
        ("||trailing_whitespace ||", []),
        ("|| leading_whitespace||", []),
        ("|| wrapping_whitespace ||", []),
        ("words||before||", []),
        ("**||bold_markdown||**", ["bold_markdown"]),
        ("|regular|", []),
        ("||||partial_before||", []),
        ("||partial_after||||", []),
        ("||nested||after||||", []),
        ("||||nested||before||", []),
    ],
)
def test_expanded_visual_novel(given, expected):
    actual = list(find_requests("visual_novel", given, expanded=True))
    assert actual == expected


def test_all_regular_patterns():
    given = (
        "This is an **example** [Markdown](https://commonmark.org/)\n"
        "comment. Here are some requests:\n"
        "{anime 1} {anime2}\n"
        "<manga 1> <manga2>\n"
        "]light novel 1[ ]light_novel2[\n"
        "|visual novel 1| |visual_novel2|\n"
    )
    expected = [
        "anime 1",
        "anime2",
        "manga 1",
        "manga2",
        "light novel 1",
        "light_novel2",
        "visual novel 1",
        "visual_novel2",
    ]
    actual = list(find_requests("all", given))
    assert actual == expected


def test_all_extended_patterns():
    given = (
        "This is an **example** [Markdown](https://commonmark.org/)\n"
        "comment. Here are some requests:\n"
        "{{anime 1}} {{anime2}}\n"
        "<<manga 1>> <<manga2>>\n"
        "]]light novel 1[[ ]]light_novel2[[\n"
        "||visual novel 1|| ||visual_novel2||\n"
    )
    expected = [
        "anime 1",
        "anime2",
        "manga 1",
        "manga2",
        "light novel 1",
        "light_novel2",
        "visual novel 1",
        "visual_novel2",
    ]
    actual = list(find_requests("all", given, expanded=True))
    assert actual == expected

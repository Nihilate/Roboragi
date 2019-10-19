"""
Search.py
Returns a built comment created from multiple databases when given a search
term.
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

import json
import sqlite3
import traceback

import Anilist
import AnimePlanet as AniP
import CommentBuilder
import DatabaseHandler
import Kitsu
import LNDB
import MU
import NU
from VNDB import VNDB

USERNAME = ""

try:
    import Config

    USERNAME = Config.username
except ImportError:
    pass

sqlConn = sqlite3.connect("synonyms.db")
sqlCur = sqlConn.cursor()

try:
    query = (
        "SELECT dbLinks"
        "  FROM synonyms"
        ' WHERE type = "Manga"'
        "   AND lower(name) = ?;"
    )
    sqlCur.execute(query, ["despair simulator"])
except sqlite3.Error as e:
    print(e)


def buildMangaReply(searchText, isExpanded, baseComment, blockTracking=False):
    """ Builds a manga reply from multiple sources """
    try:
        ani = {
            "search_function": Anilist.getMangaDetails,
            "title_function": Anilist.getTitles,
            "synonym_function": Anilist.getSynonyms,
            "checked_synonyms": [],
            "result": None,
        }
        kit = {
            "search_function": Kitsu.search_manga,
            "synonym_function": Kitsu.get_synonyms,
            "title_function": Kitsu.get_titles,
            "checked_synonyms": [],
            "result": None,
        }
        mu = {"search_function": MU.getMangaURL, "result": None}
        ap = {"search_function": AniP.getMangaURL, "result": None}

        try:
            query = (
                "SELECT dbLinks"
                "  FROM synonyms"
                ' WHERE type = "Manga"'
                "   AND lower(name) = ?"
            )
            sqlCur.execute(query, [searchText.lower()])
        except sqlite3.Error as e:
            print(e)

        alternateLinks = sqlCur.fetchone()

        if alternateLinks:
            synonym = json.loads(alternateLinks[0])

            if synonym:
                anisyn = None
                if "ani" in synonym and synonym["ani"]:
                    anisyn = synonym["ani"]

                kitsyn = None
                if "kit" in synonym and synonym["kit"]:
                    kitsyn = synonym["kit"]

                musyn = None
                if "mu" in synonym and synonym["mu"]:
                    musyn = synonym["mu"]

                apsyn = None
                if "ap" in synonym and synonym["ap"]:
                    apsyn = synonym["ap"]

                if anisyn:
                    ani["result"] = Anilist.getMangaDetailsById(anisyn)
                else:
                    ani["result"] = None
                kit["result"] = Kitsu.get_manga(kitsyn) if kitsyn else None
                mu["result"] = MU.getMangaURLById(musyn) if musyn else None
                ap["result"] = AniP.getMangaURLById(apsyn) if apsyn else None

        else:
            data_sources = [ani, kit]
            aux_sources = [mu, ap]

            synonyms = set([searchText])
            titles = set()

            for x in range(len(data_sources)):
                for source in data_sources:
                    if source["result"]:
                        break
                    else:
                        for title in titles:
                            if title in source["checked_synonyms"]:
                                break

                            if source["result"]:
                                break

                            source["result"] = source["search_function"](title)
                            source["checked_synonyms"].append(title)

                            if source["result"]:
                                break

                        for synonym in synonyms:
                            if synonym in source["checked_synonyms"]:
                                break

                            if source["result"]:
                                break

                            search_function = source["search_function"]
                            source["result"] = search_function(synonym)
                            source["checked_synonyms"].append(synonym)

                            if source["result"]:
                                break

                    if source["result"]:
                        result = source["result"]
                        synonym_function = source["synonym_function"]
                        title_function = source["title_function"]
                        synonyms.update([s.lower() for s in synonym_function(result)])
                        titles.update([t.lower() for t in title_function(result)])

            for source in aux_sources:
                for title in titles:
                    source["result"] = source["search_function"](synonym)

                    if source["result"]:
                        break

                if not source["result"]:
                    for synonym in synonyms:
                        source["result"] = source["search_function"](synonym)

                        if source["result"]:
                            break

        if ani["result"] or kit["result"]:
            try:
                titleToAdd = ""
                if ani["result"]:
                    try:
                        titleToAdd = ani["result"]["title_romaji"]
                    except Exception:
                        titleToAdd = ani["result"]["title_english"]
                elif kit["result"]:
                    try:
                        titleToAdd = kit["result"]["title_romaji"]
                    except Exception:
                        titleToAdd = kit["result"]["title_english"]

                subreddit = str(baseComment.subreddit).lower
                ignored_subreddits = ("nihilate", "roboragi")
                if subreddit not in ignored_subreddits and not blockTracking:
                    DatabaseHandler.addRequest(
                        name=titleToAdd,
                        rType="Manga",
                        requester=baseComment.author.name,
                        subreddit=baseComment.subreddit,
                    )
            except Exception:
                traceback.print_exc()
                pass

        if ani["result"] or kit["result"]:
            return CommentBuilder.buildMangaComment(
                isExpanded=isExpanded,
                ani=ani["result"],
                mu=mu["result"],
                ap=ap["result"],
                kit=kit["result"],
            )
        else:
            print("No result found for " + searchText)
            return None

    except Exception:
        traceback.print_exc()
        return None


def buildAnimeReply(searchText, isExpanded, baseComment, blockTracking=False):
    """ Builds an anime reply from multiple sources """
    try:
        kit = {
            "search_function": Kitsu.search_anime,
            "synonym_function": Kitsu.get_synonyms,
            "title_function": Kitsu.get_titles,
            "checked_synonyms": [],
            "result": None,
        }
        ani = {
            "search_function": Anilist.getAnimeDetails,
            "synonym_function": Anilist.getSynonyms,
            "title_function": Anilist.getTitles,
            "checked_synonyms": [],
            "result": None,
        }
        ap = {"search_function": AniP.getAnimeURL, "result": None}

        try:
            query = (
                "SELECT dbLinks"
                "  FROM synonyms"
                ' WHERE type = "Anime"'
                "   AND lower(name) = ?"
            )
            sqlCur.execute(query, [searchText.lower()])
        except sqlite3.Error as e:
            print(e)

        alternateLinks = sqlCur.fetchone()

        if alternateLinks:
            synonym = json.loads(alternateLinks[0])

            if synonym:
                kitsyn = None
                if "kit" in synonym and synonym["kit"]:
                    kitsyn = synonym["kit"]

                anisyn = None
                if "ani" in synonym and synonym["ani"]:
                    anisyn = synonym["ani"]

                apsyn = None
                if "ap" in synonym and synonym["ap"]:
                    apsyn = synonym["ap"]

                kit["result"] = Kitsu.get_anime(kitsyn) if kitsyn else None

                if anisyn:
                    ani["result"] = Anilist.getAnimeDetailsById(anisyn)
                else:
                    ani["result"] = None

                ap["result"] = AniP.getAnimeURLById(apsyn) if apsyn else None

        else:
            data_sources = [ani, kit]
            aux_sources = [ap]

            synonyms = set([searchText])
            titles = set()

            for x in range(len(data_sources)):
                for source in data_sources:
                    if source["result"]:
                        break
                    else:
                        for synonym in titles | synonyms:
                            if synonym in source["checked_synonyms"]:
                                continue

                            search_function = source["search_function"]
                            source["result"] = search_function(synonym)
                            source["checked_synonyms"].append(synonym)

                            if source["result"]:
                                break

                    if source["result"]:
                        result = source["result"]
                        synonym_function = source["synonym_function"]
                        title_function = source["title_function"]
                        synonyms.update([s.lower() for s in synonym_function(result)])
                        titles.update([t.lower() for t in title_function(result)])

            for source in aux_sources:
                for title in titles:
                    source["result"] = source["search_function"](synonym)

                    if source["result"]:
                        break

                if not source["result"]:
                    for synonym in synonyms:
                        source["result"] = source["search_function"](synonym)

                        if source["result"]:
                            break

        if ani["result"] or kit["result"]:
            try:
                titleToAdd = ""
                if ani["result"]:
                    if "title_romaji" in ani["result"]:
                        titleToAdd = ani["result"]["title_romaji"]
                elif kit["result"]:
                    if "title_romaji" in kit["result"]:
                        titleToAdd = kit["result"]["title_romaji"]

                subreddit = str(baseComment.subreddit).lower
                ignored_subreddits = ("nihilate", "roboragi")
                if subreddit not in ignored_subreddits and not blockTracking:
                    DatabaseHandler.addRequest(
                        name=titleToAdd,
                        rType="Anime",
                        requester=baseComment.author.name,
                        subreddit=baseComment.subreddit,
                    )
            except Exception:
                traceback.print_exc()
                pass

        if ani["result"] or kit["result"]:
            return CommentBuilder.buildAnimeComment(
                isExpanded=isExpanded,
                ani=ani["result"],
                ap=ap["result"],
                kit=kit["result"],
            )
        else:
            print("No result found for " + searchText)
            return None

    except Exception:
        traceback.print_exc()
        return None


def buildLightNovelReply(searchText, isExpanded, baseComment, blockTracking=False):
    """ Builds an LN reply from multiple sources """
    try:
        ani = {
            "search_function": Anilist.getLightNovelDetails,
            "synonym_function": Anilist.getSynonyms,
            "title_function": Anilist.getTitles,
            "checked_synonyms": [],
            "result": None,
        }
        kit = {
            "search_function": Kitsu.search_light_novel,
            "synonym_function": Kitsu.get_synonyms,
            "title_function": Kitsu.get_titles,
            "checked_synonyms": [],
            "result": None,
        }
        nu = {"search_function": NU.getLightNovelURL, "result": None}
        lndb = {"search_function": LNDB.getLightNovelURL, "result": None}

        try:
            query = (
                "SELECT dbLinks"
                "  FROM synonyms"
                ' WHERE type = "LN"'
                "   AND lower(name) = ?"
            )
            sqlCur.execute(query, [searchText.lower()])
        except sqlite3.Error as e:
            print(e)

        alternateLinks = sqlCur.fetchone()

        if alternateLinks:
            synonym = json.loads(alternateLinks[0])

            if synonym:
                anisyn = None
                if "ani" in synonym and synonym["ani"]:
                    anisyn = synonym["ani"]

                kitsyn = None
                if "kit" in synonym and synonym["kit"]:
                    kitsyn = synonym["kit"]

                nusyn = None
                if "nu" in synonym and synonym["nu"]:
                    nusyn = synonym["nu"]

                lndbsyn = None
                if "lndb" in synonym and synonym["lndb"]:
                    lndbsyn = synonym["lndb"]

                if anisyn:
                    ani["result"] = Anilist.getMangaDetailsById(anisyn)
                else:
                    ani["result"] = None

                if kitsyn:
                    kit["result"] = Kitsu.get_light_novel(kitsyn)
                else:
                    kit["result"] = None

                nu["result"] = NU.getLightNovelById(nusyn) if nusyn else None

                if lndbsyn:
                    lndb["result"] = LNDB.getLightNovelById(lndbsyn)
                else:
                    lndb["result"] = None

        else:
            data_sources = [ani, kit]
            aux_sources = [nu, lndb]

            synonyms = set([searchText])
            titles = set()

            for x in range(len(data_sources)):
                for source in data_sources:
                    if source["result"]:
                        break
                    else:
                        for synonym in titles | synonyms:
                            if synonym in source["checked_synonyms"]:
                                continue

                            search_function = source["search_function"]
                            source["result"] = search_function(synonym)
                            source["checked_synonyms"].append(synonym)

                            if source["result"]:
                                break

                    if source["result"]:
                        result = source["result"]
                        synonym_function = source["synonym_function"]
                        title_function = source["title_function"]
                        synonyms.update([s.lower() for s in synonym_function(result)])
                        titles.update([t.lower() for t in title_function(result)])

            for source in aux_sources:
                for title in titles:
                    source["result"] = source["search_function"](synonym)

                    if source["result"]:
                        break

                if not source["result"]:
                    for synonym in synonyms:
                        source["result"] = source["search_function"](synonym)

                        if source["result"]:
                            break

        if ani["result"] or kit["result"]:
            try:
                titleToAdd = ""
                if ani["result"]:
                    try:
                        titleToAdd = ani["result"]["title_romaji"]
                    except Exception:
                        titleToAdd = ani["result"]["title_english"]
                elif kit["result"]:
                    try:
                        titleToAdd = kit["result"]["title_romaji"]
                    except Exception:
                        titleToAdd = kit["result"]["title_english"]

                subreddit = str(baseComment.subreddit).lower
                ignored_subreddits = ("nihilate", "roboragi")
                if subreddit not in ignored_subreddits and not blockTracking:
                    DatabaseHandler.addRequest(
                        name=titleToAdd,
                        rType="LN",
                        requester=baseComment.author.name,
                        subreddit=baseComment.subreddit,
                    )
            except Exception:
                traceback.print_exc()
                pass

        if ani["result"] or kit["result"]:
            return CommentBuilder.buildLightNovelComment(
                isExpanded=isExpanded,
                ani=ani["result"],
                nu=nu["result"],
                lndb=lndb["result"],
                kit=kit["result"],
            )
        else:
            print("No result found for " + searchText)
            return None

    except Exception:
        traceback.print_exc()
        return None


def buildVisualNovelReply(searchText, isExpanded, baseComment, blockTracking=False):
    """ Builds an VN reply from VNDB """
    try:
        vndb = VNDB()

        try:
            query = (
                "SELECT dbLinks"
                "  FROM synonyms"
                ' WHERE type = "VN"'
                "   AND lower(name) = ?"
            )
            sqlCur.execute(query, [searchText.lower()])
        except sqlite3.Error as e:
            print(e)

        alternateLinks = sqlCur.fetchone()

        if alternateLinks:
            synonym = json.loads(alternateLinks[0])

            if synonym:
                if "vndb" in synonym and synonym["vndb"]:
                    synonym = synonym["vndb"]

                if synonym:
                    result = vndb.getVisualNovelDetailsById(synonym)
                else:
                    result = None

        else:
            result = vndb.getVisualNovelDetails(searchText)

        vndb.close()

        if result:
            try:
                titleToAdd = result["title"]

                subreddit = str(baseComment.subreddit).lower
                ignored_subreddits = ("nihilate", "roboragi")
                if subreddit not in ignored_subreddits and not blockTracking:
                    DatabaseHandler.addRequest(
                        name=titleToAdd,
                        rType="VN",
                        requester=baseComment.author.name,
                        subreddit=baseComment.subreddit,
                    )
            except Exception:
                traceback.print_exc()
                pass

            return CommentBuilder.buildVisualNovelComment(isExpanded, result)
        else:
            print("No result found for " + searchText)
            return None

    except Exception:
        traceback.print_exc()
        return None


def isValidComment(comment):
    """
    Checks if the comment is valid (i.e. not already seen, not a post by
    Roboragi and the parent commenter isn't Roboragi)
    """
    try:
        if DatabaseHandler.commentExists(comment.id):
            return False

        try:
            if comment.author.name == USERNAME:
                DatabaseHandler.addComment(
                    commentid=comment.id,
                    requester=comment.author.name,
                    subreddit=comment.subreddit,
                    hadRequest=False,
                )
                return False
        except Exception:
            pass

        return True

    except Exception:
        traceback.print_exc()
        return False

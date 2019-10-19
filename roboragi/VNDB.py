"""
    @author: Modified from HarHar's (https://github.com/HarHar) VNDB Python API
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
import json
import socket
import time
import traceback

import Config

cache = {"get": []}
cachetime = 720  # cache stuff for 12 minutes

username = Config.vndbuser
password = Config.vndbpassword

client_name = "RoboragiRedditBot"
client_version = "1.0"
client_protocol = 1


class vndbException(Exception):
    pass


class VNDB(object):
    """ Python interface for vndb's api (vndb.org), featuring cache """

    protocol = 1

    def __init__(self):
        self.sock = socket.socket()
        self.sock.connect(("api.vndb.org", 19534))

        login_args = dict(
            protocol=client_protocol,
            client=client_name,
            clientver=float(client_version),
        )

        self.sendCommand("login", login_args)

        res = self.getRawResponse()
        if res.find("error ") == 0:
            msg = json.loads(" ".join(res.split(" ")[1:]))["msg"]
            raise vndbException(msg)

    def close(self):
        self.sock.close()

    def get(self, type, flags, filters, options):
        """ Gets a VN/producer

        Example:
        >>> results = vndb.get('vn', 'basic', '(title="Clannad")', '')
        >>> results['items'][0]['image']
        u'http://s.vndb.org/cv/99/4599.jpg'
        """
        args = "{0} {1} {2} {3}".format(type, flags, filters, options)
        for item in cache["get"]:
            item_query = item["query"]
            cached_time = item["time"] + cachetime
            if item_query == args and time.time() < cached_time:
                return item["results"]

        self.sendCommand("get", args)
        res = self.getResponse()[1]
        cache["get"].append(dict(time=time.time(), query=args, results=res))
        return res

    def sendCommand(self, command, args=None):
        """ Sends a command

        Example
        >>> self.sendCommand('test', {'this is an': 'argument'})
        """
        whole = ""
        whole += command.lower()
        if isinstance(args, str):
            whole += " " + args
        elif isinstance(args, dict):
            whole += " " + json.dumps(args)

        self.sock.send("{0}\x04".format(whole).encode())

    def getResponse(self):
        """
        Returns a tuple of the response to a command that was previously sent

        Example
        >>> self.sendCommand('test')
        >>> self.getResponse()
        ('ok', {'test': 0})
        """
        res = self.getRawResponse()
        cmdname = res.split(" ")[0]
        if len(res.split(" ")) > 1:
            args = json.loads(" ".join(res.split(" ")[1:]))

        if cmdname == "error":
            if args["id"] == "throttled":
                msg = "Throttled, limit of 100 commands per 10 minutes"
                raise vndbException(msg)
            else:
                raise vndbException(args["msg"])
        return (cmdname, args)

    def getRawResponse(self):
        """ Returns a raw response to a command that was previously sent

        Example:
        >>> self.sendCommand('test')
        >>> self.getRawResponse()
        'ok {"test": 0}'
        """
        finished = False
        whole = ""
        while not finished:
            whole += self.sock.recv(4096).decode()
            if "\x04" in whole:
                finished = True
        return whole.replace("\x04", "").strip()

    def parseResults(self, results):
        parsed_results = []
        for result in results["items"]:
            try:
                id_ = result["id"]
                title = result["title"]
                url = f"https://vndb.org/v{id_}"
                description = result["description"]
                length = self.parseLength(result["length"])

                if result["aliases"]:
                    synonyms = result["aliases"].split("\n")
                else:
                    synonyms = []

                wikipedia = result["links"]["wikipedia"]
                if wikipedia:
                    wikipedia_url = f"https://wikipedia.org/wiki/{wikipedia}"
                else:
                    wikipedia_url = None

                if result["released"]:
                    released = result["released"][:4]
                else:
                    released = None

                parsed_results.append(
                    dict(
                        id=id_,
                        title=title,
                        synonyms=synonyms,
                        url=url,
                        wikipedia_url=wikipedia_url,
                        description=description,
                        length=length,
                        release_year=released,
                    )
                )
            except Exception:
                traceback.print_exc()
        return parsed_results

    def parseLength(self, length):
        if length == 1:
            return "Very Short"
        elif length == 2:
            return "Short"
        elif length == 3:
            return "Medium"
        elif length == 4:
            return "Long"
        elif length == 5:
            return "Very Long"
        return "Unknown"

    def getClosest(self, searchText, listOfVNs):
        titleList = [vn["title"].lower() for vn in listOfVNs if vn["title"]]

        closestFromTitles = difflib.get_close_matches(
            word=searchText.lower(), possibilities=titleList, n=1, cutoff=0.95
        )

        if closestFromTitles:
            titleToFind = closestFromTitles[0]
            for vn in listOfVNs:
                if vn["title"].lower() == titleToFind:
                    return vn

        synonymList = []
        for vn in listOfVNs:
            for synonym in vn["synonyms"]:
                synonymList.append(synonym.lower())

        closestFromSynonyms = difflib.get_close_matches(
            word=searchText.lower(), possibilities=synonymList, n=1, cutoff=0.95
        )

        if closestFromSynonyms:
            synonymToFind = closestFromSynonyms[0]
            for vn in listOfVNs:
                synonyms = [synonym.lower() for synonym in vn["synonyms"]]
                if synonymToFind.lower() in synonyms:
                    return vn

        return None

    def getVisualNovelDetails(self, searchText):
        try:
            results = self.get(
                type="vn",
                flags="basic,details",
                filters='(search~"{0}")'.format(searchText),
                options="",
            )
            parsed_results = self.parseResults(results)
            closest = self.getClosest(searchText, parsed_results)

            return closest
        except Exception:
            traceback.print_exc()
            return None

    def getVisualNovelDetailsById(self, id):
        try:
            results = self.get(
                type="vn",
                flags="basic,details",
                filters='(id="{0}")'.format(str(id)),
                options="",
            )
            parsed_results = self.parseResults(results)

            return parsed_results[0] if parsed_results else None
        except Exception:
            traceback.print_exc()
            return None

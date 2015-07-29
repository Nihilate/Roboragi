'''
MU.py
Handles all MangaUpdates information
'''

from html.parser import HTMLParser
import requests

MULink = None

#Parses the HTML scraped from MU and gives us the first URL to a series it gives us.
class MUParser(HTMLParser):
    global MULink
    
    def handle_starttag(self, tag, attrs):
        global MULink

        for attr in attrs:
            try:
                if ('https://www.mangaupdates.com/series.html?id=' in attr[1]) and (MULink is None):
                    MULink = attr[1]
            except:
                pass

#Searches MU and returns the very first manga series it finds. NOT IDEAL.
def getMangaURL(searchText):
    try:
        global MULink
        MULink = None
        
        payload = {'search': searchText}
        searchtext = requests.get('https://www.mangaupdates.com/series.html', params=payload)
            
        parser = MUParser()
        parser.feed(searchtext.text)

        return MULink
    except Exception as e:
        return None

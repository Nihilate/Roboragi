'''
AnimeBot.py
Acts as the "main" file and ties all the other functionality together.
'''

import praw
import re
import traceback
import time

import Search
import CommentBuilder
import DatabaseHandler
import Config
import Reference

TIME_BETWEEN_PM_CHECKS = 60  # in seconds

USERNAME = Config.username
PASSWORD = Config.password
USERAGENT = Config.useragent
REDDITAPPID = Config.redditappid
REDDITAPPSECRET = Config.redditappsecret
REFRESHTOKEN = Config.refreshtoken
SUBREDDITLIST = Config.get_formatted_subreddit_list()

reddit = praw.Reddit(user_agent=USERNAME)

# the subreddits where expanded requests are disabled
disableexpanded = ['animesuggest']

# subreddits I'm actively avoiding
exiled = ['anime']

USERNAME_PATTERN = re.compile(
    pattern=r'[uU]\/([A-Za-z0-9_-]+?)(>|}|$)',
    flags=re.S
)

SUBREDDIT_PATTERN = re.compile(
    pattern=r'[rR]\/([A-Za-z0-9_]+?)(>|}|$)',
    flags=re.S
)


# Sets up Reddit for PRAW
def setupReddit():
    try:
        print('Setting up Reddit')
        reddit.set_oauth_app_info(
            client_id=REDDITAPPID,
            client_secret=REDDITAPPSECRET,
            redirect_uri='http://127.0.0.1:65010/' 'authorize_callback'
        )
        reddit.refresh_access_information(REFRESHTOKEN)
        print('Reddit successfully set up')
    except Exception as e:
        print('Error with setting up Reddit: ' + str(e))


def get_regular_regex(left_brace_character, right_brace_character):
    return r'(?<=(?<!\S)\{0})([^\{0}\{1}]+?)(?=\{1}(?!\())'.format(left_brace_character, right_brace_character)


def get_expanded_regex(left_brace_character, right_brace_character):
    return r'\{0}{{2}}(.+?)\{1}{{2}}'.format(left_brace_character, right_brace_character)


def get_regular_requests(comment, left_brace_character, right_brace_character):
    requests = get_requests(
        comment,
        get_regular_regex(left_brace_character, right_brace_character)
    )
    for request in requests:
        yield request


def get_expanded_requests(comment, left_brace_character, right_brace_character):
    requests = get_requests(
        comment,
        get_expanded_regex(left_brace_character, right_brace_character)
    )
    for request in requests:
        yield request


def get_requests(comment, regex):
    for match in re.finditer(regex, comment, re.M):
        matched_text = match.group(1)
        if not re.match(r'\s', matched_text) and not re.match(r'^.+\s$', matched_text):
            yield matched_text


def process_pms():
    """ function for processing edit requests via pm """
    for msg in reddit.get_unread(limit=None):
        usernameMention = msg.subject == 'username mention'
        usernameInBody = msg.subject == 'comment reply' and 'u/roboragi' in msg.body.lower()

        # This PM doesn't meet the response criteria. Skip it.
        if not (usernameMention or usernameInBody):
            continue

        # Figure out if there might be any tags in the message body.
        hasCurlies = '{' in msg.body and '}' in msg.body
        hasPointies = '<' in msg.body and '>' in msg.body
        hasSquares = ']' in msg.body and '[' in msg.body
        hasVerticalBars = '|' in msg.body

        # There are no tags to process in the message body. Skip this PM.
        if not any((hasCurlies, hasPointies, hasSquares, hasVerticalBars)):
            continue

        if str(msg.subreddit).lower() in exiled:
            continue

        try:
            mentionedComment = reddit.get_info(thing_id=msg.name)
            mentionedComment.refresh()

            replies = mentionedComment.replies

            ownComments = []
            commentToEdit = None

            for reply in replies:
                if (reply.author.name == 'Roboragi'):
                    ownComments.append(reply)

            for comment in ownComments:
                if 'http://www.reddit.com/r/Roboragi/wiki/index' in comment.body:
                    commentToEdit = comment

            commentReply = process_comment(mentionedComment, True)

            try:
                if (commentReply):
                    if commentToEdit:
                        commentToEdit.edit(commentReply)
                        print('Comment edited.\n')
                    else:
                        mentionedComment.reply(commentReply)
                        print('Comment made.\n')

                    msg.mark_as_read()

                    if not (DatabaseHandler.commentExists(mentionedComment.id)):
                        DatabaseHandler.addComment(
                            mentionedComment.id,
                            mentionedComment.author.name,
                            msg.subreddit,
                            True
                        )
            except praw.errors.Forbidden:
                print('Edit request from banned '
                      'subreddit: {0}\n'.format(msg.subreddit))

        except Exception as e:
            print(e)


def process_comment(comment, is_edit=False):
    """ process dat comment """
    # Anime/Manga requests that are found go into separate arrays
    animeArray = []
    mangaArray = []
    lnArray = []
    vnArray = []

    # ignores all "code" markup (i.e. anything between backticks)
    comment.body = re.sub(r"\`[{<\[]+(.*?)[}>\]]+\`", "", comment.body)

    num_so_far = 0

    numOfRequest = 0
    numOfExpandedRequest = 0

    # This checks for requests. First up we check all known tags for the !stats request
    if re.search('({!stats.*?}|{{!stats.*?}}|<!stats.*?>|<<!stats.*?>>)', comment.body, re.S) is not None:
        username = USERNAME_PATTERN.search(comment.body)
        subreddit = SUBREDDIT_PATTERN.search(comment.body)

        if username:
            commentReply = CommentBuilder.buildStatsComment(
                username=username.group(1)
            )
        elif subreddit:
            commentReply = CommentBuilder.buildStatsComment(
                subreddit=subreddit.group(1)
            )
        else:
            commentReply = CommentBuilder.buildStatsComment()
    else:

        # The basic algorithm here is:
        # If it's an expanded request, build a reply using the data in the
        # braces, clear the arrays, add the reply to the relevant array and
        # ignore everything else. If it's a normal request, build a reply using
        # the data in the braces, add the reply to the relevant array.

        # Counts the number of expanded results vs total results. If it's not
        # just a single expanded result, they all get turned into normal
        # requests.

        forceNormal = False

        for match in re.finditer('(' + get_expanded_regex('{','}') + ')|(' + get_expanded_regex('<','>') + ')|(' + get_expanded_regex(']','[') + ')|(' + get_expanded_regex('|','|') + ')', comment.body, re.M):
            numOfRequest += 1
            numOfExpandedRequest += 1

        for match in re.finditer('(' + get_regular_regex('{','}') + ')|(' + get_regular_regex('<','>') + ')|(' + get_regular_regex(']','[') + ')|(' + get_regular_regex('|','|') + ')', comment.body, re.M):
            numOfRequest += 1

        if (numOfExpandedRequest >= 1) and (numOfRequest > 1):
            forceNormal = True

        # Determine whether we'll build an expanded reply just once.
        subredditName = str(comment.subreddit).lower()
        isExpanded = (forceNormal or (subredditName in disableexpanded))

        # The final comment reply. We add stuff to this progressively.
        commentReply = ''

        # Expanded Anime
        for match in get_expanded_requests(comment.body, '{', '}'):
            if num_so_far < 30:
                reply = Search.buildAnimeReply(match, isExpanded, comment)

                if (reply is not None):
                    num_so_far = num_so_far + 1
                    animeArray.append(reply)

        # Normal Anime
        for match in get_regular_requests(comment.body, '{', '}'):
            if num_so_far < 30:
                reply = Search.buildAnimeReply(match, False, comment)

                if (reply is not None):
                    num_so_far = num_so_far + 1
                    animeArray.append(reply)

        # Expanded Manga
        # NORMAL EXPANDED
        for match in get_expanded_requests(comment.body, '<', '>'):
            if num_so_far < 30:
                reply = Search.buildMangaReply(match, isExpanded, comment)

                if (reply is not None):
                    num_so_far = num_so_far + 1
                    mangaArray.append(reply)

        # Normal Manga
        # NORMAL
        for match in get_regular_requests(comment.body, '<', '>'):
            if num_so_far < 30:
                reply = Search.buildMangaReply(match, False, comment)

                if (reply is not None):
                    num_so_far = num_so_far + 1
                    mangaArray.append(reply)

        # Expanded LN
        for match in get_expanded_requests(comment.body, ']', '['):
            if num_so_far < 30:
                reply = Search.buildLightNovelReply(match, isExpanded, comment)

                if (reply is not None):
                    num_so_far = num_so_far + 1
                    lnArray.append(reply)

        # Normal LN
        for match in get_regular_requests(comment.body, ']', '['):
            if num_so_far < 30:
                reply = Search.buildLightNovelReply(match, False, comment)

                if (reply is not None):
                    num_so_far = num_so_far + 1
                    lnArray.append(reply)

        # Expanded VN
        for match in get_expanded_requests(comment.body, '|', '|'):
            if num_so_far < 30:
                reply = Search.buildVisualNovelReply(match, isExpanded, comment)

                if (reply is not None):
                    num_so_far = num_so_far + 1
                    vnArray.append(reply)

        # Normal VN
        for match in get_regular_requests(comment.body, '|', '|'):
            if num_so_far < 30:
                reply = Search.buildVisualNovelReply(match, False, comment)

                if (reply is not None):
                    num_so_far = num_so_far + 1
                    vnArray.append(reply)

        # Here is where we create the final reply to be posted

        # Basically just to keep track of people posting the same title
        # multiple times (e.g. {Nisekoi}{Nisekoi}{Nisekoi})
        postedAnimeTitles = []
        postedMangaTitles = []
        postedLNTitles = []
        postedVNTitles = []

        # Adding all the anime to the final comment. If there's manga too we
        # split up all the paragraphs and indent them in Reddit markup by
        # adding a '>', then recombine them
        for i, animeReply in enumerate(animeArray):
            if not (i is 0):
                commentReply += '\n\n'

            if not (animeReply['title'] in postedAnimeTitles):
                postedAnimeTitles.append(animeReply['title'])
                commentReply += animeReply['comment']

        if mangaArray:
            commentReply += '\n\n'

        # Adding all the manga to the final comment
        for i, mangaReply in enumerate(mangaArray):
            if not (i is 0):
                commentReply += '\n\n'

            if not (mangaReply['title'] in postedMangaTitles):
                postedMangaTitles.append(mangaReply['title'])
                commentReply += mangaReply['comment']

        if lnArray:
            commentReply += '\n\n'

        # Adding all the manga to the final comment
        for i, lnReply in enumerate(lnArray):
            if not (i is 0):
                commentReply += '\n\n'

            if not (lnReply['title'] in postedLNTitles):
                postedLNTitles.append(lnReply['title'])
                commentReply += lnReply['comment']

        # Adding all the manga to the final comment
        for i, vnReply in enumerate(vnArray):
            if not (i is 0):
                commentReply += '\n\n'

            if not (vnReply['title'] in postedVNTitles):
                postedVNTitles.append(vnReply['title'])
                commentReply += vnReply['comment']

        # If there are more than 10 requests, shorten them all
        lenRequests = sum(map(len, (animeArray, mangaArray, lnArray, vnArray)))
        if not (commentReply is '') and (lenRequests >= 10):
            commentReply = re.sub(r"\^\((.*?)\)", "", commentReply, flags=re.M)

    # If there was actually something found, add the signature and post the
    # comment to Reddit. Then, add the comment to the "already seen" database.
    if commentReply is not '':

        if num_so_far >= 30:
            commentReply += ("\n\nI'm limited to 30 requests at once and have "
                             "had to cut off some, sorry for the "
                             "inconvinience!\n\n")

        commentReply += Config.getSignature(comment.permalink)

        commentReply += Reference.get_bling(comment.author.name)

        total_expected = int(numOfRequest)
        total_found = sum(map(len, (animeArray, mangaArray, lnArray, vnArray)))

        if total_found != total_expected:
            commentReply += '&#32;|&#32;({0}/{1})'.format(total_found,
                                                          total_expected)

        if is_edit:
            return commentReply
        else:
            try:
                comment.reply(commentReply)
                print("Comment made.\n")
            except praw.errors.Forbidden:
                print('Request from banned '
                      'subreddit: {0}\n'.format(comment.subreddit))
            except Exception:
                traceback.print_exc()

            comment_author = comment.author.name if comment.author else '!UNKNOWN!'

            try:
                DatabaseHandler.addComment(
                    comment.id,
                    comment_author,
                    comment.subreddit,
                    True
                )
            except:
                traceback.print_exc()
    else:
        try:
            if is_edit:
                return None
            else:
                comment_author = comment.author.name if comment.author else '!UNKNOWN!'

                DatabaseHandler.addComment(
                    comment.id,
                    comment_author,
                    comment.subreddit,
                    False
                )
        except:
            traceback.print_exc()


def start():
    """ The main function """
    last_checked_pms = time.time()

    # This opens a constant stream of comments. It will loop until there's a
    # major error (usually this means the Reddit access token needs refreshing)
    comment_stream = praw.helpers.comment_stream(
        reddit,
        SUBREDDITLIST,
        limit=250,
        verbosity=0
    )

    for comment in comment_stream:

        # check if it's time to check the PMs
        if (time.time() - last_checked_pms) > TIME_BETWEEN_PM_CHECKS:
            process_pms()
            last_checked_pms = time.time()

        # Is the comment valid (i.e. it's not made by Roboragi and I haven't
        # seen it already). If no, try to add it to the "already seen pile" and
        # skip to the next comment. If yes, keep going.
        if not (Search.isValidComment(comment, reddit)):
            try:
                if not (DatabaseHandler.commentExists(comment.id)):
                    DatabaseHandler.addComment(
                        comment.id,
                        comment.author.name,
                        comment.subreddit,
                        False
                    )
            except:
                pass
            continue

        process_comment(comment)


# ------------------------------------#
# Here's the stuff that actually gets run

# Initialise Reddit.
setupReddit()

# Loop the comment stream until the Reddit access token expires. Then get a new
# access token and start the stream again.
while 1:
    try:
        start()
    except Exception:
        traceback.print_exc()
        pass

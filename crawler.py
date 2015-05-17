# dom parser
from bs4 import BeautifulSoup as Soup
from Queue import Queue
from log import log
from utils import Utils

import threading
import requests
import json
import re
import pdb
import time
import sys
# import urlparse

class Crawler():

    # contructor
    def __init__(self, options):
        self.log = log
        self.queue = Queue()
        self.utils = Utils(options)
        self.options = options
        self.maxPagePost = self.options["maxPagePost"] if "maxPagePost" in self.options else 10
        self.maxPageThread = self.options["maxPageThread"] if "maxPageThread" in self.options else 10
        self.numberOfSpidies = self.options["numberOfSpidies"] if "numberOfSpidies" in self.options else 2
        self.endLevel = self.options["endLevel"] if "endLevel" in self.options else 3
        self.exception = []
        self.queued = []
        self.started = False

    # push url to queue
    def push_queue(self, obj_push, level, parrent_id=None, parrent_url=None):
        if parrent_url in self.queued:
            return

        if obj_push.get("last") != None and len(obj_push.get("last")) > 0:
            last_page_url = self.utils.prepare_link(obj_push.get("last").get("href"))
            last_page = re.findall("(\d+)\.html", last_page_url)[0]

            # max pages of forum or thread
            if level == 1:
                last_page = int(last_page) if int(last_page) < self.maxPageThread + 1 else self.maxPageThread + 1
            elif level == 2:
                last_page = int(last_page) if int(last_page) < self.maxPagePost + 1 else self.maxPagePost + 1

            for p in range(2, last_page):
                _url = re.sub("(\d+)\.html", str(p) + ".html", last_page_url)
                self.queued.append(_url)
                if self.utils.check_db_link({"level": level, "url": _url}) == None:
                    self.queue.put({ "url": _url, "level": level, "parrent_id": parrent_id })

    # push data to db
    def push_db(self, obj_push, level, parrent_id=None, parrent_url=None):
        if obj_push == None:
            return

        if level == 0:
            # forums
            forum_link = obj_push.get("link")[0]
            forum_url = forum_link.get("href")
            forum_num_thread = obj_push.get("num_threads")[0].getText()
            forum_num_post = obj_push.get("num_posts")[0].getText()

            forum_num_thread = int(forum_num_thread.replace(',','')) if forum_num_thread != '-' else 0
            forum_num_post = int(forum_num_post.replace(',','')) if forum_num_post != '-' else 0

            # check the url format only accept "/" or "http://forums.hardwarezone.com.sg"
            if re.match("^\/|^"+ self.options.get("url"), forum_url) != None:
                forum_url = self.utils.prepare_link(forum_url)
                forum_id = re.findall("(\d+)\/*$", forum_url)[0]
                forum_name = forum_link.getText()

                if self.utils.check_db_id({ "id": forum_id, "level": level }) == None:
                    # push forum to db
                    self.utils.push_forum({
                        "id": forum_id,
                        "url": forum_url,
                        "name": forum_name,
                        "num_threads": forum_num_thread,
                        "num_posts": forum_num_post
                    })
                    self.log("[Push]" + forum_url , ["forum"])

                # push to queue
                if int(level) <= int(self.endLevel):
                    self.queue.put({ "url": forum_url, "level": level + 1, "parrent_id": forum_id })

        elif level == 1:
            # threads
            thread_link = obj_push.get("link")[0]
            thread_author_ctx = obj_push.get("author")[0]
            thread_name = thread_link.getText()
            thread_url = thread_link.get("href")
            thread_author = thread_author_ctx.getText()
            thread_replies = obj_push.get("replies")[0].getText()
            thread_views = obj_push.get("views")[0].getText()

            thread_replies = int(thread_replies.replace(',','')) if thread_replies != '-' else 0
            thread_views = int(thread_views.replace(',','')) if thread_views != '-' else 0

            if len(re.findall("(\d+)\.html", thread_url)) == 0:
                self.log("Thread without id", ["error"])
                return

            thread_id = re.findall("(\d+)\.html", thread_url)[0]
            thread_url = self.utils.prepare_link(thread_url)

            if self.utils.check_db_id({ "id": thread_id, "level": level }) == None:
                # push thread to db
                self.utils.push_thread({
                    "id": thread_id,
                    "name": thread_name,
                    "url": thread_url,
                    "author": thread_author,
                    "forum_id": parrent_id,
                    "replies": thread_replies,
                    "views": thread_views
                })
                self.log("[Push] " + thread_url, ["thread"])

            # push to queue
            if thread_url not in self.exception and int(level) <= int(self.endLevel):
                self.queue.put({ "url": thread_url, "level": level + 1, "parrent_id": thread_id})

            self.push_queue(obj_push, level, parrent_id, parrent_url)

        elif level == 2:
            # post
            post_author = obj_push.get("author")[0].getText()
            post_text = obj_push.get("post")[0].getText()
            post_id = re.findall("([0-9]+)", obj_push.get("post")[0].get("id"))[0]

            if self.utils.check_db_id({ "id": post_id, "level": level }) == None:
                # push thread to db
                self.utils.push_post({
                    "id": post_id,
                    "author": post_author,
                    "text": post_text,
                    "thread_id": parrent_id,
                    "parrent_url": parrent_url
                })
                self.log("[Push] " + post_id, ["post"])

            # push queue
            if int(level) <= int(self.endLevel):
                self.push_queue(obj_push, level, parrent_id, parrent_url)

    # parse html
    def parse_text(self, html, level, parrent_id=None, parrent_url=None):
        queries = self.options.get("levels")[level].get("queries")

        # get context to search
        context = queries.get("context")
        context_html = Soup(html).select(context)

        # read queries
        if len(context_html) > 0:
            for ctx in context_html:
                obj_push = {}
                for query in queries:
                    if query != "context" and query != "last":
                        obj_push[query] = ctx.select(queries[query])
                    elif query == "last" and len(Soup(html).select(queries[query])) > 0:
                        _last = Soup(html).select(queries[query])[len(Soup(html).select(queries[query])) - 1]
                        obj_push[query] = _last
                # push to db
                if obj_push != None and len(obj_push) > 0:
                    self.push_db(obj_push, level, parrent_id, parrent_url)

    # crawl html
    def crawl(self, args=None):

        if args == None:
            args = {}
            args["url"] = self.options.get("url")
            args["level"] = 0
            args["parrent_id"] = None

        # check max level
        if int(args["level"]) > len(self.options.get("levels")) - 1:
            return

        if int(args["level"]) > int(self.endLevel):
            return

        # get html
        req = requests.get(args["url"])

        # check fail
        if req.status_code != 200:
            self.log("[Request][Fail] " + args["url"])
            return

        self.log("[Success] " + args["url"], ["request"])

        # if not fail parse html to object
        self.parse_text(req.text, args["level"], args["parrent_id"], args["url"])

    # worker/spider
    def spidey(self):
        while True:
            item = self.queue.get()
            self.crawl(item)
            self.queue.task_done()

    # summon spiders
    def spawn_spidies(self):
        print "********** Start to crawl **********"

        for s in range(self.numberOfSpidies):
            t = threading.Thread(target=self.spidey)
            t.daemon = True
            t.start()

        self.crawl()
        # block util done every thing
        self.queue.join()

        # done ?
        print "**********  Done   crawl  **********"

if __name__ == '__main__':

    configPath = "parser/forums.hardwarezone.json"
    deepLevel = 2
    startUrl = "http://forums.hardwarezone.com.sg"
    startLevel = 0

    try:
        configPath = sys.argv[1]
    except IndexError:
        print "No config path"

    try:
        deepLevel = sys.argv[2]
    except IndexError:
        print "No end level"

    try:
        startUrl = sys.argv[3]
    except IndexError:
        print "No start url"

    try:
        startLevel = sys.argv[4]
    except IndexError:
        print "No start level"

    with open(configPath) as config_file:
        config_json = json.load(config_file);

    config_json["endLevel"] = deepLevel
    config_json["startUrl"] = startUrl
    config_json["startLevel"] = startLevel

    crl = Crawler(config_json)
    crl.spawn_spidies()

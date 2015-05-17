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
# import urlparse

class Scanner():

    # contructor
    def __init__(self, options):
        self.log = log
        self.queue = Queue()
        self.utils = Utils(options)
        self.options = options
        self.numberOfSpidies = 2
        self.queued = []

    # push url to queue
    def push_queue(self, obj_push, level, parrent_id=None, parrent_url=None):
        if parrent_url in self.queued or level + 1 == self.endLevel:
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
                        "name": forum_name
                    })
                    self.log("[Push]" + forum_url , ["forum"])

                # push to queue
                self.queue.put({ "url": forum_url, "level": level + 1, "parrent_id": forum_id })

        elif level == 1:
            # threads
            thread_link = obj_push.get("link")[0]
            thread_author_ctx = obj_push.get("author")[0]
            thread_name = thread_link.getText()
            thread_url = thread_link.get("href")
            thread_author = thread_author_ctx.getText()

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
                    "forum_id": parrent_id
                })
                self.log("[Push] " + thread_url, ["thread"])

            # push to queue
            if thread_url not in self.exception:
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

    # scan html
    def scan(self, args=None):
        if args == None:
            args = {}
            args["url"] = self.options.get("url")
            args["level"] = 0
            args["parrent_id"] = None

        # check max level
        if args != None and args["level"] > len(self.options.get("levels")) - 1:
            return

        # get html
        req = requests.get(args["url"])

        # check fail
        if req.status_code != 200:
            self.log("[Request][Fail] " + args["url"])
            return []

        self.log("[Success] " + args["url"], ["request"])

        # if not fail parse html to object
        self.parse_text(req.text, args["level"], args["parrent_id"], args["url"])

    # worker/spider
    def spidey(self):
        while True:
            item = self.queue.get()
            self.scan(item)
            self.queue.task_done()

    # summon spiders
    def spawn_spidies(self):
        print "********** Start to scan **********"

        for s in range(self.numberOfSpidies):
            t = threading.Thread(target=self.spidey)
            t.daemon = True
            t.start()

        self.scan()
        # block util done every thing
        self.queue.join()

        # done ?
        print "**********  Done   scan  **********"

if __name__ == '__main__':

    with open('parser/forums.hardwarezone.json') as config_file:
        config_json = json.load(config_file);

    scn = Scanner(config_json)
    scn.spawn_spidies()

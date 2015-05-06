# dom parser
from bs4 import BeautifulSoup as Soup
from Queue import Queue
from threading import Thread
from log import log
from utils import Utils

import requests
import json
import re
import pdb
# import urlparse

class Crawler():

    # contructor
    def __init__(self, options):
        self.log = log
        self.queue = Queue()
        self.utils = Utils(options)
        self.options = options
        self.maxPage = 10
        self.numberOfSpidies = 3
        self.queued = []
        self.exception = [
        ]

    def push_queue(self, obj_push, level, parrent_id=None, parrent_url=None):
        if parrent_url in self.queued:
            return

        if obj_push.get("last") != None and len(obj_push.get("last")) > 0:
            last_page_url = self.utils.prepare_link(obj_push.get("last").get("href"))
            last_page = re.findall("(\d+)\.html", last_page_url)[0]
            last_page = int(last_page) if int(last_page) < self.maxPage + 1 else self.maxPage + 1

            for p in range(2, last_page):
                _url = re.sub("(\d+)\.html", str(p) + ".html", last_page_url)
                self.queued.append(_url)
                if self.utils.check_db_link({"level": level, "url": _url}) == None:
                    self.queue.put(self.crawl(_url, level, parrent_id))

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
                self.queue.put(self.crawl(forum_url, level + 1, forum_id))

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
                self.queue.put(self.crawl(thread_url, level + 1, thread_id))
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

    # crawl html
    def crawl(self, url=None, level=None, parrent_id=None):
        # check max level
        if level > len(self.options.get("levels")) - 1:
            return

        # get html
        if url is None:
            url = self.options.get("url")

        if level is None:
            level = 0

        req = requests.get(url)

        # check fail
        if req.status_code != 200:
            self.log("[Request][Fail] " + url)
            return []

        self.log("[Success] " + url, ["request"])

        # if not fail parse html to object
        self.parse_text(req.text, level, parrent_id, url)

    def spidey(self):
        while True:
            item = self.queue.get()
            do_work(item)
            self.queue.task_done()

    def spawn_spidies(self):
        print "********** Start to crawl **********"

        for spidey in range(self.numberOfSpidies):
            t = Thread(target=spidey)
            t.daemon = True
            t.start()

        self.crawl()
        # block util done every thing
        self.queue.join()

        # done ?
        print "**********  Done   crawl  **********"

from bs4 import BeautifulSoup as Soup

import re
import sqlite3

class Utils():
    def __init__(self, options):
        self.conn = sqlite3.connect("crawl_db", check_same_thread=False)
        self.options = options

    def prepare_link(self, link):
        return self.options.get("url") + link if re.match("^\/", link) != None else link

    def check_db_id(self, obj):
        if obj.get("level") == 0:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM crawl_forum WHERE forum_id=?", (obj.get("id"),))
            return cursor.fetchone()

        elif obj.get("level") == 1:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM crawl_thread WHERE thread_id=?", (obj.get("id"),))
            return cursor.fetchone()

        elif obj.get("level") == 2:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM crawl_post WHERE post_id=?", (obj.get("id"),))
            return cursor.fetchone()

        else:
            return None

    def check_db_link(self, obj):
        if obj.get("level") == 2:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM crawl_post WHERE post_url=?", (obj.get("url"),))
            return cursor.fetchone()

        else:
            return None

    def push_forum(self, forum):
        if forum != None:
            cursor = self.conn.cursor();
            cursor.execute("insert into crawl_forum values(NULL, ?, ?, ?, ?, ?, NULL)",
                (forum["id"], forum["url"], forum["name"], forum["num_threads"], forum["num_posts"]));
            self.conn.commit()

    def push_thread(self, thread):
        if thread != None:
            cursor = self.conn.cursor();
            cursor.execute("insert into crawl_thread values(NULL, ?, ?, ?, ?, ?, ?, ?)",
                (thread["id"], thread["name"], thread["url"], thread["author"], thread["forum_id"], thread["replies"], thread["views"]));
            self.conn.commit()

    def push_post(self, post):
        if post != None:
            cursor = self.conn.cursor();
            cursor.execute("insert into crawl_post values(NULL, ?, ?, ?, NULL, ?, ?)",
                (post["id"], post["author"], post["text"], post["thread_id"], post["parrent_url"]));
            self.conn.commit()

    def get_post(self, obj):
        if obj != None:
            cursor = self.conn.cursor()
            results = []
            #string_to_remove = ["\\n", "\\r", "\\t", "\\f"]
            for row in cursor.execute("SELECT post_id, post_author, post_content FROM crawl_post WHERE thread_id = ?", (obj.get("thread_id"),)):
                '''
                print re.sub('[\r\n]', ' ', row[2])
                tempStr = str(row)
                # remove special character
                for ch in string_to_remove:
                    if ch in tempStr:
                        tempStr = tempStr.replace(ch, ' ')
                # remove non-character character
                tempStr = re.sub('[^a-zA-Z0-9\.\, ]', '', tempStr)
                results.append(tempStr[1:]) #remove u character at begining of string
                '''
                tempList = list(row)
                tempList[2] = re.sub('[\r\n\t\f]', ' ', row[2])
                results.append(tempList)
            return results
        else:
            return None

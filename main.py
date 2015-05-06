import json
from crawler import Crawler

def main():
    # get the parse config file
    with open('parser/forums.hardwarezone.json') as config_file:
        config_json = json.load(config_file);

    # init crawler
    crwl = Crawler(config_json)
    crwl.spawn_spidies()

# run main
main()

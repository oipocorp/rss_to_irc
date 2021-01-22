import feedparser
import time
from pprint import pprint
from operator import itemgetter
import pickle
from dateutil import tz
from time import mktime
from datetime import datetime


def get_item_hash(item):
    return ''.join(list(item.values()))


def time_to_str(published_time):
    return time.strftime('%Y-%m-%d %H:%M:%S %z', published_time)


def format_news_item(item):
    return '{}: {}:\n\t{}\n\t{}\n\n'.format(item['date'], item['label'], item['title'], item['link'])


def load_hash_list():
    try:
        with open('hash_list.pickle', 'rb') as pickle_file:
            return pickle.load(pickle_file)
    except FileNotFoundError:
        return []


def save_hash_list(hash_list):
    with open('hash_list.pickle', 'wb') as pickle_file:
        pickle.dump(hash_list, pickle_file)


def get_news():
    hash_list = load_hash_list()
    agregado = []
    with open('feeds.txt', 'r') as feed_list_file:
        for config in feed_list_file:
            if config.strip():
                label, feed = config.strip('\n').split(';')
                NewsFeed = feedparser.parse(feed)
                for entry in NewsFeed.entries:
                    if entry.published_parsed:
                        item = {'date': time_to_str(entry.published_parsed),
                                'label': label,
                                'title': entry['title'],
                                'link': entry['link']}
                        item_hash = get_item_hash(item)
                        if item_hash not in hash_list:
                            agregado.append(item)
                            hash_list.append(item_hash)

    save_hash_list(hash_list)
    return agregado

# with open('agg_feed.txt', 'w') as agg_feed:
#     for item in sorted(agregado, key=lambda tup: tup['date']):
#         agg_feed.write(format_news_item(item))

try:
    while True:
        for item in sorted(get_news(), key=lambda tup: tup['date']):
           print(format_news_item(item))
        time.sleep(30)
except KeyboardInterrupt:
    pass

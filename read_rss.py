import feedparser
import time
import pickle
import sys
import blessed
from tzlocal import get_localzone
from dateutil import tz
from datetime import datetime
from time import mktime


term = blessed.Terminal()
local_tz = get_localzone()


def get_item_hash(item):
    return ''.join([item['date'], item['label'], item['title'], item['link']])


def time_to_str(published_time):

    utc = datetime(published_time.tm_year,
                   published_time.tm_mon,
                   published_time.tm_mday,
                   published_time.tm_hour,
                   published_time.tm_min,
                   published_time.tm_sec)
    from_zone = tz.tzutc()
    to_zone = tz.tzlocal()
    utc = utc.replace(tzinfo=from_zone)
    local_dt = utc.astimezone(to_zone)
    return str(local_dt)


def format_news_item(item):
    return '{}: {}:\n\t{}\n\t{}\n\n'.format(item['date'],
                                            item['label'],
                                            item['title'],
                                            item['link'])


def print_item(item):
    global term
    print(f"{term.yellow(item['date'])}: {term.yellow(item['label'].upper())}:")
    print(f"\t{term.link(item['link'], item['title'])}\n")


def load_saved_items():
    try:
        with open('saved_items.pickle', 'rb') as pickle_file:
            return pickle.load(pickle_file)
    except FileNotFoundError:
        return {}


def dump_saved_items(saved_items):
    with open('saved_items.pickle', 'wb') as pickle_file:
        pickle.dump(saved_items, pickle_file)


def get_news():
    saved_items = load_saved_items()
    agregado = []
    with open('files/feeds.txt', 'r') as feed_list_file:
        for config in feed_list_file:
            if config.strip():
                label, feed = config.strip('\n').split(';')

                try:
                    news_feed = feedparser.parse(feed)
                except (ConnectionResetError, TimeoutError):
                    print(f"Falha na conexao com {label}")
                    continue

                for news_item in news_feed.entries:
                    if news_item.published_parsed:
                        item = {'date': time_to_str(news_item.published_parsed),
                                'label': label,
                                'title': news_item['title'],
                                'link': news_item['link'],
                                'news_item': news_item}
                        item_hash = get_item_hash(item)
                        if feed not in saved_items:
                            saved_items[feed] = {'hash_list': []}
                        if item_hash not in saved_items[feed]['hash_list']:
                            agregado.append(item)
                            saved_items[feed]['hash_list'].append(item_hash)

    dump_saved_items(saved_items)
    return agregado


def main():
    try:
        while True:
            for item in sorted(get_news(), key=lambda tup: tup['date']):
                print_item(item)
                sys.stdout.flush()
            time.sleep(30)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

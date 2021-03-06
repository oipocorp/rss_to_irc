import feedparser
import time
import pickle
import sys
import blessed
from tzlocal import get_localzone
from dateutil import tz
from datetime import datetime
from urllib.request import Request, urlopen


term = blessed.Terminal()
local_tz = get_localzone()


def get_feed_url(url):
    try:
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        return urlopen(req).read()
    except Exception as e:
        print_log(e)
        return None


def print_log(*arg):
    with open('exec.log', '+a', encoding="utf-8") as log_fd:
        log_fd.write(datetime.now().strftime(r'%Y/%m/%d %H:%M:%S: '))
        for message in arg:
            log_fd.write(str(message).strip('\n')+'\n')


def get_item_hash(item):
    return ''.join([str(item['date']),
                    item['label'],
                    item['title'],
                    item['link']])


def adjust_tz(published_time):

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
    return local_dt


def format_news_item(item):
    return '{}: {}:\n\t{}\n\t{}\n\n'.format(item['date'],
                                            item['label'],
                                            item['title'],
                                            item['link'])


def print_item(item):
    if item['new']:
        global term
        item_str = str(item['date'])+': '+item['label'].upper()+': '
        print(f"{term.yellow(item_str)}")
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


def get_feed(label, url):
    feed = {'label': label, 'url': url, 'news_feed': ''}
    try:
        content = get_feed_url(url)
        if content:
            feed['news_feed'] = feedparser.parse(content)
        else:
            return None
    except (ConnectionResetError, TimeoutError):
        print_log(f"Falha na conexao com {label}")
    return feed


def get_feeds_list():
    with open('files/feeds.txt', 'r') as feed_list_file:
        for config in feed_list_file:
            if config.strip():
                print_log(f'Processando: {config}')
                label, url = config.strip('\n').split(';')
                yield label, url


def get_items_from_feed(feed):
    for news_item in feed['news_feed'].entries:
        if news_item.published_parsed:
            try:
                item = {'date': adjust_tz(news_item.published_parsed),
                        'label': feed['label'],
                        'title': news_item['title'],
                        'link': news_item['link'],
                        'news_item': news_item,
                        'new': False}
            except KeyError as e:
                print_log('Erro em get_news:')
                print_log('news_item', feed['label'], news_item)
                print_log(e)
                continue

            yield item


def get_news():
    saved_items = load_saved_items()
    items_to_save = {}
    agregado = []

    for label, url in get_feeds_list():
        feed = get_feed(label, url)
        if feed:
            for item in get_items_from_feed(feed):
                item_hash = get_item_hash(item)

                if url not in saved_items:
                    item['new'] = True
                elif item_hash not in saved_items[url]['hash_list']:
                    item['new'] = True

                if url not in items_to_save:
                    items_to_save[url] = {'hash_list': []}
                items_to_save[url]['hash_list'].append(item_hash)

                agregado.append(item)

    dump_saved_items(items_to_save)
    print_log('Gerando lista ordenada.')
    return sorted(agregado, key=lambda tup: tup['date'])


def main():
    try:
        while True:
            for item in get_news():
                print_item(item)
                sys.stdout.flush()
            print_log('Aguardando para proximo refresh.')
            time.sleep(30)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

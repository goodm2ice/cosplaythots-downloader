from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import urljoin, urlparse
import requests
import argparse
import re
import os
import signal
import sys


def signal_handler(sig, frame):
    print('\nExiting')
    sys.exit(0)


photo_regex = re.compile(r'(?i)href="([^"]+a\/1280[^"]+?)(?:\s+\d+w)?"')
preload_regex = re.compile(r'(?i)images\/a\/\d+\/([-\d]+)\/([-\d]+)')
def get_photo_urls(url: str) -> list[str]:
    page = requests.get(url)
    bs = BeautifulSoup(page.text, 'html.parser')
    preload = bs.select_one('head link[rel="preload"][href*="images/a"]')
    if preload is None:
        return []
    res = preload_regex.search(str(preload.get('href')))
    if not res:
        return []

    req = {
        'owner_id': res.group(1),
        'album_id': res.group(2),
        'download': 1,
        'offset': 0,
        'limit': 10,
    }
    out = []
    while True:
        res = requests.post('https://cosplaythots.com/cms/load-more-photos.php', json=req)
        if res.status_code != 200:
            raise RuntimeError()
        data = res.json()
        if (not 'photos' in data) or len(data['photos']) <= 0:
            break
        for p in data['photos']:
            res = photo_regex.search(p['html'])
            if res:
                out.append(res.group(1))
        req['offset'] += req['limit'] # Следующая страница

    return list(dict.fromkeys(out))


def prepare_folder_name(text: str) -> str:
    return re.sub(r'\s+', ' ', re.sub(r'[^@#\w\s-]', '', text).strip())


page_title = re.compile(r'(?i)^(.+?(?:\((@.+?)\))?)(?:(?:\s+-)+\s+\d+\s+images|\s+\+18\s+\w+)\s+leaked\s+from.+$')
def parse_title(text: str) -> tuple[str | None, str | None]:
    res = page_title.match(text)
    if not res:
        return (None, None)
    title = prepare_folder_name(res.group(1))
    username = prepare_folder_name(res.group(2))

    return (title, username)


def list_entity(url: str, base_path: Path | None, prefix='', n: int | None = None):
    if not '/p/' in url:
        raise ValueError('URL is not entity')
    print(f'{prefix}[Entity{"" if n is None else f" {n}"}]: {url}')
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'html.parser')

    title = ' - '.join([tag.get_text() for tag in soup.select_one('body > div > center').select('a.btn')])
    print(f'{prefix}\tTitle: {title}')

    path = (base_path or Path.cwd()).absolute().joinpath(prepare_folder_name(title))
    path.mkdir(parents=True, exist_ok=True)

    urls = get_photo_urls(url)
    print(f'{prefix}\tFound images: {len(urls)}')
    if len(urls) > 0:
        print(f'{prefix}\tDownloading', end='')
    for photo_url in urls:
        try:
            filename = os.path.basename(urlparse(photo_url).path)
            data = requests.get(urljoin(url, photo_url)).content
            with open(path.joinpath(filename), 'wb') as f:
                f.write(data)
            print('.', end='')
        except:
            print('!', end='')
    print('Done!')


def list_page(url: str, n: int):
    page = requests.get(f'{url}?page={n}')
    soup = BeautifulSoup(page.text, 'html.parser')
    return [str(url.get('href')) for url in soup.select('.grid > .grid-item[onclick] a[href^="/p/"]')]


def list_category(url: str, args: argparse.Namespace):
    if not '/f/' in url and not '/m/' in url and not '/c/' in url:
        raise ValueError('URL is not category')
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'html.parser')

    title, username = parse_title(soup.title.string or soup.find('title').text)

    path = (args.output or Path.cwd()).absolute().joinpath(title)
    path.mkdir(parents=True, exist_ok=True)

    urls = []
    page = 1
    last_count = 0
    while True:
        last_count = len(urls)
        urls.extend(list_page(url, page))
        page+=1
        if len(urls) - last_count < 10:
            break # Если последняя страница выходим

    urls = list(dict.fromkeys(urls)) # Удаляем возможные повторения
    urls = urls[args.skip:args.skip + args.count]

    print(f'\tFound entites: {len(urls)}')

    for i, entity_url in enumerate(urls):
        try:
            list_entity(urljoin(url, entity_url), path, '\t', i)
        except ValueError:
            pass


def main():
    signal.signal(signal.SIGINT, signal_handler)

    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--output', type=Path, default=None, help='Директория для загрузки')
    parser.add_argument('-s', '--skip', type=int, default=0, help='Пропуск указанного колличества категорий')
    parser.add_argument('-c', '--count', type=int, default=100, help='Число загружаемых категорий (не более указанного)')
    parser.add_argument('urls', nargs='+')
    args = parser.parse_args()
    print(f'Skip: {args.skip}')
    print(f'Count: {args.count}')
    for url in args.urls:
        print(f'[URL]: {url}')
        try:
            list_category(url, args)
        except ValueError:
            print('\tNot a category! Trying entity...')
            try:
                list_entity(url, args.output)
            except ValueError:
                print('\tNot an entity, skip!')
            except BaseException as e:
                print(f'\tError: {e}')
        except BaseException as e:
            print(f'\tError: {e}')


if __name__ == '__main__':
    main()

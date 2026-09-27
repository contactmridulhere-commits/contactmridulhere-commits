"""Refresh the "Latest from the channel" block in README.md from the YouTube RSS feed.

Uses the channel's long-form uploads playlist (UULF...) so Shorts don't crowd the row.
Standard library only. If the feed can't be fetched or parsed, README.md is left untouched.
"""
import html
import pathlib
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET

CHANNEL_ID = 'UCSW2N1gM2P8K7g-jmNEJigg'
FEED = f'https://www.youtube.com/feeds/videos.xml?playlist_id=UULF{CHANNEL_ID[2:]}'
COUNT = 3
README = pathlib.Path(__file__).resolve().parent.parent / 'README.md'
START, END = '<!-- VIDEOS:START -->', '<!-- VIDEOS:END -->'
NS = {'a': 'http://www.w3.org/2005/Atom', 'yt': 'http://www.youtube.com/xml/schemas/2015'}
UA = {'User-Agent': 'Mozilla/5.0 (profile-readme-updater)'}


def fetch(url, method='GET'):
    req = urllib.request.Request(url, headers=UA, method=method)
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.status, (r.read() if method == 'GET' else b'')


def thumb(video_id):
    """Prefer the 1280x720 thumbnail; fall back to 320x180, which every video has."""
    hi = f'https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg'
    try:
        status, _ = fetch(hi, 'HEAD')
        if status == 200:
            return hi
    except Exception:
        pass
    return f'https://i.ytimg.com/vi/{video_id}/mqdefault.jpg'


def main():
    try:
        _, body = fetch(FEED)
        entries = ET.fromstring(body).findall('a:entry', NS)[:COUNT]
    except Exception as exc:  # network hiccup or YouTube blocking the runner: keep the current README
        print(f'feed unavailable, leaving README as is: {exc}')
        return 0
    if not entries:
        print('feed returned no videos, leaving README as is')
        return 0

    links = []
    for e in entries:
        vid = e.find('yt:videoId', NS).text
        title = html.escape(e.find('a:title', NS).text.strip(), quote=True)
        links.append(f'  <a href="https://www.youtube.com/watch?v={vid}"><img src="{thumb(vid)}" width="32%" alt="{title}" title="{title}"></a>')
    block = f'{START}\n<p align="center">\n' + '\n'.join(links) + f'\n</p>\n{END}'

    text = README.read_text(encoding='utf-8')
    new = re.sub(re.escape(START) + r'.*?' + re.escape(END), lambda _: block, text, flags=re.S)
    if new != text:
        README.write_text(new, encoding='utf-8')
        print('README updated')
    else:
        print('no change')
    return 0


if __name__ == '__main__':
    sys.exit(main())

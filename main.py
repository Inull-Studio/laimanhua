from concurrent.futures import ThreadPoolExecutor, Future
from hashlib import md5
from shutil import move
from urllib.parse import urljoin, urlsplit
from bs4 import BeautifulSoup
import requests, sys, tempfile, time, os, json


class Laimanhua:
    location = os.path.join(os.path.dirname(sys.argv[0]), 'downloads')
    proxies = {}
    url = 'https://m.laimanhua8.com/'
    picurl = 'https://mhpicwwt.kingwar.cn/'
    searchurl = 'https://m.laimanhua8.com/e/search/'

    header = {'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0'}
    picheader = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0',
        'Referer': url}
    searchheader = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0',
        'Origin': url}

    def __init__(self, search_kw: str) -> None:
        if not os.path.exists(self.location):
            os.mkdir(self.location)
        self.kw = search_kw

    def search(self, keyword: str) -> list[dict]:
        print('正在搜索', keyword)
        self.searchheader['Referer'] = 'https://m.laimanhua8.com/e/search/result/?searchid=' + md5(keyword.encode()).hexdigest().upper()
        r = requests.post(self.searchurl, data={'key': keyword.encode('gbk')}, headers=self.searchheader, proxies=self.proxies)
        r.encoding = 'gb2312'
        soup = BeautifulSoup(r.text, 'html.parser')
        ul = soup.find('ul', id='detail')
        li = ul.find_all('li')
        result: list[dict] = []
        for dt in li:
            result.append({dt.h3.string: urljoin(self.url, dt.a['href'])})
        return result

    def parse_chapter(self, comic_url: str, comicname: str) -> list[dict]:
        r = requests.get(comic_url, headers=self.header, proxies=self.proxies)
        r.encoding = 'gb2312'
        soup = BeautifulSoup(r.text, 'html.parser')
        div = soup.find('div', id='chapterList')
        result: list[dict] = []
        for a in div.find_all('a'):
            result.append({a.string: urljoin(self.url, a['href'])})
        return result

    def get_pic(self, chapter: dict[str, str]) -> list[str]:
        chaptername, url = chapter.copy().popitem()
        self.chapterlocate = os.path.join(self.location, chaptername)
        if not os.path.exists(self.chapterlocate):
            os.mkdir(self.chapterlocate)

        r = requests.get(url, headers=self.header)
        r.encoding = 'gb2312'
        soup = BeautifulSoup(r.text, 'html.parser')
        scripts = soup.find_all('script')
        info = scripts[6].string.split('{')[1].split('}')[0]
        info = json.loads('{' + info + '}')
        picurls = []
        for u in info['images']:
            picurl = urljoin(urljoin(self.picurl, info['path']), u)
            picurls.append(picurl)
        return picurls

    def download(self, picurl: str) -> None:
        piclocate = os.path.join(self.chapterlocate, picurl.split('/')[-1].strip())
        if os.path.exists(piclocate):
            return
        r = requests.get(picurl, headers=self.picheader)
        tmpf = tempfile.NamedTemporaryFile('wb', delete=False)
        tmpf.write(r.content)
        tmpf.close()
        move(tmpf.name, piclocate)

    def start(self):
        result = self.search(self.kw)
        for i in range(len(result)):
            print('{:<2}: {}'.format(i+1, result[i].copy().popitem()[0]))
        print('\n如果未找到您所需的漫画，请提供更多搜索关键字来提升精确度!')
        index = int(input('请输入您要下载的漫画id:'))
        time.sleep(1)

        comicurl, comicname = result[index - 1].popitem()
        chapter_urls = self.parse_chapter(comicurl, comicname)
        time.sleep(1)
        for chapter in chapter_urls:
            results: list[Future] = []
            pics = self.get_pic(chapter)
            chaptername, _ = chapter.popitem()
            time.sleep(0.5)
            with ThreadPoolExecutor(4) as execute:
                for pic in pics:
                    res = execute.submit(self.download, pic)
                    results.append(res)
                for r in results:
                    print('正在下载{}...'.format(chaptername), end='\r')
                    r.result()
            print()
        print('下载完成!')
        sys.exit(0)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('usage:', sys.argv[0], '<keyword> [proxy]')
        sys.exit(0)

    manhua = Laimanhua(sys.argv[1])
    if len(sys.argv) > 2:
        manhua.proxies['http'] = sys.argv[2].strip()
        manhua.proxies['https'] = sys.argv[2].strip()
    manhua.start()
from hashlib import md5
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import requests, base64, sys, tempfile

class Laimanhua:
    url = 'https://www.laimanhua8.com/'
    picurl = 'https://mhpicwwt.kingwar.cn/'
    searchurl = 'https://www.laimanhua8.com/cse1/search/'

    header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0'}
    picheader = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0',
        'Referer': url}
    searchheader = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0',
        'Origin': 'https://www.laimanhua8.com'}

    def __init__(self, search_kw: str) -> None:
        result = self.search(search_kw)
        for i in range(len(result)):
            print('{:<2}: {}'.format(i+1, result[i].copy().popitem()[0]))
        print('\n如果未找到您所需的漫画，请提供更多搜索关键字来提升精确度!')
        index = int(input('请输入您要下载的漫画id:'))

        chapter_urls = self.parse_chapter(result[index - 1].popitem()[1])
        for chapter in chapter_urls:
            self.get_pic(chapter)

    def search(self, keyword: str) -> list[dict]:
        print('正在搜索', keyword)
        self.searchheader['Referer'] = 'https://www.laimanhua8.com/ee/search/result/?searchid=' + md5(keyword.encode()).hexdigest().upper()
        r = requests.post(self.searchurl, data={'key': keyword.encode('gbk')}, headers=self.searchheader)
        r.encoding = 'gb2312'
        soup = BeautifulSoup(r.text, 'html.parser')
        div = soup.find('div', id='dmList')
        li = div.find_all('li')
        result: list[dict] = []
        for dt in li:
            result.append({dt.dt.a['title']: urljoin(self.url, dt.dt.a['href'])})
        return result

    def parse_chapter(self, comic_url: str) -> list[dict]:
        r = requests.get(comic_url, headers=self.header)
        r.encoding = 'gb2312'
        soup = BeautifulSoup(r.text, 'html.parser')
        div = soup.find('div', id='play_0')
        result: list[dict] = []
        for a in div.find_all('a'):
            result.append({a['title']: urljoin(self.url, a['href'])})
        return result

    def get_pic(self, chapter: dict) -> list:
        pass

    def download(self, picurl: str, name: str) -> None:
        pass

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('usage:', sys.argv[0], '<keyword>')
        sys.exit(0)
    manhua = Laimanhua(sys.argv[1])
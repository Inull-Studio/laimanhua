import base64
import os
import random
import re
import sys
import tempfile
from concurrent.futures import Future, ThreadPoolExecutor
from shutil import move
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from rich.progress import track


class Laimanhua:
    location = os.path.join(os.path.dirname(sys.argv[0]), "downloads")
    proxies = {}
    url = "https://www.laimanhua88.com"
    picurls = [
        "https://xwdf.kingwar.cn",
        "https://mhreswhm.kingwar.cn",
        "https://qwe123.kingwar.cn",
        "https://resmhpic.kingwar.cn",
        "https://reszxc.kingwar.cn",
        "https://mhpic5eer.kingwar.cn",
        "https://mhpic7ffr.tgmhfc.uk",
    ]
    picurl = random.choice(picurls)
    searchurl = "https://www.laimanhua88.com/s81/search/"

    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:140.0) Gecko/20100101 Firefox/140.0"
    }
    picheader = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0",
        "Referer": "https://laimanhua88.com/",
    }
    searchheader = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0",
        "Origin": url,
    }

    def __init__(self, search_kw: str) -> None:
        if not os.path.exists(self.location):
            os.mkdir(self.location)
        self.kw = search_kw

    def post(self, url, **kwargs):
        if self.proxies:
            kwargs["proxies"] = self.proxies
        # print(kwargs)
        return requests.post(url, **kwargs)

    def get(self, url, **kwargs):
        if self.proxies:
            kwargs["proxies"] = self.proxies
        # print(kwargs)
        return requests.get(url, **kwargs)

    def search(self) -> list[dict]:
        print("正在搜索", self.kw)
        self.searchheader["Referer"] = "https://www.laimanhua88.com/"
        r = self.post(
            self.searchurl,
            data={"key": self.kw.encode("gbk")},
            headers=self.searchheader,
        )
        r.encoding = "gb2312"
        soup = BeautifulSoup(r.text, "html.parser")
        ul = soup.find("div", class_="dmList").ul
        li = ul.find_all("li")
        result: list[dict] = []
        for dt in li:
            result.append({dt.dt.a.string: urljoin(self.url, dt.dt.a["href"])})
        return result

    def parse_chapter(self, comic_url: str, comicname: str) -> list[dict]:
        self.comiclocate = os.path.join(self.location, comicname)
        if not os.path.exists(self.comiclocate):
            os.mkdir(self.comiclocate)

        r = self.get(comic_url, headers=self.header)
        r.encoding = "gb2312"
        soup = BeautifulSoup(r.text, "html.parser")
        ul = soup.find("div", id="play_0").ul
        result: list[dict] = []
        for a in ul.find_all("a"):
            result.append({a.get_text(): urljoin(self.url, a["href"])})
        return result

    def get_pic(self, chapter: dict[str, str]) -> list[str]:
        chaptername, url = chapter.copy().popitem()
        self.chapterlocate = os.path.join(self.comiclocate, chaptername)
        if not os.path.exists(self.chapterlocate):
            os.mkdir(self.chapterlocate)

        r = self.get(url, headers=self.header)
        r.encoding = "gb2312"
        soup = BeautifulSoup(r.text, "html.parser")
        scripts = soup.find_all("script")
        script = re.search("var picTree ='(.*)';", str(scripts))
        if script:
            pics = (
                base64.b64decode(script.group(1)).decode("utf8").split("$qingtiandy$")
            )
        # info = scripts[6].string.split("{")[1].split("}")[0]
        # info = json.loads("{" + info + "}")
        picurls = []
        for uri in pics:
            picurl = urljoin(self.picurl, uri)
            picurls.append(picurl)
        return picurls

    def download(self, picurl: str) -> None:
        piclocate = os.path.join(self.chapterlocate, picurl.split("/")[-1].strip())
        if os.path.exists(piclocate):
            return
        r = self.get(picurl, headers=self.picheader)
        tmpf = tempfile.NamedTemporaryFile("wb", delete=False)
        tmpf.write(r.content)
        tmpf.close()
        move(tmpf.name, piclocate)

    def start(self):
        result = self.search()
        for i in range(len(result)):
            print("{:<2}: {}".format(i + 1, result[i].copy().popitem()[0]))
        print("\n如果未找到您所需的漫画，请提供更多搜索关键字来提升精确度!")
        if len(result) != 1:
            index = int(input("请输入您要下载的漫画id:"))
        else:
            index = 1

        comicname, comicurl = result[index - 1].popitem()
        chapter_urls = self.parse_chapter(comicurl, comicname)
        for chapter in chapter_urls:
            results: list[Future] = []
            pics = self.get_pic(chapter)
            chaptername, _ = chapter.popitem()
            with ThreadPoolExecutor(8) as execute:
                for pic in pics:
                    res = execute.submit(self.download, pic)
                    results.append(res)
                for r in track(
                    results, description="正在下载{}...".format(chaptername)
                ):
                    r.result()
        print("下载完成!")
        sys.exit(0)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage:", sys.argv[0], "<keyword> [proxy]")
        sys.exit(0)

    manhua = Laimanhua(sys.argv[1])
    if len(sys.argv) > 2:
        manhua.proxies["http"] = sys.argv[2].strip()
        manhua.proxies["https"] = sys.argv[2].strip()
    manhua.start()

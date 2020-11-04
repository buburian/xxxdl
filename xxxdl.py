# 先拿掉youtube, 其他候補

import re
import requests
from datetime import datetime
import sys
import os
import argparse
import shutil
import m3u8
import json
from urllib.parse import urlparse
from tqdm import tqdm
from lxml import html, etree
from pathlib import Path
import random
from pytube import YouTube, exceptions
import js2py
import base64

project_name = "XXX 下載器"
version = "2.0a"


class MyParser(argparse.ArgumentParser):
    def error(self, message):
        if message == 'the following arguments are required: video_page_url':
            message = "缺少 影片連結 參數"
        sys.stderr.write('錯誤: %s\n' % message)
        self.print_help()
        sys.exit(2)


class XxxDownloader:
    def __init__(self):
        self.__support_host = [
            # {'host': ['twitter.com'], 'func': lambda: self.__do_twitter()},
            {'host': ['xvideos.com'],
                'func': lambda: self.__do_xtubetype('xvideos')},
            {'host': ['xtube.com'], 'func': lambda: self.__do_xtubetype(
                'xtube')},  # 2020 fixed
            {'host': ['pornhub.com'],
                'func': lambda: self.__do_pornhubtype()},  # 2020 fixed
            {'host': ['redtube.com'], 'func': lambda: self.__do_xtubetype(
                'redtube')},
            {'host': ['tube8.com'],
                'func': lambda: self.__do_xtubetype('tube8')},
            # {'host': ['playvids.com'], 'func': lambda: self.__do_vidstype()},
            # {'host': ['peekvids.com'], 'func': lambda: self.__do_vidstype()},
            # {'host': ['youtube.com'],'func': lambda: self.__do_youtube()},  # 2020 fixed
            # {'host': ['vimeo.com', 'player.vimeo.com'],'func': lambda: self.__do_vimeo()}
        ]

        self.__urlcheck_pattern = re.compile(
            r"^https?:\/\/(?:www|cn|player\.)?([^\/]+)\/?", re.IGNORECASE)

        self.__header = {
            'User-Agent': 'Mozilla/5.0 (iPad; U; CPU OS 3_2_1 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Mobile/7B405',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-TW,zh;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate'
        }

        self.__pattern = dict(xvideos=dict(pattern_video=r"html5player\.setVideoUrlHigh\('([^']*)'\);",
                                           pattern_video_title=r"html5player\.setVideoTitle\('([^']*)'\);",
                                           pattern_file_ext=r"(?:.*)\/videos\/([^/]*)\/(?:.*)"),
                              xtube=dict(pattern_video=r'{\s?defaultQuality:\s?(?:[^"]*),\s?format:\s?["]?(\w*)["]?,\s?quality:\s?["]?(\d*)["]?,\s?videoUrl:\s?"([^"]*)"\s?}',
                                         pattern_video_title=r'<h1>([^</>]*)</h1>',
                                         pattern_file_ext=None),
                              pornhub=dict(pattern_video=r'defaultQuality["]?:(?:\w*),["]?format["]?:["]?(\w*)["]?,'
                                                         r'["]?quality["]?:["]?(\d*)["]?,["]?videoUrl["]?:"([^"]*)"}',
                                           pattern_video_title=r'<meta property="og:title" content="([^"]*)"',
                                           pattern_file_ext=None),
                              redtube=dict(pattern_video=r'defaultQuality["]?:(?:\w*),["]?format["]?:["]?(\w*)["]?,'
                                                         r'["]?quality["]?:["]?(\d*)["]?,["]?videoUrl["]?:"([^"]*)"}',
                                           pattern_video_title=r'<h1 class="video_title">([^"]*)<\/h1>',
                                           pattern_file_ext=None),
                              tube8=dict(pattern_video=r'defaultQuality["]?:(?:\w*),["]?format["]?:["]?(\w*)["]?,'
                                                       r'["]?quality["]?:["]?(\d*)["]?,["]?videoUrl["]?:"([^"]*)"}',
                                         pattern_video_title=r'<h1>\n(.*)<\/h1>',
                                         pattern_file_ext=None)
                              )
        self.__session = requests.session()
        self.__showlog_flag = True
        self.__req = None
        self.__video_title = None
        self.__url = None
        self.__random_user_agent()

    def __random_user_agent(self):
        ua = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/60.0.3112.113 Safari/537.36',
            'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/69.0.3497.100 Safari/537.36',
            'Mozilla/5.0 (Linux; Android 6.0.1; SM-G532G Build/MMB29T) AppleWebKit/537.36 '
            '(KHTML, like Gecko) Chrome/63.0.3239.83 Mobile Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/69.0.3497.100 Safari/537.36'
            'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0',
            'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:18.0) Gecko/20100101 Firefox/18.0',
            'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:44.0) Gecko/20100101 Firefox/44.0',
            'Mozilla/5.0 (Windows NT 5.1; rv:7.0.1) Gecko/20100101 Firefox/7.0.1',
            'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko',
            'Mozilla/4.0 (compatible; MSIE 9.0; Windows NT 6.1)',
            'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.0.3705)',
            'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)',
            'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome'
            '/46.0.2490.80 Safari/537.36'
        ]

        self.__header['User-Agent'] = ua[random.randint(0, len(ua)-1)]

    def internet_on(self):
        try:
            self.__session.get('http://216.58.192.142', timeout=2)
            return True
        except Exception:
            return False

    def get_support_host(self):
        return [x['host'][0] for x in self.__support_host]

    def set_quite(self):
        self.__showlog_flag = False

    def log(self, strings):
        if self.__showlog_flag:
            print("{}\n".format(strings))

    def __connect(self, url=None, headers=None, timeout=3, stream=False):
        try:
            if not url:
                url = self.__url
            if not headers:
                headers = self.__header

            req = self.__session.get(
                url, headers=headers, timeout=timeout, stream=stream)
            if int(req.status_code) in [404, 500, 429]:
                self.log("網頁找不到或是網頁發生錯誤。錯誤碼 {0}".format(int(req.status_code)))
                return False
            return req
        except:
            self.log("網站連線超時，請檢查網路狀況")
            return False

    def __download_from_url(self, mp4_url, file_save_to):

        file_save_to = "".join(
            [letter for letter in file_save_to if letter not in "\/*"])

        """
        @param: url to download file
        @param: dst place to put the file
        備註起來的是續傳
        先關閉
        """
        try:
            file_size = int(self.__session.head(
                mp4_url).headers["Content-Length"])
            # if os.path.exists(dst):
            #     first_byte = os.path.getsize(dst)
            # else:
            #     first_byte = 0
            # if first_byte >= file_size:
            #     return file_size
            # header = {"Range": "bytes=%s-%s" % (first_byte, file_size)}
            if self.__showlog_flag:
                pbar = tqdm(desc="[{0}] ".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                            total=file_size, initial=0, unit='B', unit_scale=True, ascii=True,
                            postfix="下載成 {0}".format(file_save_to), ncols=80,
                            bar_format='{desc} {percentage:3.0f}% [ETA {remaining}][{rate_fmt}] {postfix}')
            req = self.__connect(url=mp4_url, stream=True, timeout=30)
            with(open(file_save_to, 'wb')) as f:
                for chunk in req.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
                        if self.__showlog_flag:
                            pbar.update(len(chunk))
            if self.__showlog_flag:
                pbar.close()
            self.log("{0} 下載成功 -> {1}".format(mp4_url, file_save_to))
            return file_size
        except Exception:
            self.log("{0} 下載失敗".format(mp4_url))
            return False

    def checkifcanClaw(self, url):
        for s in self.__support_host:
            if re.compile(r"^https?:\/\/(.*)?{}".format(s['host'][0]), re.IGNORECASE).match(url):
                return True
            else:
                return False

    def claw(self, url):
        self.__url = url.strip()
        for s in self.__support_host:
            if re.compile(r"^https?:\/\/(.*)?{}".format(s['host'][0]), re.IGNORECASE).match(self.__url):
                return s['func']()
        else:
            self.log("網址可能不是支援的網站, 目前僅支援 {0}".format(
                ", ".join([i['host'][0] for i in self.__support_host])))
            return False

    def __do_pornhubtype(self):
        req = self.__connect()
        html = etree.HTML(req.content)
        self.log("開始分析影片")
        if "pornhub.com/embed/" in self.__url:
            self.log("這網址不是影片頁面，不能使用內嵌頁面")
            return False
        video_title = "".join(html.xpath("//h1//text()")).strip()
        js_temp = html.xpath("//script/text()")

        for j in js_temp:
            if "flashvars" in j:
                mp4_url = self.__exeJs(j)
                self.log("影片真實路徑可能是 {0}".format(mp4_url))
                break
        req = self.__connect(url=mp4_url, stream=True,
                             timeout=10)  # 影片格式改成跟主機問
        regular_express = req.headers.get("Content-Type").split("/")
        if len(regular_express) == 0 or regular_express[1] == "":
            self.log("影片格式抓取有誤，請聯絡程式作者")
            return False
        file_ext = regular_express[1]

        self.log("影片標題是 {0}".format(video_title))
        file_save_to = "{0}.{1}".format(video_title, file_ext)  # 現在檔名都是影片標題
        return self.__download_from_url(mp4_url, file_save_to)  # 檔名用標頭

    def __do_xtubetype(self, pattern_name):
        req = self.__connect()
        req_text = str(req.text)

        self.log("開始分析影片")

        regular_express = re.findall(
            self.__pattern[pattern_name]['pattern_video'], req_text)
        if len(regular_express) == 0 or regular_express[0] == "":
            self.log("這網址不是影片頁面，或是要會員才可以看的影片，請檢查之後再試一次")
            return False

        if pattern_name in ['xtube', 'redtube', 'tube8']:
            maxRate = 0
            for mediaDefinition in regular_express:
                if mediaDefinition[2] == "":
                    continue
                if int(mediaDefinition[1]) > maxRate:
                    maxRate = int(mediaDefinition[1])
                    mp4_url = mediaDefinition[2]
                    file_ext = mediaDefinition[0]

            mp4_url = mp4_url.replace("\\", "").strip()
            if file_ext == "":
                # 如果json沒有，就從filename抓
                if len(os.path.basename(urlparse(mp4_url).path).split(".")) == 2:
                    file_ext = os.path.basename(
                        urlparse(mp4_url).path).split(".")[1]
                else:
                    # filename也沒有就只好跟server問
                    req = self.__connect(
                        url=mp4_url, stream=True, timeout=10)  # 影片格式改成跟主機問
                    regular_express = req.headers.get(
                        "Content-Type").split("/")
                    if len(regular_express) == 0 or regular_express[1] == "":
                        self.log("影片格式抓取有誤，請聯絡程式作者")
                        return False
                    file_ext = regular_express[1]
        else:  # xvideos
            mp4_url = regular_express[0].strip()

            # regular_express = re.findall(self.__pattern[pattern_name]['pattern_file_ext'], mp4_url) # xvideo的檔案副檔名在真實網址裡面。不在source html
            # if len(regular_express) == 0 or regular_express[0] == "":
            #     self.log("影片格式抓取有誤，請聯絡程式作者")
            #     return False
            # file_ext = regular_express[0]

            req = self.__connect(url=mp4_url, stream=True,
                                 timeout=10)  # 影片格式改成跟主機問
            regular_express = req.headers.get("Content-Type").split("/")
            if len(regular_express) == 0 or regular_express[1] == "":
                self.log("影片格式抓取有誤，請聯絡程式作者")
                return False
            file_ext = regular_express[1]

        self.log("影片真實路徑可能是 {0}".format(mp4_url))

        regular_express = re.findall(
            self.__pattern[pattern_name]['pattern_video_title'], req_text)
        if len(regular_express) == 0 or regular_express[0] == "":
            self.log("影片標題抓取有誤，請聯絡程式作者")
            return False

        video_title = regular_express[0].strip()
        self.log("影片標題是 {0}".format(video_title))
        file_save_to = "{0}.{1}".format(video_title, file_ext)  # 現在檔名都是影片標題
        return self.__download_from_url(mp4_url, file_save_to)  # 檔名用標頭


    
    def __exeJs(self, js):
        flashvars = re.findall(r"flashvars_\d+", js)[0]
        js = "\n".join(js.split("\n\t")[:-5]).strip()
        res = js2py.eval_js(js + flashvars)

        if res.quality_720p:
            return res.quality_720p
        elif res.quality_480p:
            return res.quality_480p
        elif res.quality_240p:
            return res.quality_240p
        else:
            self.log("parse url error")


if __name__ == '__main__':

    xx = XxxDownloader()
    support_hosts = ""
    for i, x in enumerate(xx.get_support_host(), 1):
        if i % 3 == 0:
            support_hosts = "{0}{1}".format(support_hosts, x)
            support_hosts = "{0}\n".format(support_hosts)
        else:
            support_hosts = "{0}{1}\t".format(support_hosts, x)

    support_hosts = support_hosts[:-1]
    parser = MyParser(prog="XXXDL", epilog="目前支援有公開連結的網站，包括\n--------------"
                      "--------------------\n{0}\n\n\t\t\t\t\t\tW.S.Y"
                      " 2020 \n（其餘影音平台之後補上）\n".format(support_hosts),
                      formatter_class=argparse.RawTextHelpFormatter)

    # parser.add_argument('video_page_url', help="影片連結", required=False)

    group = parser.add_mutually_exclusive_group()
    group.add_argument('-g', dest='singleUrl', help="單一影片連結")
    group.add_argument('-a', dest='url',
                       help='加入連結', default=False)
    group.add_argument('-c', dest='clearflag',  help='清除列表',
                       action="store_true", default=False)
    group.add_argument('-l', dest='listflag', help='顯示列表',
                       action="store_true", default=False)
    group.add_argument('-s', dest='startrun', help='開始批次抓取',
                       action="store_true", default=False)

    parser.add_argument('-q', help='關閉系統訊息', action="store_true")
    parser.add_argument('-v', help="顯示程式版本", action="store_true")

    args = parser.parse_args()

    if args.q:
        xx.set_quite()
    if args.v:
        sys.stderr.write('{0} {1}\n'.format(project_name, version))
        exit(0)

    if not xx.internet_on():
        sys.stderr.write('錯誤: %s\n' % "網路尚未連線。無法在離線狀況下使用")
        sys.exit(2)

    if not args.singleUrl:
        if not os.path.exists("db.lst"):
            Path('db.lst').touch()

        if args.url:
            if xx.checkifcanClaw(args.url):
                with open("db.lst", "r") as f:
                    data = f.readline()
                with open("db.lst", "w") as f:
                    if data == "":
                        data = set()
                    else:
                        data = set(json.loads(data))

                    data.add(args.url)
                    f.write(json.dumps(list(data)))
                sys.stderr.write('網址: %s 加入成功\n' % args.url)
            else:
                sys.stderr.write('錯誤: %s\n' % "網址格式有錯")

        elif args.listflag:
            with open("db.lst", "r") as f:
                data = f.readline()
            if data == "":
                data = set()
            else:
                data = set(json.loads(data))

            sys.stderr.write('目前待抓取網址有:\n')
            for u in data:
                sys.stderr.write('%s\n' % u)

        elif args.clearflag:
            yn = input("確定清除所有待抓取網址? (Y/n) ")
            if yn == "Y" or yn == "y" or yn == "Yes" or yn == "yes":
                with open("db.lst", "w") as f:
                    f.write("")
                sys.stderr.write('已經清除\n')
            else:
                sys.stderr.write('使用者取消\n')

        elif args.startrun:
            with open("db.lst", "r") as f:
                data = f.readline()
            if data == "":
                data = set()
            else:
                data = set(json.loads(data))

            for u in data.copy():
                sys.stderr.write('開始抓取: %s\n' % u)
                if not xx.claw(u):
                    sys.stderr.write('抓取: %s 失敗\n' % u)
                data.remove(u)
                with open("db.lst", "w") as f:
                    f.write(json.dumps(list(data)))

        else:
            sys.stderr.write(
                'usage: XXXDL [-h] [-g SINGLEURL | -a URL | -c | -l | -s] [-q] [-v]\n')
    else:
        # 直接抓取
        if not all([urlparse(args.singleUrl).scheme, urlparse(args.singleUrl).netloc,
                    urlparse(args.singleUrl).path]):
            sys.stderr.write('錯誤: %s\n' % "網址格式有錯")
            sys.exit(2)

        if not xx.claw(args.singleUrl):
            sys.exit(2)

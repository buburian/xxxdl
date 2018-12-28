import re, requests, datetime,sys,os,argparse,shutil,m3u8,json
from urllib.parse import urlparse
from tqdm import tqdm
from lxml import html
from pathlib import Path
import random, base64
from pytube import YouTube, exceptions


project_name = "XXX下載器"
version = "1.6b"


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
            {'host': ['twitter.com'],     'func': lambda: self.__do_twitter()},
            {'host': ['xvideos.com'],     'func': lambda: self.__do_porntype('xvideos')},
            {'host': ['xtube.com'],       'func': lambda: self.__do_porntype('xtube')},
            {'host': ['pornhub.com'],     'func': lambda: self.__do_porntype('pornhub')},
            {'host': ['redtube.com'],     'func': lambda: self.__do_porntype('redtube')}, # redtube, tube8, pornhub完全一樣
            {'host': ['tube8.com'],       'func': lambda: self.__do_porntype('tube8')},
            {'host': ['playvids.com'],    'func': lambda: self.__do_vidstype()},
            {'host': ['peekvids.com'],    'func': lambda: self.__do_vidstype()},
            {'host': ['youtube.com'],     'func': lambda: self.__do_youtube()},
            {'host': ['vimeo.com', 'player.vimeo.com'],       'func': lambda: self.__do_vimeo()}
        ]

        self.__urlcheck_pattern = re.compile(r"^https?:\/\/(?:www\.)?([^\/]+)\/?", re.IGNORECASE)

        self.__header = {
            'User-Agent': 'Mozilla/5.0 (iPad; U; CPU OS 3_2_1 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Mobile/7B405',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-TW,zh;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate'
        }

        self.__pattern = dict(xvideos=dict(pattern_video=r"html5player\.setVideoUrlHigh\('([^']*)'\);",
                                           pattern_video_title=r"html5player\.setVideoTitle\('([^']*)'\);",
                                           pattern_file_ext=r"(?:.*)\/videos\/([^/]*)\/(?:.*)"),
                              xtube=dict(pattern_video=r'defaultQuality["]?:(?:\w*),["]?format["]?:["]?(\w*)["]?,'
                                                       r'["]?quality["]?:["]?(\d*)["]?,["]?videoUrl["]?:"([^"]*)"}',
                                         pattern_video_title=r'<h1>([^</>]*)</h1>',
                                         pattern_file_ext=None),
                              pornhub=dict(pattern_video=r'defaultQuality["]?:(?:\w*),["]?format["]?:["]?(\w*)["]?,'
                                                         r'["]?quality["]?:["]?(\d*)["]?,["]?videoUrl["]?:"([^"]*)"}',
                                           pattern_video_title=r'<meta property="og:title" content="([^"]*)"',
                                           pattern_file_ext=None),
                              redtube=dict(pattern_video=r'defaultQuality["]?:(?:\w*),["]?format["]?:["]?(\w*)["]?,'
                                                         r'["]?quality["]?:["]?(\d*)["]?,["]?videoUrl["]?:"([^"]*)"}',
                                           pattern_video_title=r'<h1 class="video_title_text">([^"]*)<\/h1>',
                                           pattern_file_ext=None),
                              tube8=dict(pattern_video=r'defaultQuality["]?:(?:\w*),["]?format["]?:["]?(\w*)["]?,'
                                                       r'["]?quality["]?:["]?(\d*)["]?,["]?videoUrl["]?:"([^"]*)"}',
                                         pattern_video_title=r'<h1 class="main-title"><span class="item">([^"]*)'
                                                             r'<\/span><\/h1>',
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

        self.__header['User-Agent'] = ua[random.randint(0,len(ua)-1)]

    def get_support_host(self):
        return [x['host'][0] for x in self.__support_host]

    def set_quite(self):
        self.__showlog_flag = False

    def log(self, strings):
        if self.__showlog_flag:
            print("[{0}] {1}".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), strings))

    def __connect(self, url=None, headers=None, timeout=3, stream=False):
        try:
            if not url:
                url = self.__url
            if not headers:
                headers = self.__header

            req = self.__session.get(url, headers=headers, timeout=timeout, stream=stream)
            if int(req.status_code) in [404, 500, 429]:
                self.log("網頁找不到或是網頁發生錯誤。錯誤碼 {0}".format(int(req.status_code)))
                return False
            return req
        except:
            self.log("網站連線超時，請檢查網路狀況")
            return False

    def claw(self, url):
        self.__url = url.strip()
        domain_name = self.__urlcheck_pattern.match(self.__url).group(1) if self.__urlcheck_pattern.match(self.__url) else ""
        try:
            return [i['func'] for i in self.__support_host if domain_name in i['host']][0]()
        except IndexError:
            self.log("網址可能不是支援的網站, 目前僅支援 {0}".format(", ".join([i['host'] for i in self.__support_host])))
            return False

    def __do_vimeo(self):
        self.log("開始分析影片")
        vimeo_id = self.__url.split("/")[-1]
        if vimeo_id == "":
            vimeo_id = self.__url.split("/")[-2]
        try:
            vimeo_id = int(vimeo_id)
        except ValueError:
            self.log("id編號錯誤。請輸入正確vimeo影片網址")
            return False
        # ------
        req = self.__session.get('https://www.vimeo.com/{0}/'.format(vimeo_id), headers=self.__header, timeout=10)
        is_private = re.search(r'class="exception_title--password iris_header">([^"]*)<\/h1>', req.text)
        if is_private and is_private.group(1) == 'This video is private':
            # 需要密碼
            password = input("請輸入密碼: ")
            b64passwd = base64.b64encode(password.encode("utf8")).decode("utf8")
            payload = {'password': b64passwd, 'Watch Video': ''}
            r = self.__session.post('https://player.vimeo.com/video/{0}/check-password?referrer=null'
                                    .format(vimeo_id), headers=self.__header, data=payload)
            config = json.loads(r.text)
            if not config:
                self.log("密碼錯誤")
                return False
        else:
            # 不需要密碼
            req = self.__session.get('https://player.vimeo.com/video/{0}/'.format(vimeo_id), headers=self.__header)
            configObj = re.search(r'var(?:\W+)config(?:\W+)=(.*);(?:\n|\r|\n\r)?', req.text)

            if configObj:
                try:
                    config = json.loads(configObj.group(1))
                except:
                    self.log("It may not be a video page")
                    return False
            else:
                self.log('It may not be a video page')
                return False
        # 取最高畫質
        config['request']['files']['progressive'].sort(key=lambda k: int(k['quality'][0:-1]),reverse=True)
        mp4_url = config['request']['files']['progressive'][0]['url']
        video_title = config['video']['title']
        self.log("影片真實路徑可能是 {0}".format(mp4_url))
        self.log("影片標題是 {0}".format(video_title))
        file_ext = "mp4"
        file_save_to = "{0}.{1}".format(video_title, file_ext) # 現在檔名都是影片標題
        return self.__download_from_url(mp4_url, file_save_to)  # 檔名用標頭

    def __do_youtube(self):
        self.log("開始分析影片")
        try:
            if self.__showlog_flag:
                def show_progress_bar(stream, chunk, file_handle, bytes_remaining):
                    pbar.update(len(chunk))

                yt = YouTube(self.__url, on_progress_callback=show_progress_bar)
                video = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()

                pbar = tqdm(desc="[{0}] ".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                            postfix="下載成 {0}".format(video.default_filename),
                            total=video.filesize, initial=0, unit='B', unit_scale=True, ascii=True, ncols=80,
                            bar_format='{desc} {percentage:3.0f}% [ETA {remaining}][{rate_fmt}] {postfix}')

                video.download()
                pbar.close()
            else:
                yt = YouTube(self.__url)
                video = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
                video.download()
            return True
        except exceptions.RegexMatchError:
            self.log("這網址不是影片頁面，或是要會員才可以看的影片，請檢查之後再試一次")
            return False

    def __do_porntype(self, pattern_name):
        req = self.__connect()
        req_text = str(req.text)
        self.log("開始分析影片")
        # 分析是否是embed type
        if "pornhub.com/embed/" in self.__url:
            self.log("這網址不是影片頁面，不能使用內嵌頁面")
            return False
        regular_express = re.findall(self.__pattern[pattern_name]['pattern_video'], req_text)
        if len(regular_express) == 0 or regular_express[0] == "":
            self.log("這網址不是影片頁面，或是要會員才可以看的影片，請檢查之後再試一次")
            return False

        if pattern_name in ['xtube', 'pornhub', 'redtube', 'tube8']:
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
                #如果json沒有，就從filename抓
                if len(os.path.basename(urlparse(mp4_url).path).split(".")) == 2:
                    file_ext = os.path.basename(urlparse(mp4_url).path).split(".")[1]
                else:
                    #filename也沒有就只好跟server問
                    req = self.__connect(url=mp4_url, stream=True, timeout=10)  # 影片格式改成跟主機問
                    regular_express = req.headers.get("Content-Type").split("/")
                    if len(regular_express) == 0 or regular_express[1] == "":
                        self.log("影片格式抓取有誤，請聯絡程式作者")
                        return False
                    file_ext = regular_express[1]
        else:
            mp4_url = regular_express[0].strip()

            # regular_express = re.findall(self.__pattern[pattern_name]['pattern_file_ext'], mp4_url) # xvideo的檔案副檔名在真實網址裡面。不在source html
            # if len(regular_express) == 0 or regular_express[0] == "":
            #     self.log("影片格式抓取有誤，請聯絡程式作者")
            #     return False
            # file_ext = regular_express[0]

            req = self.__connect(url=mp4_url, stream=True, timeout=10)  # 影片格式改成跟主機問
            regular_express = req.headers.get("Content-Type").split("/")
            if len(regular_express) == 0 or regular_express[1] == "":
                self.log("影片格式抓取有誤，請聯絡程式作者")
                return False
            file_ext = regular_express[1]

        self.log("影片真實路徑可能是 {0}".format(mp4_url))

        regular_express = re.findall(self.__pattern[pattern_name]['pattern_video_title'], req_text)
        if len(regular_express) == 0 or regular_express[0] == "":
            self.log("影片標題抓取有誤，請聯絡程式作者")
            return False

        video_title = regular_express[0].strip()
        self.log("影片標題是 {0}".format(video_title))
        file_save_to = "{0}.{1}".format(video_title, file_ext) # 現在檔名都是影片標題
        return self.__download_from_url(mp4_url, file_save_to)  # 檔名用標頭

    def __do_vidstype(self):
        req = self.__connect()
        req_text = str(req.text)
        self.log("開始分析影片")
        lg = html.fromstring(req_text)

        regular_express = lg.xpath("//video[@id='mediaPlayer']/@src")

        if len(regular_express) == 0 or regular_express[0] == "":
            self.log("這網址不是影片頁面，或是要會員才可以看的影片，請檢查之後再試一次")
            return False

        mp4_url = regular_express[0].strip()
        self.log("影片真實路徑可能是 {0}".format(mp4_url))

        req = self.__connect(url=mp4_url, stream=True, timeout=10)  # 影片格式改成跟主機問
        regular_express = req.headers.get("Content-Type").split("/")
        if len(regular_express) == 0 or regular_express[1] == "":
            self.log("影片格式抓取有誤，請聯絡程式作者")
            return False
        file_ext = regular_express[1]

        regular_express = lg.xpath("//div[@class='info-video']/h1/text()|//h1[@class='title-video']/text()")

        if len(regular_express) == 0 or regular_express[0] == "":
            self.log("影片標題抓取有誤，請聯絡程式作者")
            return False

        video_title = regular_express[0].strip()
        self.log("影片標題是 {0}".format(video_title))
        file_save_to = "{0}.{1}".format(video_title, file_ext) # 現在檔名都是影片標題
        return self.__download_from_url(mp4_url, file_save_to)  # 檔名用標頭

    def __do_twitter(self):
        '''
            twitter下載參考了 https://github.com/h4ckninja/twitter-video-downloader
        '''
        video_player_url_prefix = 'https://twitter.com/i/videos/tweet/'
        tweet_id = urlparse(self.__url).path.split("/")[-1]
        tweet_dir = Path("./twitter_tmp")
        video_player_url = video_player_url_prefix + tweet_id
        video_player_response = self.__connect(url=video_player_url)

        # Get the JS file with the Bearer token to talk to the API.
        # Twitter really changed things up.
        js_file_url = re.search(r'<script src="([^<>]*)"></script>', video_player_response.text).group(1)
        js_file_response = self.__connect(url=js_file_url)

        # Pull the bearer token out
        bearer_token_pattern = re.compile('Bearer ([a-zA-Z0-9%-])+')
        bearer_token = bearer_token_pattern.search(js_file_response.text)
        bearer_token = bearer_token.group(0)

        newheaders = self.__header.copy()
        newheaders['Authorization'] = bearer_token

        player_config = self.__connect(url='https://api.twitter.com/1.1/videos/tweet/config/' + tweet_id + '.json',
                                       headers=newheaders, timeout=10)

        if player_config.text == "":
            self.log("沒有權限讀取，不可以抓取非公開的影片")
            return False

        m3u8_url_get = json.loads(player_config.text)
        m3u8_url_get = m3u8_url_get['track']['playbackUrl']

        # Get m3u8
        m3u8_response = self.__connect(url=m3u8_url_get, headers=newheaders, timeout=10)
        m3u8_url_parse = urlparse(m3u8_url_get)
        video_host = m3u8_url_parse.scheme + '://' + m3u8_url_parse.hostname
        m3u8_parse = m3u8.loads(m3u8_response.text)

        maxbandwith = 0
        playlistID = 0
        for playlist in m3u8_parse.playlists:
            if playlist.stream_info.bandwidth > maxbandwith:
                maxbandwith = playlist.stream_info.bandwidth
                maxbandwithIndex = playlistID
            playlistID += 1
        playlist = m3u8_parse.playlists[maxbandwithIndex]

        resolution = str(playlist.stream_info.resolution[0]) + 'x' + str(playlist.stream_info.resolution[1])
        resolution_dir = Path(tweet_dir) / Path(resolution)
        Path.mkdir(resolution_dir, parents=True, exist_ok=True)
        playlist_url = video_host + playlist.uri

        ts_m3u8_response = requests.session().get(playlist_url)
        ts_m3u8_parse = m3u8.loads(ts_m3u8_response.text)

        ts_list = []

        if self.__showlog_flag:
            pbar = tqdm(desc="[{0}] ".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                        total=len(ts_m3u8_parse.segments.uri), initial=0, unit='區塊', unit_scale=False, ascii=True,
                        postfix="下載成 {0}.ts".format(tweet_id), ncols=80,
                        bar_format='{desc} {percentage:3.0f}% [ETA {remaining}] {postfix}')

        for ts_uri in ts_m3u8_parse.segments.uri:
            # print('[+] Downloading ' + resolution)
            ts_file = requests.session().get(video_host + ts_uri)
            fname = ts_uri.split('/')[-1]
            ts_path = resolution_dir / Path(fname)
            ts_list.append(ts_path)
            ts_path.write_bytes(ts_file.content)
            if self.__showlog_flag:
                pbar.update(1)

        if self.__showlog_flag:
            pbar.close()
        ts_full_file = Path(resolution_dir) / Path(tweet_id + '.ts')

        # Shamelessly taken from https://stackoverflow.com/questions/13613336/python-concatenate-text-files/27077437#27077437
        with open(str(ts_full_file), 'wb') as wfd:
            for f in ts_list:
                with open(f, 'rb') as fd:
                    shutil.copyfileobj(fd, wfd, 1024 * 1024 * 10)
                os.remove(f)
        if Path("./" + os.path.basename(str(ts_full_file))).exists():
            os.remove("./" + os.path.basename(str(ts_full_file)))
        if ts_full_file.exists():
            os.rename(ts_full_file, "./" + os.path.basename(str(ts_full_file)))
            try:
                shutil.rmtree("./twitter_tmp")
            except:
                pass

        return True

    def __download_from_url(self, mp4_url, file_save_to):
        
        file_save_to = "".join([letter for letter in file_save_to if letter not in "\/*"])

        """
        @param: url to download file
        @param: dst place to put the file
        備註起來的是續傳
        先關閉
        """
        try:
            file_size = int(self.__session.head(mp4_url).headers["Content-Length"])
            # if os.path.exists(dst):
            #     first_byte = os.path.getsize(dst)
            # else:
            #     first_byte = 0
            # if first_byte >= file_size:
            #     return file_size
            # header = {"Range": "bytes=%s-%s" % (first_byte, file_size)}
            if self.__showlog_flag:
                pbar = tqdm(desc="[{0}] ".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
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
            self.log("{0} 下載成功".format(file_save_to))
            return file_size
        except Exception as e:
            self.log("下載失敗")
            return False

    def internet_on(self):
        try:
            self.__session.get('http://216.58.192.142', timeout=2)
            return True
        except Exception as e:
            return False


if __name__ == '__main__':
    xx = XxxDownloader()
    support_hosts = ""
    for i, x in enumerate(xx.get_support_host(), 1):
        if i%3 == 0:
            support_hosts = "{0}{1}".format(support_hosts,x)
            support_hosts = "{0}\n".format(support_hosts)
        else:
            support_hosts = "{0}{1}\t".format(support_hosts,x)

    support_hosts = support_hosts[:-1]
    parser = MyParser(prog="XXXDL", epilog="目前支援有公開連結的網站，包括\n--------------"
                                                   "--------------------\n{0}\n\n\t\t\t\t\t\tW.S.Y"
                                                   " 2019".format(support_hosts), usage="xxxdl [-h]"
                                                                                        " [-q] video_page_url",
                      formatter_class=argparse.RawTextHelpFormatter)


    parser.add_argument('video_page_url', help="影片連結/批次連結檔案名")
    parser.add_argument('-q', '--quite',  help='關閉系統訊息', action="store_true")
    # parser.add_argument('-l', '--list', help='讀檔批次抓取', action="store_true")
    parser.add_argument('--version', action='version', version='{0} {1}\n'.format(project_name, version))

    args = parser.parse_args()

    if args.quite:
        xx.set_quite()

    if not xx.internet_on():
        sys.stderr.write('錯誤: %s\n' % "網路尚未連線。無法在離線狀況下使用")
        sys.exit(2)

    # if args.list:
    #     videolist = args.video_page_url
    #     with open(args.video_page_url ,"r") as f:
    #         for i in f.readlines():
    #             print(i.strip())
    #             error = 0
    #             while error < 2:
    #                 if not xx.claw(i.strip()):
    #                     error = error + 1
    #                 else:
    #                     break;
    #
    # else:
    if not all([urlparse(args.video_page_url).scheme, urlparse(args.video_page_url).netloc,
                urlparse(args.video_page_url).path]):
        sys.stderr.write('錯誤: %s\n' % "網址格式有錯")
        sys.exit(2)
    if not xx.claw(args.video_page_url):
        sys.exit(2)



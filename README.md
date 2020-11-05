# XXX下載器 ver 2.0b


這是用來下載一些"影片"

目前只有測試win10 64位元 

其他win7 或是win10 32位元不保證可以使用

點擊 run.bat 跳出 dos視窗之後。在裡面輸入 xxxdl -h 看說明



### 單次抓取
用法:  xxxdl -g [網址]

    xxxdl -g http://www.pornhub.com/view_video.php?viewkey=???????


### 批次抓取

加入等待抓取的網址

    用法:  xxxdl -a [網址]

查詢等待抓取的網址

    用法:  xxxdl -l

清除所有等待抓取的網址

    用法:  xxxdl -c

開始抓取(這時會一個個抓取那些使用 -a 參數加入的網址)

    用法:  xxxdl -s


加上 -q參數就是安靜模式。不會有訊息顯示(不建議使用)  

    xxxdl -g -q http://www.pornhub.com/view_video.php?viewkey=???????


如果網址有奇怪符號的 建議使用雙引號框住

    xxxdl -g "http://www.pornhub.com/view_video.php?viewkey=???????"

下載成功會在同一個目錄下出現




### 支援網站(目前先移除youtube)
| 列表 | ||
|:------------ | :----------- |:------------|
| twitter.com  | xvideos.com  |xtube.com    |
| pornhub.com  | redtube.com  |  tube8.com  |
| playvids.com | peekvids.com | vimeo.com



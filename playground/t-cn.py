# coding=utf-8
import requests
import pandas as pd
import re
import pyperclip

# not worked now!
# request请求
# os 短链接复制
# pd 读取剪切板中的网址
# re 正则匹配


def sina_url(url):
    base_url = "https://service.weibo.com/share/share.php?url=" + url + "&title=" + url
    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/77.0.3865.120 Safari/537.36"
    }
    res = requests.get(base_url, header)
    # 匹配字符串scope.short_url = " http://t.cn/Ryh0P2j ";\
    match = r'scope.short_url = "[?\s+](.*)"'
    url_short = re.search(match, res.text)
    print(url_short)
    if url_short:
        copy(url_short.group(1))
    else:
        print("get none")


def copy(url_short):
    pyperclip.copy(url_short)
    print(url_short)


if __name__ == "__main__":
    url_long = list(pd.read_clipboard())  # 读入剪切板数据
    print(url_long)
    if ("http://" in url_long[0]) or ("https://" in url_long[0]):  # 读取
        sina_url(url_long[0])

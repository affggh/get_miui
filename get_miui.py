import os
import sys
import textwrap
import requests
import bs4
import re
import threading


class GetMIUI(object):
    def __init__(self):
        self.url = "https://xiaomirom.com/series/"
        self.urlbase = "https://xiaomirom.com"
        self.ret = []
        self.rex_compile = re.compile(
            "(?:https?|ftp|file)://[-A-Za-z0-9+&@#/%?=~_|!:,.;]+[-A-Za-z0-9+&@#/%=~_|]")
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36'
        }

    def parse_dbutton(self, val: str) -> str:
        return self.rex_compile.search(val).group()

    def dlink_get(self, url: str, romtype: str = "recovery") -> str:
        reponse = requests.get(url, headers=self.headers)
        reponse.encoding = reponse.apparent_encoding
        data = bs4.BeautifulSoup(reponse.text, "html.parser")
        data = data.find_all("button")
        val = ""
        for i in data:
            val = i.get("onclick")
            if type(val) == str:
                val = self.parse_dbutton(val)
                if val.endswith(".tgz") and romtype == "fastboot":
                    break
                elif val.endswith(".zip") and romtype == "recovery":
                    break
        return val

    def getLink(self, deviceid: str, nation: str = "china", romtype: str = "recovery", ver: str = "stable", lines: int = 1) -> str:
        if ver == "stable":
            ver = "稳定版"
        elif ver == "dev":
            ver = "开发版"
        elif ver == "test":
            ver = "内测版"
        else:
            ver == "稳定版"
        reponse = requests.get(self.url, headers=self.headers)
        reponse.encoding = reponse.apparent_encoding
        # 整理数据
        data = bs4.BeautifulSoup(reponse.text, "html.parser")
        data = data.find("dl")
        if data == None:
            print("网站可能需要人机验证")
            return ""
        item = {}
        for i in data.find_all("dd"):
            if i.a.get("nav").find(deviceid) > -1:
                for j in i.find_all("a"):
                    item[j.string] = j.get("href")
        if len(item) == 0:
            print(f"没有爬到此机型代号：{deviceid} 的任何版本链接")
            return ""

        # 找对应国家的版本
        for i in item:
            if item[i].find(nation) > -1:
                break

        reponse = requests.get(item[i], headers=self.headers)
        reponse.encoding = reponse.apparent_encoding
        data = bs4.BeautifulSoup(reponse.text, "html.parser")
        data = data.find_all("p")
        item = []
        for i in range(len(data)):
            if data[i].strong != None:
                if data[i].strong.string != None:
                    if data[i].strong.string.lower().find(romtype) >-1:
                        bdata = data[i].find_all("strong")
                        if bdata[1].string.find(ver) > -1:
                            item.append(self.urlbase+data[i+2].a.get("href"))

        if len(item) == 0:
            print("未能获取到下载链接...")
            print(textwrap.dedent(f'''\
            请检查你的  设备代号 : {deviceid}
            区    域 : {nation}
            ROM 类型 : {romtype}
            版    本 : {ver}
        '''))
            return ""
        dlink = []
        if len(item) < lines:
            lines = len(item)
        for i in range(lines):
            sys.stderr.write(f"[{i+1}/{lines}] Get from {item[i]}\r")
            dlink.append(self.dlink_get(item[i], romtype))
        sys.stderr.write('\n')
        sys.stderr.flush()
        return dlink


if __name__ == '__main__':
    import argparse
    miui = GetMIUI()
    description = "Get first MIUI Download link from %s" %miui.urlbase
    parser = argparse.ArgumentParser(prog=sys.argv[0], description=description)
    parser.add_argument(
        "codename", help="Device codename like tiffany [Xiaomi 5X]")
    parser.add_argument("-n", default="china",
                        metavar="nation", help="Rom nation like china")
    parser.add_argument("-t", default="recovery", metavar="romtype",
                        help="Rom type , only allow recovery and fastboot")
    parser.add_argument("-v", default="stable", metavar="romver",
                        help="Only acquire stable, dev, test")
    parser.add_argument("-l", default=1, metavar="number", type=int,
                        help="Print result line number")

    args = parser.parse_args()

    # print(args)
    dlink = miui.getLink(args.codename,
                         args.n,
                         args.t,
                         args.v,
                         args.l)
    for i in dlink: print(i)

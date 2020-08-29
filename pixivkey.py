import requests, threading, re, os, sys, datetime
from concurrent.futures import ThreadPoolExecutor, wait, as_completed

# https://api.imjad.cn/pixiv/v2/?type=rank&mode=week&page=5
# mode #  
# day	日榜
# week	周榜
# month	月榜
# week_rookie	新人
# week_original	原创
# day_male	男性向
# day_female	女性向
# day_r18
# and more~


# date #
# yyyy-mm-dd

def parse_ymd(s):
    year_s, mon_s, day_s = s.split('-')
    return datetime.date(int(year_s), int(mon_s), int(day_s))

def mkdir(path):
    folder = os.path.exists(path)
    if not folder:
        os.makedirs(path)
        return 1106
    else:
        return 1

def download(url,filename):
    r = requests.get(url, stream=True)    
    with open(filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=32):
            f.write(chunk)
    print('下载完成' + filename)

def cleanurl(url):
    newurl = url.replace('https://i.pximg.net', 'https://pximg.sihuan.workers.dev') #这个是 SiHuan 做的反代
    # newurl = url.replace('https://i.pximg.net', 'https://pximg.pixiv-viewer.workers.dev')
    p = re.compile(r'_(.*)$')
    filename = re.findall(p,url)[0] #其实这儿正则有一丢丢问题 但是一般情况没问题 一个榜下来也没有一个不一般的情况吧

    return newurl,filename

def getoriginal(illust):
    original = []
    if illust['meta_pages']:
        for img in illust['meta_pages']:
            original.append(img['image_urls']['original'])
    elif illust['meta_single_page']:
        original.append(illust['meta_single_page']['original_image_url'])

    return original


def getillusts(date, mode, key):
    url = 'https://api.imjad.cn/pixiv/v2/'
    params = {
        'type': 'rank',
        'mode': mode,
        'date': date,
        'page': 1
    }
    illusts = {}
    while params['page']:
        print(params)
        resp = requests.get(url=url,params=params)
        print(resp.status_code)
        resp = resp.json()
        # print(resp)
        try:
            if resp['next_url']:
                params['page'] += 1
            else:
                params['page'] = 0
            for illust in resp['illusts']:
                for tag in illust['tags']:
                    if tag['name'] == key:
                        title = illust['title']
                        print(title)
                        illusts[title] = getoriginal(illust)
        except:
            print(resp)
    return illusts

def main(begin, end, mode, key):
    basedir = begin + '--' + end + '_' + mode + '_' + key

    begin = parse_ymd(begin)
    end = parse_ymd(end)

    illusts = {}
    with ThreadPoolExecutor(max_workers=16) as pool:
        tasklist = []
        for i in range((end - begin).days+1):
            date = str(begin + datetime.timedelta(days=i))
            task = pool.submit(getillusts, date, mode, key)
            tasklist.append(task)
        pool.shutdown()

        for future in as_completed(tasklist):
            addillusts = future.result()
            illusts.update(addillusts)

    print('抓取完成，开始下载。')
    mkdir(basedir)
    with ThreadPoolExecutor(max_workers=8) as pool:
        tasklist = []
        for illust in illusts:
            nowdir = basedir + '/' + illust
            mkdir(nowdir)
            for url in illusts[illust]:
                newurl, filename = cleanurl(url)
                filename = nowdir + '/' + filename
                print('准备下载 %s' % filename)
                task = pool.submit(download, newurl, filename)
                tasklist.append(task)
        pool.shutdown()
        wait(tasklist)
        # 下面用的 as_completed 不好 总之这儿很不清真，需要全部下载完才有输出。不过又不是不能用
        # for future in as_completed(tasklist):
        #     name, time = future.result()
        #     print(name,' 耗时 ',time)


main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
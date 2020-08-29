import requests, threading, re, os, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed

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

def mkdir(path):
    folder = os.path.exists(path)
    if not folder:
        os.makedirs(path)
        return 1106
    else:
        return 1

def download(url,filename):
    begin = time.time()
    r = requests.get(url, stream=True)    
    with open(filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=32):
            f.write(chunk)
    return filename, time.time() - begin

def cleanurl(url):
    # newurl = url.replace('https://i.pximg.net', 'https://pximg.sihuan.workers.dev') #这个是 SiHuan 做的反代
    newurl = url.replace('https://i.pximg.net', 'https://pximg.pixiv-viewer.workers.dev')
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


def getillusts(mode,date):
    url = 'https://api.imjad.cn/pixiv/v2/'
    params = {
        'type': 'rank',
        'mode': mode,
        'date': date,
        'page': 1
    }
    illusts = {}
    index = 0

    while params['page']:
        resp = requests.get(url=url,params=params).json()

        if resp['next_url']:
            params['page'] += 1
        else:
            params['page'] = 0

        for illust in resp['illusts']:
            index = index + 1
            title = str(index) + '_' + illust['title']
            illusts[title] = getoriginal(illust)
    return illusts

def main(mode,date):
    print('准备下载 %s %s 榜' % (date, mode))
    illusts = getillusts(mode,date)
    print('抓取完成，开始下载。')
    basedir = date + '_' + mode
    mkdir(basedir)
    with ThreadPoolExecutor(max_workers=8) as pool:
        tasklist = []
        for illust in illusts:
            nowdir = basedir + '/' + illust
            mkdir(nowdir)
            for url in illusts[illust]:
                newurl, filename = cleanurl(url)
                filename = nowdir + '/' + filename
                print('Downloading %s' % filename)
                task = pool.submit(download, newurl, filename)
                tasklist.append(task)
        pool.shutdown()
        # 下面用的 as_completed 不好 总之这儿很不清真，需要全部下载完才有输出。不过又不是不能用
        for future in as_completed(tasklist):
            name, time = future.result()
            print(name,' 耗时 ',time)


main(sys.argv[1], sys.argv[2])
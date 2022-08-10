import asyncio
from datetime import timedelta, datetime
import functools
import signal
import sqlite3
import sys
import time

from pixivpy_async import AppPixivAPI

import ranktaitai
from logger import logger
import db


sys.dont_write_bytecode = True

_TOKEN = ""



_OffsetError = Exception('Offset over 5000')
_AuthError = Exception('Auth error')
_UnknowError = Exception('Unknow error')

async def _login(aapi):
    await aapi.login(refresh_token=_TOKEN)

def requestNoError(aapi):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args,**kwargs):
            while True:
                json_result = await func(*args,**kwargs)
                if not json_result.error:
                    return json_result,None

                if json_result.error.message == 'Rate Limit':
                    logger.warning('Rate Limit, sleep 80 second')
                    time.sleep(80)
                    continue
                elif json_result.error.message == '{"offset":["Offset must be no more than 5000"]}':
                    logger.warning('Offset over 5000,Skip')
                    return None, _OffsetError
                elif json_result.error.message == 'Error occurred at the OAuth process. Please check your Access Token to fix this. Error Message: invalid_grant':
                    logger.warning('Auth error, Refresh token')
                    await _login(aapi)
                else:
                    logger.error('Unknown error: ' + json_result.error.message)
                    return None, _UnknowError
        return wrapper
    return decorator

async def updateUserDetail(aapi,conn,uid):
    json_result, error = await requestNoError(aapi)(aapi.user_detail)(uid)
    if error == None:
            db.dbUpdateUser(conn,uid,json_result.user.name)
            return json_result.user.name
    elif error == _UnknowError:
        logger.error((f'Update detail error: {uid}'))
        return None
    else:
        return None

async def updateUserFollowing(aapi,conn,uid):
    allUserNum = 0
    newUserNum = 0
    next_qs = {'restrict': 'public', 'offset': 0, 'user_id': uid}
    while next_qs:
        json_result,error = await requestNoError(aapi)(aapi.user_following)(**next_qs)
        if error == None:
            followings = [ {'id':preview.user.id, 'name': preview.user.name} for preview in json_result.user_previews ]
            for following in followings:
                allUserNum += 1
                newUserNum += db.dbAddorUpdateUser(conn,following['id'],following['name'])
            next_qs = aapi.parse_qs(json_result.next_url)
        elif error == _OffsetError:
            logger.warning(f'Update user following Offset over 5000,Skip: {uid}')
            db.dbUpdateUser(conn,uid,following=True)
            return allUserNum,newUserNum
        else:
            logger.error(f'Update user following unknow error: {uid}')
            return allUserNum,newUserNum

    db.dbUpdateUser(conn,uid,following=True)
    return allUserNum,newUserNum

async def updateUserIllusts(aapi,conn,uid):
    allIllustNum = 0
    newIllustNum = 0
    next_qs = {'user_id': uid, 'filter': 'for_ios', 'type': 'illust', 'offset': 0}
    while next_qs:
        json_result,error = await requestNoError(aapi)(aapi.user_illusts)(**next_qs)
        if error == None:
            for illust in json_result.illusts:
                allIllustNum += 1
                newIllustNum += db.dbAddorUpdateIllust(conn,illust)
            next_qs = aapi.parse_qs(json_result.next_url)
        elif error == _OffsetError:
            logger.warning(f'Update user illust Offset over 5000,Skip: {uid}')
            db.dbUpdateUser(conn,uid,illust=True)
            return allIllustNum,newIllustNum
        else:
            logger.error(f'Update user illust unknow error: {uid}')
            return allIllustNum,newIllustNum
    
    db.dbUpdateUser(conn,uid,illust=True)
    return allIllustNum,newIllustNum

async def updateRank(aapi,conn,mode,date):
    allIllustNum = 0
    newIllustNum = 0
    newUserNum = 0

    next_qs = {'mode': mode, 'date': date, 'offset': 0}
    while next_qs:
        json_result,error = await requestNoError(aapi)(aapi.illust_ranking)(**next_qs)
        if error == None:
            for illust in json_result.illusts:
                allIllustNum += 1
                newIllustNum += db.dbAddorUpdateIllust(conn,illust)
                newUserNum += db.dbAddorUpdateUser(conn,illust.user.id,illust.user.name)
            next_qs = aapi.parse_qs(json_result.next_url)
        elif error == _OffsetError:
            logger.warning(f'Update rank Offset over 5000,Skip: {mode} {date}')
            return allIllustNum,newIllustNum
        else:
            logger.error(f'Update rank unknow error: {mode} {date}')
            return allIllustNum,newIllustNum
    
    return allIllustNum,newIllustNum,newUserNum


async def freshByUsers(aapi,conn,uids,detail = True, following = True, illust = True):
    l = len(uids)
    logger.warning(f'total {l} users to update { "detail" if detail else ""} { "following" if following else ""} { "illust" if illust else ""}')
    for i,uid in enumerate(uids):
        logger.info(f'{i+1}/{l} {uid} Start')
        if detail:
            uname = await updateUserDetail(aapi,conn,uid)
            logger.info(f'Update detail   : {uname}')
        if following:
            a,n = await updateUserFollowing(aapi,conn,uid)
            logger.info(f'Update following: all:{a} new:{n}')
        if illust:
            a,n = await updateUserIllusts(aapi,conn,uid)
            logger.info(f'Update illust   : all:{a} new:{n}')
        logger.info(f'{i+1}/{l} {uid} Done')

async def freshByRank(aapi,conn,modes,begindate,enddate):
    begin = datetime.strptime(begindate,'%Y-%m-%d')
    end = datetime.strptime(enddate,'%Y-%m-%d')
    l = (end - begin).days + 1
    logger.warning(f'total {l} days to update. { " ".join(modes) } {begindate}--{enddate}')

    i = 0
    while begin <= end:
        date = begin.strftime('%Y-%m-%d')
        logger.info(f'{i+1}/{l} {date} Start')
        for mode in modes:
            allIllustNum,newIllustNum,newUserNum = await updateRank(aapi,conn,mode,date)
            logger.info(f'Update {mode:<9} : illusts:{allIllustNum} illusts*:{newIllustNum} user*:{newUserNum}')
        logger.info(f'{i+1}/{l} {date} Done')
        begin += timedelta(days=1)
        i += 1


async def _main(aapi,conn):
    await _login(aapi)

    # 刷新用户信息、关注、作品
    # uids = dbGetAllUserList(conn)
    # uids = ranktaitai.uids
    # done = uids.index(691307)
    # uids = uids[done + 1:]
    # await freshByUsers(aapi,conn,uids,detail = True, following = False, illust = True)

    # 刷新排行榜
    modes = ['day','day_r18']
    begindate = '2019-12-01'
    enddate = '2020-01-1'
    await freshByRank(aapi,conn,modes,begindate,enddate)


def main():
    conn = sqlite3.connect('pixiv.db')
    def signal_handler(signal, frame):
        logger.warning('Stop by Ctrl+C!')
        conn.commit()
        conn.close()
        sys.exit(0)

    logger.warning('Start')
    signal.signal(signal.SIGINT, signal_handler)

    asyncio.run(_main(AppPixivAPI(),conn))

    conn.close()
    logger.warning('Stop by All Done!')

if __name__ == '__main__':
    main()

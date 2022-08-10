from logger import logger
import time

def dbGetAllUserList(conn,limit=None):
    cur = conn.cursor()
    cur.execute('select ID from USER')
    ids = [id[0] for id in cur.fetchall()]
    if limit:
        ids = ids[:limit]
    return ids

def dbUpdateUser(conn,uid,name='',following=False,illust=False):
    cur = conn.cursor()
    if name:
        cur.execute('update USER set NAME=?,UPDATETIME=? where ID=?', ( \
            name, \
            int(time.time()), \
            uid))
    if following:
        cur.execute('update USER set UPDATEFOLLOWING=? where ID=?', ( \
            int(time.time()), \
            uid))
    if illust:
        cur.execute('update USER set UPDATEILLUST=? where ID=?', ( \
            int(time.time()), \
            uid))
    conn.commit()
    logger.debug(f'Update user:{uid:>10} { name } {"following" if following else ""} {"ilusts" if illust else ""}')

def dbAddorUpdateUser(conn,uid,name = '',update = False):
    cur = conn.cursor()
    cur.execute('select ID from USER where ID=?', (uid,))
    if cur.fetchone():
        if update and name:
            dbUpdateUser(conn,uid,name)
        else:
            logger.trace(f'   Skip update user: {uid:>10} {name}')
        return 0
    else:
        cur.execute('insert into USER (ID,NAME,UPDATETIME) values (?,?,?)', (uid,name if name else None,int(time.time())))
        conn.commit()
        logger.debug(f'   Add user: {uid:>10} {name}')
        return 1

def dbUpdateIllust(conn,illust):
    cur = conn.cursor()

    view = illust.total_view
    like = illust.total_bookmarks
    if view > 0:
        rate = like / view
    else:
        rate = 0
    if illust.page_count == 1:
        url = illust.meta_single_page['original_image_url']
    else:
        url = ','.join([img['image_urls']['original'] for img in illust.meta_pages])
    cur.execute('update ILLUST set TITLE=?,TAGS=?,WIDTH=?,HEIGHT=?,VIEW=?,BOOKMARK=?,RATE=?,URLS=?,UPDATETIME=? where ID=?', ( \
        illust['title'], \
        ','.join([tag['name'] for tag in illust.tags]), \
        illust['width'], \
        illust['height'], \
        view, \
        like, \
        rate, \
        url, \
        int(time.time()), \
        illust['id']))
    conn.commit()
    logger.debug(f'Update illust: {illust["id"]:>10}')

def dbAddorUpdateIllust(conn,illust,update = False):
    cur = conn.cursor()
    cur.execute('select ID from ILLUST where ID=?', (illust['id'],))
    if cur.fetchone():
        if update:
            dbUpdateIllust(conn,illust)
        else:
            logger.trace(f' Skip update illust: {illust["id"]:>10} {illust["title"]}')
        return 0
    else:
        view = illust.total_view
        like = illust.total_bookmarks
        if view > 0:
            rate = like / view
        else:
            rate = 0
        if illust.page_count == 1:
            url = illust.meta_single_page['original_image_url']
        else:
            url = ','.join([img['image_urls']['original'] for img in illust.meta_pages])
        cur.execute('insert into ILLUST values (?,?,?,?,?,?,?,?,?,?,?,?,?)', ( \
            illust['id'], \
            illust['title'],\
            0 if illust.type == 'illust' else 1, \
            illust['user']['id'], \
            ','.join([tag['name'] for tag in illust.tags]), \
            illust['create_date'], \
            illust['width'], \
            illust['height'],\
            view, \
            like, \
            rate, \
            url, \
            int(time.time())))
        conn.commit()
        logger.debug(f'Add illust: {illust["id"]:>10} {illust["title"]}')
        return 1

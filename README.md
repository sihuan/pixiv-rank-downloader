# pixiv rank downloader

    获取 pixiv 插画信息存在 sqlite 数据库.

## 能干啥

1. 日榜

    获取指定日期区间日榜所有插画信息，同时记录前述插画的作者。

2. 从画师更新

    指定画师列表 uids List[int]，和更新内容 detail、following、illust
    
    对应更新列表中画师的信息、关注的画师、插画作品

## 用法

一般来说，假设你没有任何数据。

### 获取 token
先获取 refresh_token，方法见 [@ZipFile Pixiv OAuth Flow](https://gist.github.com/ZipFile/c9ebedb224406f4f11845ab700124362)


填到 [updatedb.py#L18](updatedb.py#L18)，像这样
```python
_TOKEN = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

### 新建数据库

只需要运行一次

```shell
python initdb.py
```

### 获取数据

修改 [updatedb.py#L168](updatedb.py#L168) `_main()` 函数内容。

从日榜获取

``` python
modes = ['day','day_original'] #指定榜单，大概有下面这些可选
# day, week, month, day_male, day_female, week_original, week_rookie,day_r18, day_male_r18, day_female_r18, week_r18, week_r18g
begindate = '2019-12-01'
enddate = '2020-01-1'
await freshByRank(aapi,conn,modes,begindate,enddate)
```

从画师获取

```python
uids = [11111,22222,3333]       #指定画师 id 列表
# uids = dbGetAllUserList(conn) #获取数据库中所有画师
# uids = ranktaitai.uids        #附带了一个在 2021-01-01--2022-08-07 上过榜的画师列表
await freshByUsers(aapi,conn,uids,detail = True, following = False, illust = True)
# detail：更新画师信息
# following: 获取画师关注的画师存到数据库
# illust: 获取画师所有插画
```

执行

```shell
python updatedb.py
```

### 建议

建议先获取一定时间的榜单数据（同时更新了上过榜的画师），再通过数据库中所有画师更新插画作品。

日志配置在 [logger.py](logger.py)

### 糊的太烂，别喷我，别问我为啥不写命令行读参数
# -- coding: utf-8 --
import os
import shutil
import sys

def mkdir(path):
    folder = os.path.exists(path)
    if not folder:
        os.makedirs(path)
        return 1106
    else:
        return 1

index = 0
for root , dirs, files in os.walk('./'):
    mkdir('./justok')
    for name in files:
        index += 1
        if name.endswith(".png") or name.endswith(".jpg"): # 只复制特定类型文件
            print(name)
            # print (os.path.join(root, name))
            source = os.path.join(root, name)
            target = os.path.join('./justok', str(index)+name)
            try:
                shutil.copy(source, target)
            except:
                print("Copy %s failed!" % name)
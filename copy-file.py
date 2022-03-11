# -*- coding: UTF-8 -*-
__author__ = 'genffy'
'''
将某个文件下的所有文件拷贝到指定的文件夹下。（之前由于歌曲存放是按专辑名歌手名 建文件夹的，不想手动的Ctr+C和Ctr+V）
'''
import os


def findFile(rootDir):
    list_dirs = os.walk(rootDir)
    for root, dirs, files in list_dirs:
        for d in dirs:
            print os.path.join(root, d)
        for f in files:
            thisFile = os.path.join(root, f)
            targetFile = os.path.join('E:\musicFile', f)
            copyFile(thisFile, targetFile)
            print os.path.join(root, f)


def copyFile(sourceFile, targetFile):
    open(targetFile, "wb").write(open(sourceFile, "rb").read())
    print 'copy success'+sourceFile


'''
import os
def findFile(rootDir):
    for lists in os.listdir(rootDir):
        path = os.path.join(rootDir, lists)
        print path
        if os.path.isdir(path):
            findFile(path)
'''
findFile('E:\Music')

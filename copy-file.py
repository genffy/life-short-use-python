# -*- coding: UTF-8 -*-
__author__ = "genffy"
"""
将某个文件下的所有文件拷贝到指定的文件夹下。（之前由于歌曲存放是按专辑名歌手名 建文件夹的，不想手动的Ctr+C和Ctr+V）
"""
import os


def findFile(
    root_dir, target_dir, ext_arr=[".jpg", ".png", ".jpeg", ".gif", ".mp4", ".mp3"]
):
    list_dirs = os.walk(root_dir)
    for root, dirs, files in list_dirs:
        # for d in dirs:
        #     print(os.path.join(root, d))
        for f in files:
            ext = os.path.splitext(f)[1]  # 获取后缀名
            if ext in ext_arr:
                print(ext)
                thisFile = os.path.join(root, f)
                targetFile = os.path.join(target_dir, f)
                copyFile(thisFile, targetFile)
                print(os.path.join(root, f))


def copyFile(sourceFile, targetFile):
    open(targetFile, "wb").write(open(sourceFile, "rb").read())
    print("copy success" + sourceFile)


if __name__ == "__main__":
    findFile(f"path/to/source", f"path/to/target")

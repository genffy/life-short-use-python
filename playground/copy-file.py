# -*- coding: UTF-8 -*-
__author__ = "genffy"
"""
将某个文件下的所有文件拷贝到指定的文件夹下。（之前由于歌曲存放是按专辑名歌手名 建文件夹的，不想手动的Ctr+C和Ctr+V）
"""
import os


def find_file(root_dir, target_dir, ext_arr=None):
    if ext_arr is None:
        ext_arr = [".jpg", ".png", ".jpeg", ".gif", ".mp4", ".mp3"]
    list_dirs = os.walk(root_dir)
    for root, dirs, files in list_dirs:
        # for d in dirs:
        #     print(os.path.join(root, d))
        for f in files:
            ext = os.path.splitext(f)[1]  # 获取后缀名
            if ext in ext_arr:
                print(ext)
                this_file = os.path.join(root, f)
                target_file = os.path.join(target_dir, f)
                copy_file(this_file, target_file)
                print(os.path.join(root, f))


def copy_file(source_file, target_file):
    open(target_file, "wb").write(open(source_file, "rb").read())
    print("copy success" + source_file)


if __name__ == "__main__":
    find_file("path/to/source", "path/to/target")

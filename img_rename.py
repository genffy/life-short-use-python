#coding=utf-8
'''
Created on 2013年10月21日

@author: genffy
'''

import os
import sys
import os.path
from random import Random
import Image
from ExifTags import TAGS
from xml.etree.ElementTree import tostring

'''
@see: get randomString

'''
def random_str(randomlength=8):
    str = ''
    chars = 'AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz0123456789'
    length = len(chars) - 1
    random = Random()
    for i in range(randomlength):
        str+=chars[random.randint(0, length)]
    return str
'''
@see: get exif information from imge files

'''
def get_exif_data(fname,key):
    """Get embedded EXIF data from image file."""
    ret = {}
    try:
        img = Image.open(fname)
        if hasattr( img, '_getexif' ):
            exifinfo = img._getexif()
            if exifinfo != None:
                for tag, value in exifinfo.items():
                        decoded = TAGS.get(tag,tag)
                        if key==decoded:
                            ret[decoded] = value
    except IOError:
        print 'IOERROR ' + fname
    return ret.get(key).replace(" ","-")
'''
@see: rename image file 

'''
def rename_img(startdir):
    exif_log=open("exif_log.txt","a")
    for dirpath, dirnames, filenames in os.walk(startdir):
            for filename in filenames:
                if os.path.splitext(filename)[1] == '.jpg':
                   filepath = os.path.join(dirpath, filename)
                   newname="genffy-"+get_exif_data(startdir+"/"+filename,"Model")+'-'+random_str()+".jpg"
                   os.rename(os.path.join(dirpath,filename),os.path.join(dirpath,newname))
                   exif_log.write(filename+"\n")
                   print filename
                    

if __name__ == '__main__':
    startdir='C:/Users/genffy/Desktop/upload'
    rename_img(startdir)           

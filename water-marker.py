#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse
import os
import sys
import math
import textwrap

from PIL import Image, ImageFont, ImageDraw, ImageEnhance, ImageChops, ImageOps
import cv2 as cv
import numpy as np


def add_mark(imagePath, mark, args):
    """
    添加水印，然后保存图片
    """
    im = Image.open(imagePath)
    im = ImageOps.exif_transpose(im)

    image = mark(im)
    name = os.path.basename(imagePath)
    if image:
        if not os.path.exists(args.out):
            os.mkdir(args.out)

        new_name = os.path.join(args.out, name)
        if os.path.splitext(new_name)[1] != ".png":
            image = image.convert("RGB")
        image.save(new_name, quality=args.quality)

        print(name + " Success.")
    else:
        print(name + " Failed.")


def set_opacity(im, opacity):
    """
    设置水印透明度
    """
    assert opacity >= 0 and opacity <= 1

    alpha = im.split()[3]
    alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
    im.putalpha(alpha)
    return im


def crop_image(im):
    """裁剪图片边缘空白"""
    bg = Image.new(mode="RGBA", size=im.size)
    diff = ImageChops.difference(im, bg)
    del bg
    bbox = diff.getbbox()
    if bbox:
        return im.crop(bbox)
    return im


def gen_mark(args):
    """
    生成mark图片，返回添加水印的函数
    """
    # 字体宽度、高度
    is_height_crop_float = "." in args.font_height_crop  # not good but work
    width = len(args.mark) * args.size
    if is_height_crop_float:
        height = round(args.size * float(args.font_height_crop))
    else:
        height = int(args.font_height_crop)

    # 创建水印图片(宽度、高度)
    mark = Image.new(mode="RGBA", size=(width, height))
    # 生成文字
    draw_table = ImageDraw.Draw(im=mark)
    draw_table.text(
        xy=(0, 0),
        text=args.mark,
        fill=args.color,
        font=ImageFont.truetype(args.font_family, size=args.size),
    )
    del draw_table

    # 裁剪空白
    mark = crop_image(mark)

    # 透明度
    set_opacity(mark, args.opacity)

    def mark_im(im):
        """在im图片上添加水印 im为打开的原图"""

        # 计算斜边长度
        c = int(math.sqrt(im.size[0] * im.size[0] + im.size[1] * im.size[1]))

        # 以斜边长度为宽高创建大图（旋转后大图才足以覆盖原图）
        mark2 = Image.new(mode="RGBA", size=(c, c))

        # 在大图上生成水印文字，此处mark为上面生成的水印图片
        y, idx = 0, 0
        while y < c:
            # 制造x坐标错位
            x = -int((mark.size[0] + args.space) * 0.5 * idx)
            idx = (idx + 1) % 2

            while x < c:
                # 在该位置粘贴mark水印图片
                mark2.paste(mark, (x, y))
                x = x + mark.size[0] + args.space
            y = y + mark.size[1] + args.space

        # 将大图旋转一定角度
        mark2 = mark2.rotate(args.angle)

        # 在原图上添加大图水印
        if im.mode != "RGBA":
            im = im.convert("RGBA")
        im.paste(
            mark2,  # 大图
            (int((im.size[0] - c) / 2), int((im.size[1] - c) / 2)),  # 坐标
            mask=mark2.split()[3],
        )
        del mark2
        return im

    return mark_im


# python water-marker.py -f ./data/img
def main():
    parse = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
    parse.add_argument("-f", "--file", type=str, help="image file path or directory")
    parse.add_argument(
        "-m",
        "--mark",
        default="",
        type=str,
        help="watermark content",
    )
    parse.add_argument(
        "-o",
        "--out",
        default="./output",
        help="image output directory, default is ./output",
    )
    parse.add_argument(
        "-c",
        "--color",
        default="#8B8B1B",
        type=str,
        help="text color like '#000000', default is #8B8B1B",
    )
    parse.add_argument(
        "-s",
        "--space",
        default=75,
        type=int,
        help="space between watermarks, default is 75",
    )
    parse.add_argument(
        "-a",
        "--angle",
        default=30,
        type=int,
        help="rotate angle of watermarks, default is 30",
    )
    parse.add_argument(
        "--font-family",
        default="PingFang.ttc",
        type=str,
        help=textwrap.dedent(
            """\
                       using font in system just by font file name
                       for example 'PingFang.ttc', which is default installed on macOS
                       """
        ),
    )
    parse.add_argument(
        "--font-height-crop",
        default="1.2",
        type=str,
        help=textwrap.dedent(
            """\
                       change watermark font height crop
                       float will be parsed to factor; int will be parsed to value
                       default is '1.2', meaning 1.2 times font size
                       this useful with CJK font, because line height may be higher than size
                       """
        ),
    )
    parse.add_argument(
        "--size", default=50, type=int, help="font size of text, default is 50"
    )
    parse.add_argument(
        "--opacity",
        default=0.3,
        type=float,
        help="opacity of watermarks, default is 0.15",
    )
    parse.add_argument(
        "--quality",
        default=80,
        type=int,
        help="quality of output images, default is 80",
    )

    args = parse.parse_args()

    if isinstance(args.mark, str) and sys.version_info[0] < 3:
        args.mark = args.mark.decode("utf-8")

    mark = gen_mark(args)

    if os.path.isdir(args.file):
        names = os.listdir(args.file)
        for name in names:
            lowercase_filename = name.lower()
            if lowercase_filename.endswith(".jpg") or lowercase_filename.endswith(
                ".png"
            ):
                image_file = os.path.join(args.file, name)
                add_mark(image_file, mark, args)
    else:
        add_mark(args.file, mark, args)


# imgurl path to image file
def img_marker(
    imgurl,
):
    img = cv.imdecode(np.fromfile(imgurl, dtype=np.uint8), -1)
    txturls = imgurl.rsplit(".", 1)
    txturl = rf"{txturls[0]}.txt"

    if img is None:
        sys.exit("Could not read the image.")
    else:
        cv.namedWindow("Display window", cv.WINDOW_NORMAL)
        cv.resizeWindow("Display window", img.shape[1], img.shape[0])
        #  annotation file template
        # label x y w h
        # 0 0.500781 0.611111 0.023438 0.027778
        # 0 0.534766 0.599306 0.024219 0.034722
        # 1 0.376172 0.729861 0.039844 0.079167
        with open(txturl, "r") as f:
            lines = f.readlines()

        # read annotation by line
        for line in lines:
            parts = line.split()
            label = int(parts[0])
            x = float(parts[1])
            y = float(parts[2])
            w = float(parts[3])
            h = float(parts[4])

            # calculate the rectangle box
            x1 = int((x - w / 2) * img.shape[1])
            y1 = int((y - h / 2) * img.shape[0])
            x2 = int((x + w / 2) * img.shape[1])
            y2 = int((y + h / 2) * img.shape[0])

            # draw the rectangle box
            cv.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv.imshow("Display window", img)
        k = cv.waitKey(0)
        if k == ord("q"):  # wait for ESC key to exit
            cv.destroyAllWindows()

        cv.destroyAllWindows()


if __name__ == "__main__":
    # img_marker("./data/color_2023-06-07_16_36_10.png")
    main()

import base64
import io
import os
from PIL import Image
from PIL import ImageFile

# # 压缩图片文件


def compress_image(outfile, mb=190, quality=85, k=0.9):
    """不改变图片尺寸压缩到指定大小
    :param outfile: 压缩文件保存地址
    :param mb: 压缩目标，KB
    :param step: 每次调整的压缩比率
    :param quality: 初始压缩比率
    :return: 压缩文件地址，压缩文件大小
    """

    o_size = os.path.getsize(outfile) // 1024
    print(o_size, mb)
    if o_size <= mb:
        return outfile

    ImageFile.LOAD_TRUNCATED_IMAGES = True
    while o_size > mb:
        im = Image.open(outfile)
        x, y = im.size
        out = im.resize((int(x * k), int(y * k)), Image.ANTIALIAS)
        try:
            out.save(outfile, quality=quality)
        except Exception as e:
            print(e)
            break
        o_size = os.path.getsize(outfile) // 1024
    return outfile


# # 压缩base64的图片
def compress_image_bs4(b64, mb=190, k=0.9):
    """不改变图片尺寸压缩到指定大小
    :param outfile: 压缩文件保存地址
    :param mb: 压缩目标，KB
    :param step: 每次调整的压缩比率
    :param quality: 初始压缩比率
    :return: 压缩文件地址，压缩文件大小
    """
    f = base64.b64decode(b64)
    with io.BytesIO(f) as im:
        o_size = len(im.getvalue()) // 1024
        if o_size <= mb:
            return b64
        im_out = im
        while o_size > mb:
            img = Image.open(im_out)
            x, y = img.size
            out = img.resize((int(x * k), int(y * k)), Image.ANTIALIAS)
            im_out.close()
            im_out = io.BytesIO()
            out.save(im_out, "jpeg")
            o_size = len(im_out.getvalue()) // 1024
        b64 = base64.b64encode(im_out.getvalue())
        im_out.close()
        return str(b64, encoding="utf8")


if __name__ == "__main__":
    for img in os.listdir("../data/img/"):
        # print(str(img))
        compress_image(outfile="./data/img/" + str(img))
    print("完")
# from PIL import Image

# # My image is a 200x374 jpeg that is 102kb large
# foo = Image.open('path/to/image.jpg')
# foo.size  # (200, 374)

# # downsize the image with an ANTIALIAS filter (gives the highest quality)
# foo = foo.resize((160, 300), Image.ANTIALIAS)

# # The saved downsized image size is 24.8kb
# foo.save('path/to/save/image_scaled.jpg', quality=95)

# foo.save('path/to/save/image_scaled_opt.jpg', optimize=True,
#          quality=95)  # The saved downsized image size is 22.9kb

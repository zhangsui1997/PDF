import os
import sys
import shutil

from PyPDF2 import PdfFileReader, PdfFileWriter, PdfFileMerger
from PyPDF2.utils import u_, b_
from PyPDF2.generic import TextStringObject
from PyPDF2.pdf import ContentStream
from pdf2image import convert_from_path, generators
from PIL import Image


@generators.threadsafe
def single_jpgname_generator():
    while True:
        yield ""


WIDTH = 604
HEIGHT = 686
COVER_WIDTH = 439
COVER_HEIGHT = 496


# @generators.threadsafe
# def double_jpgname_generator(start, end):
#     while start < end:
#         yield str(start) + "*" + str(start + 1)
#         start += 2


def run():
    print("*使用时请将本文件和原pdf文件放在同一目录下*\n*使用时碰到任何问题可以ctrl+c退出*\n*输入时若无内容可以直接回车跳过*\n")

    coverPath = input("请输入封面pdf文件名:")
    if coverPath and not os.path.exists(coverPath):
        print("封面pdf文件不存在!")
        sys.exit(0)
    filePath = input("请输入内文pdf文件名:")
    if filePath and not os.path.exists(filePath):
        print("内文pdf文件不存在!")
        sys.exit(0)
    if not coverPath and not filePath:
        print("请输入正确的文件名!")
        sys.exit(0)

    skipNumPages = input("请输入合并图片时跳过页数(默认为1):")
    try:
        skipNumPages = int(skipNumPages) if skipNumPages else 1
    except:
        print("请输入正确的跳过页数!")
        sys.exit(0)

    outputFolder = filePath.split(".")[0] if filePath else coverPath.split(".")[0]
    if not os.path.exists(outputFolder):
        os.mkdir(outputFolder)

    fileName = filePath.split(".")[0]
    if filePath:
        pdfFile = PdfFileReader(open(filePath, 'rb'))

        txtPath = outputFolder + "/" + fileName + ".txt"
        if os.path.exists(txtPath):
            os.remove(txtPath)
        imagePath = outputFolder + "/" + fileName + "_content"
        if os.path.exists(imagePath):
            shutil.rmtree(imagePath)
        os.mkdir(imagePath)

        if pdfFile.isEncrypted:
            try:
                pdfFile.decrypt('')
                print('File Decrypted (PyPDF2)')
            except:
                command = ("cp " + filePath +
                           " temp.pdf; qpdf --password='' --decrypt temp.pdf " + filePath
                           + "; rm temp.pdf")
                os.system(command)
                print('File Decrypted (qpdf)')
                pdfFile = PdfFileReader(open(filePath, 'rb'))

        newPdfPath = outputFolder + "/" + "new.pdf"
        newPdf = open(newPdfPath, "wb")
        f = open(txtPath, "w")
        pdfWriter = PdfFileWriter()
        for i in range(pdfFile.getNumPages()):
            page = pdfFile.getPage(i)
            # 提取txt文件
            f.write("======================Page %d:======================\n" % (i + 1))
            f.write(getTextByPage(page) + "\n\n")
            # 输出符合604(宽)*686(高) 图片按照宽度等比例缩放的pdf
            # height = page.mediaBox.getHeight()
            page.scaleTo(WIDTH, HEIGHT)
            pdfWriter.addPage(page)
        f.close()
        pdfWriter.write(newPdf)
        newPdf.close()

        # images 代表PDF文档每一页的PIL图像的列表
        convert_from_path(newPdfPath, output_folder=imagePath, fmt="jpg", thread_count=4,
                          output_file=single_jpgname_generator())

        imagesName = os.listdir(imagePath)
        imagesName.sort()
        start = skipNumPages

        for i in range(len(imagesName)):

            image = Image.open(imagePath + "/" + imagesName[i])
            _filename = image.filename
            image = image.resize((WIDTH, HEIGHT), Image.ANTIALIAS)
            image.save(_filename.replace("-", ""))

            if start == i and start + 1 < len(imagesName):
                merger = [
                    Image.open(imagePath + "/" + imagesName[start]),
                    Image.open(imagePath + "/" + imagesName[start + 1])]

                targetSize = (merger[0].size[0] * 2, merger[0].size[1])
                target = Image.new('RGB', targetSize)

                left = 0
                right = targetSize[0] // 2
                UNIT_SIZE = targetSize[0] // 2
                for merge in merger:
                    target.paste(merge, (left, 0, right, targetSize[1]))
                    left += UNIT_SIZE
                    right += UNIT_SIZE

                target = target.resize((WIDTH, HEIGHT), Image.ANTIALIAS)
                target.save(imagePath + "/" + str(start + 1) + "-" + str(start + 2) + ".jpg", quality=100)
                start += 2

    if coverPath:
        newCoverPath = outputFolder + "/" + fileName
        if os.path.exists(newCoverPath):
            shutil.rmtree(newCoverPath)
        os.mkdir(newCoverPath)

        images = convert_from_path(coverPath, output_folder=newCoverPath, fmt="jpg", thread_count=2,
                                   output_file="")

        cover = Image.open(images[0].filename)
        size = cover.size
        left = cover.crop((0, 0, size[0] / 2, size[1]))
        right = cover.crop((size[0] / 2, 0, size[0], size[1]))
        bigLeft = left.resize((WIDTH, HEIGHT), Image.ANTIALIAS)
        bigRight = right.resize((WIDTH, HEIGHT), Image.ANTIALIAS)
        bigLeft.save(newCoverPath + "/" + "left.jpg", quality=100)
        bigRight.save(newCoverPath + "/" + "right.jpg", quality=100)
        smallLeft = left.resize((COVER_WIDTH, COVER_HEIGHT), Image.ANTIALIAS)
        smallRight = right.resize((COVER_WIDTH, COVER_HEIGHT), Image.ANTIALIAS)
        smallLeft.save(newCoverPath + "/" + "cover_left.jpg", quality=100)
        smallRight.save(newCoverPath + "/" + "cover_right.jpg", quality=100)


def getTextByPage(self):
    text = u_("")
    content = self["/Contents"].getObject()
    if not isinstance(content, ContentStream):
        content = ContentStream(content, self.pdf)
    # Note: we check all strings are TextStringObjects.  ByteStringObjects
    # are strings where the byte->string encoding was unknown, so adding
    # them to the text here would be gibberish.
    for operands, operator in content.operations:
        if operator == b_("Tj"):
            _text = operands[0]
            if isinstance(_text, TextStringObject):
                text += _text
        elif operator == b_("T*"):
            text += "\n"
        elif operator == b_("'"):
            text += "\n"
            _text = operands[0]
            if isinstance(_text, TextStringObject):
                text += operands[0]
        elif operator == b_('"'):
            _text = operands[2]
            if isinstance(_text, TextStringObject):
                text += "\n"
                text += _text
        elif operator == b_("TJ"):
            for i in operands[0]:
                if isinstance(i, TextStringObject):
                    text += i
            text += "\n"
    return text.replace("\n\n", "\n")


if __name__ == "__main__":
    # start = time.time()
    run()
    # height: 653.622, width: 540.236
    # print('Success! cost time:%ds' % int(time.time() - start))  # cost time: 0.007000923156738281

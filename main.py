from jinja2 import Environment, FileSystemLoader, select_autoescape
import sqlite3
from sqlite3 import Error
from flask import Flask, g, abort, request, jsonify
import os
import json
from datetime import datetime
from jinja2 import Template
from PIL import Image, ExifTags
from itertools import groupby
import glob
import exifread

image_folders = ["images1", "images2"]

app = Flask(__name__, static_folder=os.path.abspath("static"), static_url_path="/static")

env = Environment(
    loader=FileSystemLoader('templates'),
    autoescape=select_autoescape(['html', 'xml'])
)


@app.route('/static/thumbnails/<path:p>')
def thumbnail(p):
    path = get_thumbnail(p)[0]
    if path is None:
        abort(404)
    return app.send_static_file(path)


@app.route('/')
def index():
    template = env.get_template('index.html')
    return template.render(images=find_images(), image_height=300)


image_extensions = [".jpg", ".png", ".jpeg", ".gif"]

thumbnails = dict()
cached_image_info = dict()

for OrientationKey in ExifTags.TAGS.keys():
    if ExifTags.TAGS[OrientationKey] == 'Orientation':
        break


def adjust_rotation(image, exif):
    if OrientationKey in exif:
        if exif[OrientationKey] == 3:
            image = image.rotate(180, expand=True)
        elif exif[OrientationKey] == 6:
            image = image.rotate(270, expand=True)
        elif exif[OrientationKey] == 8:
            image = image.rotate(90, expand=True)
    return image


def get_thumbnail(path):
    assert ".." not in path
    if path not in thumbnails:
        print("Generating thumbnail for " + path)
        try:
            image = Image.open("static/" + path)
        except Exception as e:
            print("Could not open image")
            print(e)
            return None

        exif = dict(image.getexif().items())
        image.thumbnail(size=(1000, 300))
        image = adjust_rotation(image, exif)

        result_path = "thumbnails/" + path
        os.makedirs("static/" + os.path.dirname(result_path), exist_ok=True)
        image.save("static/" + result_path, quality=90)
        thumbnails[path] = (result_path, image.size)

    return thumbnails[path]


def find_images():
    images = []

    for folder in image_folders:
        for path in glob.glob("static/" + folder + "/**", recursive=True):
            if not any(path.endswith(ext) for ext in image_extensions):
                continue

            path = path.replace("static/", "")
            if path in cached_image_info:
                images.append(cached_image_info[path])
            else:
                image = Image.open("static/" + path)

                # exif = dict(image.getexif().items())

                # size = image.size

                accurate = False
                if path in thumbnails:
                    (_, thumbnail_size) = get_thumbnail(path)
                    accurate = True
                else:
                    exif = dict(image.getexif().items())
                    thumbnail_size = image.size
                    if OrientationKey in exif and (exif[OrientationKey] in [6, 8]):
                        thumbnail_size = (thumbnail_size[1], thumbnail_size[0])

                with open("static/" + path, 'rb') as f:
                    exifdata = exifread.process_file(f, details=False)
                
                if 'EXIF DateTimeOriginal' in exifdata:
                    date = datetime.strptime(exifdata['EXIF DateTimeOriginal'].values, r"%Y:%m:%d %H:%M:%S")
                else:
                    date = datetime.now()

                item = (path, thumbnail_size, date)

                if accurate:
                    cached_image_info[path] = item

                images.append(item)

    images.sort(key=lambda x: x[2], reverse=True)
    res = groupby(images, key=lambda x: datetime(year=x[2].year, month=x[2].month, day=x[2].day))
    res = [(x[0], list(x[1])) for x in res]
    return res


if __name__ == '__main__':
    app.run(debug=False)

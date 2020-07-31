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

image_folders = ["images1", "images2"]

app = Flask(__name__, static_folder=os.path.abspath("static"), static_url_path="/static")

env = Environment(
    loader=FileSystemLoader('templates'),
    autoescape=select_autoescape(['html', 'xml'])
)


@app.route('/')
def index():
    template = env.get_template('index.html')
    return template.render(images=find_images(), image_height=300)


image_extensions = [".jpg", ".png", ".jpeg", ".gif"]


def find_images():
    images = []

    for orientation in ExifTags.TAGS.keys():
        if ExifTags.TAGS[orientation] == 'Orientation':
            break
    
    for folder in image_folders:
        for file in os.listdir("static/" + folder):
            if not any(file.endswith(ext) for ext in image_extensions):
                continue

            path = folder + "/" + file
            image = Image.open("static/" + path)

            exif = dict(image.getexif().items())

            size = image.size

            if orientation in exif and (exif[orientation] in [6, 8]):
                size = (size[1], size[0])

            date = datetime.strptime(image.getexif()[36867], r"%Y:%m:%d %H:%M:%S")
            images.append((path, size, date))

    images.sort(key=lambda x: x[2], reverse=True)
    res = groupby(images, key=lambda x: datetime(year=x[2].year, month=x[2].month, day=x[2].day))
    res = [(x[0], list(x[1])) for x in res]
    return res


if __name__ == '__main__':
    app.run(debug=False)

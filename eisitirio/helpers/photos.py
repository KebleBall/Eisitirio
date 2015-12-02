"""Utilities for uploading photos to S3."""

from __future__ import unicode_literals

import uuid
import os

import boto
from PIL import Image

from eisitirio import app
from eisitirio.database import models

APP = app.APP

def save_photo(upload_file):
    filename = str(uuid.uuid4()) + '.' + upload_file.filename.rsplit('.', 1)[1]

    upload_folder = APP.config['TEMP_UPLOAD_FOLDER']

    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    temp_filename = os.path.join(upload_folder, filename)
    thumb_temp_filename = os.path.join(upload_folder, "thumb-" + filename)

    upload_file.save(temp_filename)

    im = Image.open(temp_filename)
    im.thumbnail(APP.config['THUMBNAIL_SIZE'])
    im.save(thumb_temp_filename)

    s3_conn = boto.connect_s3(APP.config['AWS_ACCESS_KEY_ID'],
                              APP.config['AWS_SECRET_ACCESS_KEY'])

    bucket = s3_conn.get_bucket(APP.config['S3_BUCKET'])

    bucket_location = bucket.get_location()
    if bucket_location:
        s3_conn = boto.s3.connect_to_region(
            bucket_location,
            aws_access_key_id=APP.config['AWS_ACCESS_KEY_ID'],
            aws_secret_access_key=APP.config['AWS_SECRET_ACCESS_KEY']
        )
        bucket = s3_conn.get_bucket(APP.config['S3_BUCKET'])

    full_key = bucket.new_key("full/" + filename)
    with open(temp_filename) as temp_file:
        full_key.set_contents_from_file(temp_file)
    full_key.set_acl('public-read')
    full_url = full_key.generate_url(expires_in=0, query_auth=False)

    thumb_key = bucket.new_key("thumb/" + filename)
    with open(thumb_temp_filename) as thumb_temp_file:
        thumb_key.set_contents_from_file(thumb_temp_file)
    thumb_key.set_acl('public-read')
    thumb_url = thumb_key.generate_url(expires_in=0, query_auth=False)

    return models.Photo(filename, full_url, thumb_url)

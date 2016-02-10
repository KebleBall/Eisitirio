"""Utilities for uploading photos to S3."""

from __future__ import unicode_literals

import uuid
import os

import boto
from PIL import Image

from eisitirio import app
from eisitirio.database import db
from eisitirio.database import models

APP = app.APP
DB = db.DB

def get_bucket():
    """Get the Boto bucket object."""
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

    return bucket

def save_photo(upload_file):
    """Save an uploaded photo to S3.

    Saves the uploaded photo to a temporary folder (as set in the config) with
    a UUID based filename, generates a thumbnail, and uploads both images to S3.
    """
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

    bucket = get_bucket()

    full_key = bucket.new_key("full/" + filename)
    full_key.set_contents_from_filename(temp_filename)
    full_key.set_acl('public-read')
    full_url = full_key.generate_url(expires_in=0, query_auth=False)

    thumb_key = bucket.new_key("thumb/" + filename)
    thumb_key.set_contents_from_filename(thumb_temp_filename)
    thumb_key.set_acl('public-read')
    thumb_url = thumb_key.generate_url(expires_in=0, query_auth=False)

    os.unlink(temp_filename)
    os.unlink(thumb_temp_filename)

    return models.Photo(filename, full_url, thumb_url)

def delete_photo(photo):
    """Delete a saved photo from S3.

    Used when a user's account is destroyed, or if they change their photo."""
    bucket = get_bucket()

    bucket.new_key("full/" + photo.filename).delete()
    bucket.new_key("thumb/" + photo.filename).delete()

def rotate_photo(photo, degrees):
    """Rotate a user's photo so that they're the right way up."""
    bucket = get_bucket()

    full_key = bucket.new_key("full/" + photo.filename)
    thumb_key = bucket.new_key("thumb/" + photo.filename)

    upload_folder = APP.config['TEMP_UPLOAD_FOLDER']

    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    temp_filename = os.path.join(upload_folder, photo.filename)
    thumb_temp_filename = os.path.join(upload_folder, "thumb-" + photo.filename)

    full_key.get_contents_to_filename(temp_filename)

    im = Image.open(temp_filename).rotate(degrees)
    im.save(temp_filename)
    im.thumbnail(APP.config['THUMBNAIL_SIZE'])
    im.save(thumb_temp_filename)

    full_key.set_contents_from_filename(temp_filename)
    full_key.set_acl('public-read')
    photo.full_url = full_key.generate_url(expires_in=0, query_auth=False)

    thumb_key.set_contents_from_filename(thumb_temp_filename)
    thumb_key.set_acl('public-read')
    photo.thumb_url = thumb_key.generate_url(expires_in=0, query_auth=False)

    os.unlink(temp_filename)
    os.unlink(thumb_temp_filename)

    DB.session.commit()

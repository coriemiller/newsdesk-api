from flask import Flask, request
from werkzeug.contrib.fixers import ProxyFix
import requests
from viz_checker import viz_checker
from viz_qa import download_viz_html, source_listing_id, viz_qa
from generate_video import generate_video

requests.packages.urllib3.disable_warnings()
app = Flask(__name__)

@app.route('/')
def home():
    return ("\n"
            "        <!doctype html>\n"
            "        <title>Newsdesk API</title>\n"
            "        <h1>Welcome to the Newsdesk API! Visit /video, /viz_check, /source_id</h1>\n"
            "        ")

@app.route('/video')
def make_video():
    if 'template_id' in request.args:
        template_id = request.args['template_id']
    else:
        return 'Hello, visit /video?template_id=123&?listing_id=4567 to generate your video.'
    if 'listing_id' in request.args:
        listing_id = request.args['listing_id']
    else:
        return 'Hello, visit /video?template_id=<template_id>&?listing_id=<listing_id> to generate your video.'

    return generate_video(template_id, listing_id)


@app.route('/viz_check')
def get_url():
    if 'url' in request.args:
        url = request.args['url']
    else:
        return 'Make sure to add the url parameter /viz_check?url=www.article-url/12345.com'
    return viz_checker(url)


@app.route('/source_id')
def get_viz_id():
    if 'viz_id' in request.args:
        viz_id = request.args['viz_id']
    else:
        return 'Make sure to add the url parameter /source_id?viz_id=a1B2c3D4'
    return source_listing_id(download_viz_html(viz_id))

@app.route('/qa')
def check_viz():
    if 'viz_id' in request.args:
        viz_id = request.args['viz_id']
    else:
        return 'Make sure to add the url parameter /qa?viz_id=a1B2c3D4'
    return viz_qa(viz_id)



app.wsgi_app = ProxyFix(app.wsgi_app)

if __name__ == '__main__':
    app.run(host='0.0.0.0')

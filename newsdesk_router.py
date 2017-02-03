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
    return '''
        <!doctype html>
        <title>Newsdesk API</title>
        <h1 style="font-family:Monospace;">Welcome to the Newsdesk API! Visit /video, /viz_check, /source_id, /qa</h1>
        '''

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

@app.route('/qa', methods=['POST', 'GET'])
def check_viz():
    if 'viz_id' in request.args:
        viz_id = request.args['viz_id']
        return viz_qa(viz_id)
    else:
        # return 'Make sure to add the url parameter /qa?viz_id=a1B2c3D4'
        html_string = '''
            <!doctype html>
            <head>
                <title>Q/A</title>
                <link href="//netdna.bootstrapcdn.com/bootstrap/3.3.6/css/bootstrap.min.css" rel="stylesheet" media="screen">
                <style>
                    .container {
                        text-align: center;
                        margin: auto;
                        display: block;
                    }
                    form {
                        display: inline-block;
                        left-margin: auto;
                        right-margin: auto;
                    }
                    table {
                        margin: auto;
                        margin-top: 30px;
                        color: #333;
                        font-family: monospace;
                        width: 640px;
                        border-collapse:
                        collapse; border-spacing: 0;
                    }

                    td, th {
                        border: 1px solid #CCC;
                        height: 30px;
                    }

                    th {
                        background: #F3F3F3;
                        font-weight: bold;
                        text-align: left;
                        padding: 5px;
                    }

                    td {
                        background: #FAFAFA;
                        padding: 5px;
                    }
                </style>
            </head>
            <div class="container">
                <h1>Viz URL</h1>
                <form role="form" method='POST' action='/qa'>
                    <div class="form-group">
                      <input type="text" name="url" class="form-control" id="url-box" placeholder="Enter URL..." style="max-width: 300px;" autofocus required>
                    </div>
                    <button type="submit" class="btn btn-default">Submit</button>
                </form>
            </div>
                '''
        if request.method == "POST":
            try:
                print request.form['url']
                url = request.form['url']
                viz_id = url.replace('https://w.graphiq.com/w/', '')
                # html_string = html_string + viz_qa(viz_id)
            except:
                return "Unable to get URL. Please make sure it's valid and try again."
            html_string = html_string + viz_qa(viz_id)
        return html_string



app.wsgi_app = ProxyFix(app.wsgi_app)

if __name__ == '__main__':
    app.run(host='0.0.0.0')

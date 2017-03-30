from flask import Flask, request, Response, render_template
from werkzeug.contrib.fixers import ProxyFix
import requests
from viz_checker import viz_checker
from viz_qa import download_viz_html, source_listing_id, viz_qa, get_title, get_url_from_code
from generate_video import generate_video
from viz import Viz
import json
import subprocess
import re
import cgi
import sys

reload(sys)
sys.setdefaultencoding('utf8')

# requests.packages.urllib3.disable_warnings()
app = Flask(__name__)


@app.route('/')
def home():
    return '''
        <!doctype html>
        <title>Newsdesk API</title>
        <h1 style="font-family:Monospace;text-align:center;">Welcome to the Newsdesk API!</h1>
        <h2 style="font-family:Monospace;text-align:center;">Visit /video, /viz_check, /source_id, /qa, /qapi, /qa_json</h2>
        <br><br>
        <div style="text-align:center;width:100%;">
        <iframe width="560" height="315" src="https://www.youtube.com/embed/BA17_TvO6vM" frameborder="0" allowfullscreen></iframe>
        </div>
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
        background = requests.get('http://www.bing.com/HPImageArchive.aspx?format=js&idx=0&n=1&mkt=en-US')
        bkgd_json = background.json()
        img_url = 'http://www.bing.com' + bkgd_json['images'][0]['url']
        html_string = '''
            <!doctype html>
            <head>
                <title>Q/A</title>
                <link href="//netdna.bootstrapcdn.com/bootstrap/3.3.6/css/bootstrap.min.css" rel="stylesheet" media="screen">
                <style>
                    body {
                    background: url(''' + img_url + ''') no-repeat center center fixed;
                    -webkit-background-size: cover;
                    -moz-background-size: cover;
                    -o-background-size: cover;
                    background-size: cover;
                    }
                    .container, .container-box {
                    text-align: center;
                    margin: auto;
                    background: white;
                    padding: 1px;
                    padding-bottom: 20px;
                    margin-top: 25px;
                    display: block;
                    }
                    .container-box {
                    width: 230px;
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
            <div class="container-box">
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
                viz_url = request.form['url']
                json_pat = re.compile(r'(.*.com\/w\/|.*\/preview\/)(\w*)')
                matches = json_pat.findall(viz_url)
                viz_id = matches[0][1]
            except:
                return "There was an error!"
            try:
                viz = Viz(viz_id)
                errors = viz.json_response()
                html_string += '''
                            <table>
                            <tr>
                                <th>Error Type</th>
                                <th>Error Message</th>
                            </tr>
                            '''
                # Parse error json and create 1 sentence per error, storing each sentence in error_list
                for item in errors:
                    for key, value in item.iteritems():
                        error_type = key
                        if error_type == 'Timeline errors':
                            for slide, messages in value.iteritems():
                                for message in messages:
                                    html_string = html_string + "<tr><td>" + slide + "</td><td>" + message.encode("utf-8") + "</td></tr>"
                        else:
                            for error_val in value:
                                try:
                                    html_string = html_string + '<tr><td>' + error_type + '</td><td>' + error_val.encode('utf-8') + '</td></tr>'

                                except:
                                    for sub_error in error_val:
                                        html_string = html_string + '<tr><td>' + error_type + '</td><td>' + sub_error.encode('utf-8') + '</td></tr>'
                html_string = html_string + '</table><br><div class="ftb-widget" data-widget-id="' + viz_id + '"></div><script async src="https://s.graphiq.com/rx/widgets.js"></script>'
            except:
                return 'There was an error with the API! Let Corie know.'
                html_string = html_string + viz_qa(viz_id)
        return html_string


@app.route('/qa_json', methods=['GET'])
def json_response():
    if 'viz_id' in request.args:
        viz_id = request.args['viz_id']
        errors = Viz(viz_id).json_response()
        js = json.dumps(errors)
        resp = Response(js, status=200, mimetype='application/json')
        return resp
    else:
        return 'Error'


@app.route('/asana-tag', methods=['GET', 'POST'])
def asanatag():
    html_string = '''
            <!doctype html>
            <head>
                <title>Asana Tag</title>
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
                </style>
                </head>
                    <div class="container">
                    <h1>Asana Tags</h1>
                    <form role="form" method='POST' action='/asana-tag'>
                        <div class="form-group">
                          <br>
                          <input type="text" name="tag-name" class="form-control" id="url-box" placeholder="Tag Name" style="max-width: 300px;" autofocus required>
                          <br>
                          <input type="text" name="alert-id" class="form-control" id="alert-id" placeholder="Alert ID" style="max-width: 300px;" autofocus required>
                        </div>
                        <button type="submit" class="btn btn-default">Submit</button>
                    </form>
                </div>
                '''
    if request.method == "POST":
        tag_name = request.form['tag-name']
        alert_id = request.form['alert-id']
        webhook = 'https://hooks.zapier.com/hooks/catch/708740/mh4uzq?tag_name=' + tag_name + '&alert_id=' + alert_id
        requests.get(webhook)
    return html_string


@app.route('/email', methods=['GET', 'POST'])
def emailFormat():
    background = requests.get('http://www.bing.com/HPImageArchive.aspx?format=js&idx=0&n=1&mkt=en-US')
    bkgd_json = background.json()
    img_url = 'http://www.bing.com' + bkgd_json['images'][0]['url']
    html_string = '''
            <!doctype html>
            <head>
                <title>Email Formatter</title>
                <link href="//netdna.bootstrapcdn.com/bootstrap/3.3.6/css/bootstrap.min.css" rel="stylesheet" media="screen">
                <style>
                body {
                background: url(''' + img_url + ''') no-repeat center center fixed;
                -webkit-background-size: cover;
                -moz-background-size: cover;
                -o-background-size: cover;
                background-size: cover;
                }
                a {
                text-decoration: underline;
                color: #1155CC;
                }
                h1 {
                background: white;
                width: 290px;
                margin: auto;
                display: block;
                padding: 3px;
                }
                .container {
                text-align: center;
                margin: auto;
                display: block;
                padding: 30px;
                }
                .message {
                text-align: left;
                border-style: dashed;
                padding: 30px;
                margin: auto;
                max-width: 60%;
                font-family: sans-serif;
                font-size: 13px;
                background: white;
                }
                form {
                    display: inline-block;
                    left-margin: auto;
                    right-margin: auto;
                }
                </style>
                </head>
                    <div class="container">
                    <h1>Email Formatter</h1>
                    <form role="form" method='POST' action='/email'>
                        <div class="row form-group">
                          <br>
                          <input type="text" name="greeting" class="form-control" id="greeting" placeholder="Greeting [optional]" style="max-width: 500px;" autofocus>
                          <br>
                          <textarea type="textarea" name="intro" class="form-control" id="intro" placeholder="Introduction [optional]" style="max-width: 500px;" autofocus></textarea>
                        </div>
                        <div class="row form-group">
                        <div class="col-md-6">
                          <input type="text" name="url1" class="form-control" id="url1" placeholder="Viz URL" autofocus>
                          <br>
                          <input type="text" name="url2" class="form-control" id="url2" placeholder="Viz URL" autofocus>
                          <br>
                          <input type="text" name="url3" class="form-control" id="url3" placeholder="Viz URL" autofocus>
                          <br>
                          <input type="text" name="url4" class="form-control" id="url4" placeholder="Viz URL" autofocus>
                          <br>
                          <input type="text" name="url5" class="form-control" id="url5" placeholder="Viz URL" autofocus>
                          <br>
                          <input type="text" name="url6" class="form-control" id="url6" placeholder="Viz URL" autofocus>
                          <br>
                          <input type="text" name="url7" class="form-control" id="url7" placeholder="Viz URL" autofocus>
                          <br>
                          <input type="text" name="url8" class="form-control" id="url8" placeholder="Viz URL" autofocus>
                          <br>
                          <input type="text" name="url9" class="form-control" id="url9" placeholder="Viz URL" autofocus>
                          <br>
                          <input type="text" name="url10" class="form-control" id="url10" placeholder="Viz URL" autofocus>
                          <br>
                          <input type="text" name="url11" class="form-control" id="url11" placeholder="Viz URL" autofocus>
                          <br>
                          <input type="text" name="url12" class="form-control" id="url12" placeholder="Viz URL" autofocus>
                          <br>
                          <input type="text" name="url13" class="form-control" id="url13" placeholder="Viz URL" autofocus>
                          <br>
                          <input type="text" name="url14" class="form-control" id="url14" placeholder="Viz URL" autofocus>
                          <br>
                          <input type="text" name="url15" class="form-control" id="url15" placeholder="Viz URL" autofocus>
                        </div>
                        <div class="col-md-6">
                          <input type="text" name="code1" class="form-control" id="code1" placeholder="Embed Code" autofocus>
                          <br>
                          <input type="text" name="code2" class="form-control" id="code2" placeholder="Embed Code" autofocus>
                          <br>
                          <input type="text" name="code3" class="form-control" id="code3" placeholder="Embed Code" autofocus>
                          <br>
                          <input type="text" name="code4" class="form-control" id="code4" placeholder="Embed Code" autofocus>
                          <br>
                          <input type="text" name="code5" class="form-control" id="code5" placeholder="Embed Code" autofocus>
                          <br>
                          <input type="text" name="code6" class="form-control" id="code6" placeholder="Embed Code" autofocus>
                          <br>
                          <input type="text" name="code7" class="form-control" id="code7" placeholder="Embed Code" autofocus>
                          <br>
                          <input type="text" name="code8" class="form-control" id="code8" placeholder="Embed Code" autofocus>
                          <br>
                          <input type="text" name="code9" class="form-control" id="code9" placeholder="Embed Code" autofocus>
                          <br>
                          <input type="text" name="code10" class="form-control" id="code10" placeholder="Embed Code" autofocus>
                          <br>
                          <input type="text" name="code11" class="form-control" id="code11" placeholder="Embed Code" autofocus>
                          <br>
                          <input type="text" name="code12" class="form-control" id="code12" placeholder="Embed Code" autofocus>
                          <br>
                          <input type="text" name="code13" class="form-control" id="code13" placeholder="Embed Code" autofocus>
                          <br>
                          <input type="text" name="code14" class="form-control" id="code14" placeholder="Embed Code" autofocus>
                          <br>
                          <input type="text" name="code15" class="form-control" id="code15" placeholder="Embed Code" autofocus>
                          <br>
                        </div>
                        </div>
                        <button type="submit" class="btn btn-default">Submit</button>
                    </form>
                </div>
                '''
    if request.method == 'POST':
        # test = request.form.getlist('url')
        url_array = []
        title_array = []
        embed_code_array = []
        html_string = html_string + '<div class="container row"><div class="message">'
        # for item in request.form['url']:
        #     print item
        if request.form['greeting']:
            greeting = request.form['greeting']
            html_string = html_string + greeting + '<br><br>'
        if request.form['intro']:
            intro = request.form['intro']
            html_string = html_string + intro + '<br><br>'
        if request.form['url1']:
            url1 = request.form['url1']
            url_array.append(url1)
            title_array.append(get_title(url1))
        if request.form['url2']:
            url2 = request.form['url2']
            url_array.append(url2)
            title_array.append(get_title(url2))
        if request.form['url3']:
            url3 = request.form['url3']
            url_array.append(url3)
            title_array.append(get_title(url3))
        if request.form['url4']:
            url4 = request.form['url4']
            url_array.append(url4)
            title_array.append(get_title(url4))
        if request.form['url5']:
            url5 = request.form['url5']
            url_array.append(url5)
            title_array.append(get_title(url5))
        if request.form['url6']:
            url6 = request.form['url6']
            url_array.append(url6)
            title_array.append(get_title(url6))
        if request.form['url7']:
            url7 = request.form['url7']
            url_array.append(url7)
            title_array.append(get_title(url7))
        if request.form['url8']:
            url8 = request.form['url8']
            url_array.append(url8)
            title_array.append(get_title(url8))
        if request.form['url9']:
            url9 = request.form['url9']
            url_array.append(url9)
            title_array.append(get_title(url9))
        if request.form['url10']:
            url10 = request.form['url10']
            url_array.append(url10)
            title_array.append(get_title(url10))
        if request.form['url11']:
            url11 = request.form['url11']
            url_array.append(url11)
            title_array.append(get_title(url11))
        if request.form['url12']:
            url12 = request.form['url12']
            url_array.append(url12)
            title_array.append(get_title(url12))
        if request.form['url13']:
            url13 = request.form['url13']
            url_array.append(url13)
            title_array.append(get_title(url13))
        if request.form['url14']:
            url14 = request.form['url14']
            url_array.append(url14)
            title_array.append(get_title(url14))
        if request.form['url15']:
            url15 = request.form['url15']
            url_array.append(url15)
            title_array.append(get_title(url15))

        if bool(url_array) != False:
            for url, title in zip(url_array, title_array):
                html_string = html_string + '<a href="' + url + '">' + title + '</a><br><br>'

        if request.form['code1']:
            code1 = request.form['code1']
            url1 = get_url_from_code(code1)
            url_array.append(url1)
            title_array.append(get_title(url1))
            embed_code_array.append(cgi.escape(code1))
        if request.form['code2']:
            code2 = request.form['code2']
            url2 = get_url_from_code(code2)
            url_array.append(url2)
            title_array.append(get_title(url2))
            embed_code_array.append(cgi.escape(code2))
        if request.form['code3']:
            code3 = request.form['code3']
            url3 = get_url_from_code(code3)
            url_array.append(url3)
            title_array.append(get_title(url3))
            embed_code_array.append(cgi.escape(code3))
        if request.form['code4']:
            code4 = request.form['code4']
            url4 = get_url_from_code(code4)
            url_array.append(url4)
            title_array.append(get_title(url4))
            embed_code_array.append(cgi.escape(code4))
        if request.form['code5']:
            code5 = request.form['code5']
            url5 = get_url_from_code(code5)
            url_array.append(url5)
            title_array.append(get_title(url5))
            embed_code_array.append(cgi.escape(code5))
        if request.form['code6']:
            code6 = request.form['code6']
            url6 = get_url_from_code(code6)
            url_array.append(url6)
            title_array.append(get_title(url6))
            embed_code_array.append(cgi.escape(code6))
        if request.form['code7']:
            code7 = request.form['code7']
            url7 = get_url_from_code(code7)
            url_array.append(url7)
            title_array.append(get_title(url7))
            embed_code_array.append(cgi.escape(code7))
        if request.form['code8']:
            code8 = request.form['code8']
            url8 = get_url_from_code(code8)
            url_array.append(url8)
            title_array.append(get_title(url8))
            embed_code_array.append(cgi.escape(code8))
        if request.form['code9']:
            code9 = request.form['code9']
            url9 = get_url_from_code(code9)
            url_array.append(url9)
            title_array.append(get_title(url9))
            embed_code_array.append(cgi.escape(code9))
        if request.form['code10']:
            code10 = request.form['code10']
            url10 = get_url_from_code(code10)
            url_array.append(url10)
            title_array.append(get_title(url10))
            embed_code_array.append(cgi.escape(code10))
        if request.form['code11']:
            code11 = request.form['code11']
            url11 = get_url_from_code(code11)
            url_array.append(url11)
            title_array.append(get_title(url11))
            embed_code_array.append(cgi.escape(code11))
        if request.form['code12']:
            code12 = request.form['code12']
            url12 = get_url_from_code(code12)
            url_array.append(url12)
            title_array.append(get_title(url12))
            embed_code_array.append(cgi.escape(code12))
        if request.form['code13']:
            code13 = request.form['code13']
            url13 = get_url_from_code(code13)
            url_array.append(url13)
            title_array.append(get_title(url13))
            embed_code_array.append(cgi.escape(code13))
        if request.form['code14']:
            code14 = request.form['code14']
            url14 = get_url_from_code(code14)
            url_array.append(url14)
            title_array.append(get_title(url14))
            embed_code_array.append(cgi.escape(code14))
        if request.form['code15']:
            code15 = request.form['code15']
            url15 = get_url_from_code(code15)
            url_array.append(url15)
            title_array.append(get_title(url15))
            embed_code_array.append(cgi.escape(code15))

        for url, title, embed_code in zip(url_array, title_array, embed_code_array):
            html_string = html_string + '<a href="' + url + '">' + title + '</a><br><br>' + embed_code + '<br><br>'

        html_string = html_string + '</div></div>'
    return html_string


@app.route('/qapi', methods=['GET', 'POST'])
def initialize_qapi():
    background = requests.get('http://www.bing.com/HPImageArchive.aspx?format=js&idx=0&n=1&mkt=en-US')
    bkgd_json = background.json()
    img_url = 'http://www.bing.com' + bkgd_json['images'][0]['url']
    html_string = '''
            <!doctype html>
            <head>
                <title>Q/A</title>
                <link href="//netdna.bootstrapcdn.com/bootstrap/3.3.6/css/bootstrap.min.css" rel="stylesheet" media="screen">
                <style>
                body {
                background: url(''' + img_url + ''') no-repeat center center fixed;
                -webkit-background-size: cover;
                -moz-background-size: cover;
                -o-background-size: cover;
                background-size: cover;
                }
                .container, .container-box {
                text-align: center;
                margin: auto;
                background: white;
                padding: 1px;
                padding-bottom: 20px;
                margin-top: 25px;
                display: block;
                }
                .container {
                width: 450px;
                }
                .container-box {
                width: 230px;
                }
                form {
                    display: inline-block;
                    left-margin: auto;
                    right-margin: auto;
                }
                </style>
                </head>
                <div class="container-box">
                    <h1>Viz URL</h1>
                    <form role="form" method='POST' action='/qapi'>
                        <div class="form-group">
                          <input type="text" name="url" class="form-control" id="url-box" placeholder="Enter URL..." style="max-width: 300px;" autofocus required>
                        </div>
                        <button type="submit" class="btn btn-default">Submit</button>
                    </form>
                </div>
                '''
    if request.method == "POST":
        try:
            viz_url = request.form['url']
            json_pat = re.compile(r'(.*.com\/w\/|.*\/preview\/)(\w*)')
            matches = json_pat.findall(viz_url)
            viz_id = matches[0][1]
        except:
            return 'Error parsing viz ID from URL. Make sure to submit a viz preview link!'
        try:
            viz = Viz(viz_id)
            errors = viz.json_response()
            error_list = []
            # Parse error json and create 1 sentence per error, storing each sentence in error_list
            for item in errors:
                for key, value in item.iteritems():
                    error_type = key
                    if error_type == 'Timeline errors':
                        for slide, messages in value.iteritems():
                            for message in messages:
                                error = slide + ': ' + message.encode('utf-8')
                                error_list.append(error)
                    else:
                        for error_val in value:
                            try:
                                error = error_type + ': ' + error_val.encode('utf-8')
                                error_list.append(error)
                            except:
                                for sub_error in error_val:
                                    error = error_type + ': ' + sub_error.encode('utf-8')
                                    error_list.append(error)
            # Create new QA task
            task_data = '"{\\"data\\": {  \\"notes\\" : \\"' + viz_url + '\\" ,  \\"projects\\" : \\"244458016124389\\" , \\"name\\" : \\"' + viz.title + '\\" } }"'
            task_shell_command = '/usr/bin/curl -s --request POST -H "Authorization: Bearer 0/a3244bb3177f3e0c7242c459c4324863" -H "Content-Type: application/json" https://app.asana.com/api/1.0/tasks -d ' + task_data
            new_task = subprocess.check_output(task_shell_command, shell=True)
            new_task_id = json.loads(new_task)['data']['id']
            task_url = 'https://app.asana.com/0/244458016124389/' + str(new_task_id)
            subtask_url = 'https://app.asana.com/api/1.0/tasks/' + str(new_task_id) + '/subtasks'
            html_string = html_string + '<div class="container">' + task_url + '<br><a href="' + task_url + '" target="_blank">Go!</a></div>'

            # Post each error to Asana
            for error_text in sorted(error_list, reverse=True):
                subtask_data = '"{\\"data\\": {  \\"name\\" : \\"' + error_text + '\\"  } }"'
                subtask_shell_command = '/usr/bin/curl -s --request POST -H "Authorization: Bearer 0/a3244bb3177f3e0c7242c459c4324863" -H "Content-Type: application/json" ' + subtask_url + ' -d ' + subtask_data
                subprocess.check_output(subtask_shell_command, shell=True)

            # QA 1 and 2 subtasks
            qa2_shell = '/usr/bin/curl -s --request POST -H "Authorization: Bearer 0/a3244bb3177f3e0c7242c459c4324863" -H "Content-Type: application/json" ' + subtask_url + ' -d "{\\"data\\": {  \\"name\\" : \\"QA 2\\"  } }"'
            qa1_shell = '/usr/bin/curl -s --request POST -H "Authorization: Bearer 0/a3244bb3177f3e0c7242c459c4324863" -H "Content-Type: application/json" ' + subtask_url + ' -d "{\\"data\\": {  \\"name\\" : \\"QA 1\\"  } }"'
            subprocess.check_output(qa2_shell, shell=True)
            subprocess.check_output(qa1_shell, shell=True)
        except:
            return 'There was an error with the API- let Corie know!'
    return html_string


@app.route('/digest', methods=['GET', 'POST'])
def build_digest():
    background = requests.get('http://www.bing.com/HPImageArchive.aspx?format=js&idx=0&n=1&mkt=en-US')
    bkgd_json = background.json()
    bkgd_url = 'http://www.bing.com' + bkgd_json['images'][0]['url']
    if request.method == 'GET':
        return render_template('digest_page.html', bkgd_url=bkgd_url)
    elif request.method == 'POST':
        data = {}
        viz_list = [request.form['viz_image_1'], request.form['viz_image_2'], request.form['viz_image_3'],
                    request.form['viz_image_4']]
        url_list = []
        for item in viz_list:
            json_pat = re.compile(r'(.*.com\/w\/|.*\/preview\/)(\w*)')
            matches = json_pat.findall(item)
            viz_id = matches[0][1]
            url = 'https://www.graphiq.com/API/visualizations/images/' + viz_id
            # headers = {
            #     'User-Agent': 'Mozilla/5.0'
            # }
            # r = requests.post(url, headers=headers)
            r = requests.post(url)
            image_url = r.text
            url_list.append(image_url)

        data['bkgd_url'] = bkgd_url
        data['headline_1'] = request.form['headline_1']
        data['viz_image_1'] = url_list[0]
        data['backlink_1'] = request.form['backlink_1']
        data['headline_2'] = request.form['headline_2']
        data['viz_image_2'] = url_list[1]
        data['backlink_2'] = request.form['backlink_2']
        data['headline_3'] = request.form['headline_3']
        data['viz_image_3'] = url_list[2]
        data['backlink_3'] = request.form['backlink_3']
        data['headline_4'] = request.form['headline_4']
        data['viz_image_4'] = url_list[3]
        data['backlink_4'] = request.form['backlink_4']
        return render_template('digest_result.html', data=data)


app.wsgi_app = ProxyFix(app.wsgi_app)

if __name__ == '__main__':
    app.run(host='0.0.0.0')

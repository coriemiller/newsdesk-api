import urllib
from unidecode import unidecode
import requests
import re
import json
from flask import Response
from bs4 import BeautifulSoup
from datetime import datetime
# BAD but disables warnings from unidecode
import warnings
import sys
from textgears_key import KEY

reload(sys)
sys.setdefaultencoding('utf8')
warnings.filterwarnings("ignore")

requests.packages.urllib3.disable_warnings()


def get_url_from_code(code):
    viz_url = ''
    json_pat = re.compile(r'data-widget-id="(\w*)"|\/w\/(.*?)"')
    matches = json_pat.findall(code)
    for vizid in matches[0]:
        if vizid != '':
            viz_url = 'https://w.graphiq.com/w/' + vizid
    return viz_url


def get_title(url):
    json_pat = re.compile(r'(.*.com\/w\/|.*\/preview\/)(\w*)')
    matches = json_pat.findall(url)
    viz_id = matches[0][1]
    soup = make_soup(download_viz_html(viz_id))
    title = soup.find("title").string.strip()
    return title


def source_listing_id(html):
    json_pattern = re.compile(r'FTB=(.*?})(;)')
    matches = json_pattern.findall(html)
    jsondata = json.loads(matches[0][0])
    try:
        response_obj = jsondata['sources']
    except KeyError:
        response_obj = {'source_ids': []}
    js = json.dumps(response_obj)
    resp = Response(js, status=200, mimetype='application/json')
    return resp


def download_viz_html(viz_id):
    url = 'https://w.graphiq.com/w/' + viz_id
    headers = {
        'User-Agent': 'Mozilla/5.0'
    }
    r = requests.get(url, headers=headers)
    return r.content


def make_soup(html):
    soup = BeautifulSoup(html.replace('&nbsp;', ' '), 'html.parser')
    return soup


def test_update_date(soup):
    try:
        visible_date = soup.find("div", class_="ww-source").find("a").previous_sibling
        string = re.sub(';.*', '', visible_date.string.strip().replace('As of ', '').replace('.', '').replace(',', '').replace(' ', ''))
    except AttributeError:
        message = ['No update date visible']
        return message
    try:
        datetime_object = datetime.strptime(string, '%B%d%Y')
    except ValueError:
        try:
            datetime_object = datetime.strptime(string, '%Y')
        except ValueError:
            try:
                datetime_object = datetime.strptime(string, '%B%Y')
            except ValueError:
                message = ['No update date visible.']
                return message
    if datetime_object.date() <= datetime.today().date() and datetime_object.date() > datetime.strptime('January132008',
                                                                                                        '%B%d%Y').date():
        return 'good'
    elif datetime_object.date() > datetime.today().date():
        message = ['According to my crystal ball, your date is in the future...']
        return message
    else:
        message = ["You're living in the past. Maybe too far in the past. Your date is before 2008. Double-check it please!"]
        return message


def textgears_check(text):
    clean_text = re.sub(r'<.*\\?>', '', text)
    # url = 'http://api.textgears.com/check.php?text=' + unidecode(clean_text.replace('"', '').replace('&', '%26')) + '&key=NmN7OLAGeZtPRboc'
    url = 'http://api.textgears.com/check.php?text=' + clean_text.replace('"', '') + '&key=' + KEY
    r = requests.get(url)
    results = r.json()
    i = 0
    message = []
    try:
        if results['score'] != 100:
            while i < len(results['errors']):
                bad = results['errors'][i]['bad']
                fix = results['errors'][i]['better']
                # check for dumb corrections that just add a space out front
                if bad != ''.join(fix).replace(' ', '') and bad != '"':
                    message.append(bad + ' -> ' + ', '.join(fix))
                i += 1
        else:
            message='good'
    except:
        message = 'good'
    return message


def check_title(soup):
    title = soup.find("title").string.strip()
    return textgears_check(title)


def check_subheader(soup):
    try:
        subheader = soup.find("div", class_="ww-subheader-input").string.strip()
        return textgears_check(subheader)
    except AttributeError:
        return 'good'


def check_source_text(soup):
    sources = soup.find_all("div", class_="dsrc-desc")
    messages = []
    for source in sources:
        message = textgears_check(source.string.strip())
        if message != 'good':
            messages.append(message)
    return messages


def widgets_json(html):
    json_pattern = re.compile(r'widgets=(.*?})(;)')
    matches = json_pattern.findall(html)
    jsondata = json.loads(matches[0][0])
    return jsondata


def timeline_text(widgets_json):
    i = 0
    messages = []
    for randomvalue in widgets_json:
        try:
            timeline_events = widgets_json[randomvalue]['options']['timeline']['events']
            while i < len(timeline_events):
                text = timeline_events[i]['text']['text']
                message = textgears_check(text)
                i += 1
                # this gets handles the case where a slide has no errors
                if message == 'good':
                    messages.append(['good'])
                else:
                    messages.append(message)
        except KeyError:
            continue
    return messages


def static_annotations(widgets_json):
    i = 0
    messages = []
    for randomvalue in widgets_json:
        try:
            annotations_iterable = widgets_json[randomvalue]['options']['chart']['staticAnnotations']
            while i < len(annotations_iterable):
                text = str(annotations_iterable[i]['text'])
                message = textgears_check(text)
                i += 1
                if message != 'good':
                    messages.append(message)
        except KeyError:
            continue
    return messages


def value_labels(widgets_json):
    i = 0
    messages = []
    for randomvalue in widgets_json:
        try:
            labels = widgets_json[randomvalue]['options']['chart']['series']
            while i < len(labels):
                text = labels[i]['label']
                message = textgears_check(text)
                i += 1
                if message != 'good':
                    messages.append(message)
        except KeyError:
            continue
    return messages


def field_defs(widgets_json):
    messages = []
    for randomvalue in widgets_json:
        try:
            defs = widgets_json[randomvalue]['srp_data']['defs']
            for item in defs:
                if bool(item) != False:
                    label = item['name']
                    if label != 'ID' and label != '':
                        message = textgears_check(label)
                        if message != 'good':
                            messages.append(message)
        except TypeError:
            continue
    return messages


def viz_qa(viz_id):
    response = {}
    html = download_viz_html(viz_id)
    soup = make_soup(html)
    widgets_jsondata = widgets_json(html)
    update_date_message = test_update_date(soup)
    title_message = check_title(soup)
    subheader_message = check_subheader(soup)
    source_text_message = check_source_text(soup)
    static_annotations_message = static_annotations(widgets_jsondata)
    value_labels_message = value_labels(widgets_jsondata)
    timeline_message = timeline_text(widgets_jsondata)
    if update_date_message != 'good':
        response["update_date"] = update_date_message
    if title_message != 'good':
        response["title"] = title_message
    if subheader_message != 'good':
        response["subheader"] = subheader_message
    if bool(source_text_message):
        response["source_text"] = source_text_message
    if bool(static_annotations_message):
        response["static_annotations"] = static_annotations_message
    if bool(value_labels_message):
        response["legend"] = value_labels_message
    if bool(timeline_message):
        i = 1
        for slide in timeline_message:
            response_label = 'Timeline slide ' + str(i)
            # filter out slides with no errors
            if ''.join(slide) != 'good' and bool(slide) != False:
                response[response_label] = slide
            i += 1
    if bool(response):
        # js = json.dumps(response)
        # resp = Response(js, status=200, mimetype='application/json')
        # return resp
        html_string = '''
        <table>
        <tr>
            <th>Error Type</th>
            <th>Error Message</th>
        </tr>
        '''
        # for error_type in response.keys():
        for error_type in sorted(response.iterkeys()):
            i=0
            while i < len(response[error_type]):
                if isinstance(response[error_type][i], list):
                    error_message = ', '.join(response[error_type][i])
                else:
                    error_message = (response[error_type][i])
                html_string = html_string + '<tr><td>' + error_type + '</td><td>' + error_message + '</td></tr>'
                i += 1
        html_string = html_string + '</table><br><div class="ftb-widget" data-widget-id="' + viz_id +'"></div><script async src="https://s.graphiq.com/rx/widgets.js"></script>'
        return html_string
    else:
        return '''
        <!doctype html>
        <title>Congrats!</title>
        <div style="text-align:center;width:100%;">
        <h1>Congrats!!!1!1!!!!</h1>
        <h2>I didn't find any errors.</h2>
        <iframe src="//giphy.com/embed/ytwDCq9aT3cgEyyYVO?hideSocial=true" width="480" height="360" frameborder="0" class="giphy-embed" allowfullscreen=""></iframe>
        </div>
        '''


if __name__ == '__main__':
    # 2FYJG1vV8ZT - sports, many sources, no update date
    # 65Wnn5tdeN7 - as of jan 11
    # iEAMmdcjcJ7 - update date, multiple sources
    # hsRsO5LvQTH - only year
    # 7BIwkQt6Xpb - single number day
    # acHbvVSsqS9 - title = Inaguration is happebing today
    # print check_source_text(make_soup(download_viz_html('7BIwkQt6Xpb')))
    # print value_labels(widgets_json(download_viz_html('idYAIsge8Z')))
    print textgears_check('here is my text')

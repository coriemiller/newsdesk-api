import requests
import re
import json
from flask import Response


def viz_checker(url):
    r = requests.get(url)
    viz_pattern = re.compile(
        r'(((w|s).graphiq.com)|(pointafter.com)|(insidegov.com)|(findthehome.com)|(allpatents.com)|(axlegeeks.com)|(careertrends.com)|(credio.com)|(findthecompany.com)|(findthedata.com)|(gearsuite.com)|(healthgrove.com)|(homeowl.com)|(mooseroots.com)|(petbreeds.com)|(prettyfamous.com)|(softwareinsider.com)|(specout.com)|(underthelabel.com)|(wanderbat.com)|(weatherdb.com))')
    viz_check = viz_pattern.findall(r.content)
    if viz_check == None or viz_check == [] or viz_check == '':
        data = {
            'url': url,
            'viz_present': 'false',
            'viz_id': []
        }
    else:
        pattern = re.compile(
            r'(w.graphiq.com(\/|\\u002F|&#x2f;)(vlp|w)(\/|\\u002F|&#x2f;)(.*?)("| |$|\\|\?))|(data-widget-id=\\?"(.{10,14})\\?")')
        matches = pattern.findall(r.content)
        all_viz_ids = []
        for match in matches:
            if match[4] != '':
                all_viz_ids.append(match[4])
            if match[7] != '':
                all_viz_ids.append(match[7].replace('\\', ''))
        viz_id = []
        [viz_id.append(i) for i in all_viz_ids if not viz_id.count(i)]
        data = {
            'url': url,
            'viz_present': 'true',
            'viz_id': viz_id
        }
    js = json.dumps(data)
    resp = Response(js, status=200, mimetype='application/json')
    return resp

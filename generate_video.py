import requests
import json
from flask import Response

def generate_video(template_id, listing_id):
    url = 'https://api.graphiq.com/video/generate'
    headers = {
        'content-type': "multipart/form-data; boundary=---011000010111000001101001",
        'cache-control': "no-cache",
    }
    payload = "-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"data\"\r\n\r\n{\"tpl\": " + str(
        template_id) + ", \"item_ids\": [" + str(listing_id) + "]}\r\n-----011000010111000001101001--"
    r = requests.post(url, data=payload, headers=headers)

    text_json = json.loads(str(r.text))
    errors = text_json['errors']
    success = text_json['success']
    feather_id = text_json['id']
    video_img = text_json['video_img']
    video_url = text_json['video_url']
    status_url = 'https://api.graphiq.com/video/status?id=' + feather_id
    data = {
        'errors': errors,
        'success': success,
        'feather_id': feather_id,
        'video_img': video_img,
        'video_url': video_url,
        'status_url': status_url
    }
    js = json.dumps(data)
    resp = Response(js, status=200, mimetype='application/json')
    return resp

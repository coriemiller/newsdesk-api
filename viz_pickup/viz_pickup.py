from flask import Flask, Response, jsonify, request
import requests
import json
import re

app = Flask(__name__)

# @app.route('/viz_check/<path:url>')
@app.route('/viz_check')
def viz_checker():
	if 'url' in request.args:
		url = request.args['url']
	else:
		return 'Make sure to add the url parameter /viz_check?url=www.article-url/12345.com'
	r = requests.get(url)
	viz_pattern = re.compile(r'(((w|s).graphiq.com)|(pointafter.com)|(insidegov.com)|(findthehome.com)|(allpatents.com)|(axlegeeks.com)|(careertrends.com)|(credio.com)|(findthecompany.com)|(findthedata.com)|(gearsuite.com)|(healthgrove.com)|(homeowl.com)|(mooseroots.com)|(petbreeds.com)|(prettyfamous.com)|(softwareinsider.com)|(specout.com)|(underthelabel.com)|(wanderbat.com)|(weatherdb.com))')
	viz_check = viz_pattern.findall(r.content)
	# viz_check = re.match(r'(w|s).graphiq.com', r.content)
	if viz_check == None or viz_check == [] or viz_check == '':
		data = {
			'url' : url,
			'viz_present': 'false',
			'viz_id' : []
		}
	else:
		pattern = re.compile(r'(w.graphiq.com(\/|\\u002F|&#x2f;)(vlp|w)(\/|\\u002F|&#x2f;)(.*?)("| |$|\\|\?))|(data-widget-id="(.{10,14})")')
		matches = pattern.findall(r.content)
		all_viz_ids = []
		for match in matches:
			if match[4] != '':
				all_viz_ids.append(match[4])
			if match[7] != '':
				all_viz_ids.append(match[7])
		viz_id = []
		[viz_id.append(i) for i in all_viz_ids if not viz_id.count(i)]		
		data = {
			'url': url,
			'viz_present': 'true',
			'viz_id' : viz_id
		}
	js = json.dumps(data)
	print js
	resp = Response(js, status=200, mimetype='application/json')

if __name__ == '__main__':
    # app.run(host='0.0.0.0')
	url = 'http://komonews.com/news/nation-world/biden-in-2020-with-a-smile-he-says-hes-not-ruling-it-out'
	url = 'http://www.lifezette.com/polizette/huntsman-state-speculation-gets-prickly-reception/'
	url = 'http://www.independent.co.uk/news/world/europe/germany-burqa-burka-ban-veils-angela-merkel-cdu-muslims-speech-refugee-crisis-elections-term-vote-a7458536.html'
	url = 'http://www.forbes.com/sites/alanohnsman/2016/12/05/vw-is-the-latest-carmaker-to-jump-into-ubers-mobility-business/#2dfb24fe1518'
	url_list = ['http://www.usatoday.com/story/news/world/2016/12/02/europol-isil-could-start-car-bombing-kidnapping-europe/94796972/', 
		'http://www.aol.com/article/2016/12/06/al-gore-had-an-extremely-interesting-meeting-with-donald-trump/21621475/',
		'http://www.foxnews.com/world/2016/12/06/merkel-calls-for-burqa-ban-in-germany.html',
		'http://finance.yahoo.com/news/ap-too-quiet-set-filming-050250520.html',
		'http://www.nbcnews.com/news/us-news/suicide-14-i-have-racked-my-brain-trying-understand-n686036',
		'http://www.cbssports.com/nfl/news/percy-harvins-comeback-is-over-after-just-two-games-with-the-bills/',
		'http://nypost.com/2016/12/05/carson-wentzs-rookie-plunge-from-phenom-to-exposed/',
		'https://www.yahoo.com/news/trump-heads-back-road-thank-083638064.html']
	url_list = ['http://www.msn.com/en-us/sports/nfl/giants-fullback-nikita-whitlock-says-burglars-left-racial-messages-at-home/ar-AAligRK']
	for url in url_list:
		r = requests.get(url)
		viz_pattern = re.compile(r'(((w|s).graphiq.com)|(pointafter.com)|(insidegov.com)|(findthehome.com)|(allpatents.com)|(axlegeeks.com)|(careertrends.com)|(credio.com)|(findthecompany.com)|(findthedata.com)|(gearsuite.com)|(healthgrove.com)|(homeowl.com)|(mooseroots.com)|(petbreeds.com)|(prettyfamous.com)|(softwareinsider.com)|(specout.com)|(underthelabel.com)|(wanderbat.com)|(weatherdb.com))')
		viz_check = viz_pattern.findall(r.content)
		print r.content
		# viz_check = re.match(r'(w|s).graphiq.com', r.content)
		if viz_check == None or viz_check == [] or viz_check == '':
			data = {
				'url' : url,
				'viz_present': 'false',
				'viz_id' : []
			}
		else:
			pattern = re.compile(r'(w.graphiq.com(\/|\\u002F|&#x2f;)(vlp|w)(\/|\\u002F|&#x2f;)(.*?)("| |$|\\|\?))|(data-widget-id=\\?"(.{10,14})\\?")')
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
				'viz_id' : viz_id
			}
		js = json.dumps(data)
		print js
		resp = Response(js, status=200, mimetype='application/json')
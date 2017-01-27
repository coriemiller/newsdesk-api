__author__ = 'ashwinsinghania'
import sys

reload(sys)
sys.setdefaultencoding('utf-8')
from flask import Flask
from flask import request
from flask import jsonify
from crossDomainAccess import crossdomain
from RegisterIndicators import *
from ProcessRawData import *
from Upload import UploadParse
import traceback
import os
from ftbUtils.Logger import Logger

LOG_PATH = os.path.join(os.path.dirname(__file__), 'log.txt')
LOGGER = Logger(LOG_PATH).getLogger()

app = Flask(__name__)


@app.route('/', methods=['GET'])
def home():
    return 'Welcome to the Time Series API!'


@app.route('/register', methods=['POST', 'GET'])
def register_tracker():
    """
    Takes in meta information about a series
    :return: list of dictionaries containing indicator, indicator_id, and source
    """
    if request.method == 'POST':
        try:
            LOGGER.info("About to work on /Register of JSON Block: {} characters".format(str(len(request.data))))
            if request.form['data']:
                encoded_data = request.form['data'].encode('utf-8')
                return iterate_over_list_of_indicators(encoded_data)
            else:
                LOGGER.error("ISSUE: Data not received")
                raise RegisterParseError("No data received")

        except:
            LOGGER.error(traceback.format_exc())
            exception, error, trace = sys.exc_info()
            raise RegisterParseError(error.args)

    else:
        return '''
        <!doctype html>
        <title>Register a Series</title>
        <h1>Register a Series</h1>
        <h2>Input your JSON string</h2>
        <form action="" method=post enctype=application/x-www-form-urlencoded>
            <p><input type="text" name="data">
               <input type=submit value=Upload>
        </form>
        '''


@app.route('/raw-data', methods=['POST', 'GET'])
def import_data():
    """
    Takes in series time data
    :return: status of call: "Success" or error
    """
    if request.method == 'POST':
        try:
            LOGGER.info("About to work on /Raw-Data of JSON Block: {} characters".format(len(request.form['data'])))
            if request.form['data']:
                encoded_data = request.form['data'].encode('utf-8')
                response = process_incoming_raw_data_json(encoded_data)
                if response == "Complete":
                    return response
                else:
                    raise RawDataParseError(response)
            LOGGER.error("ISSUE: Data not received")
            raise RawDataParseError("Data not Received")

        except:
            LOGGER.error(traceback.format_exc())
            exception, error, trace = sys.exc_info()
            raise RawDataParseError(error.args)

    else:
        return '''
        <!doctype html>
        <title>Send Raw Data</title>
        <h1>Send Raw Data</h1>
        <h2>Input your JSON string</h2>
        <form action="" method=post enctype=application/x-www-form-urlencoded>
            <p><input type="text" name="data">
               <input type=submit value=Upload>
        </form>
        '''


@app.route('/upload', methods=['POST', 'GET'])
@crossdomain(origin='*')
def upload_file():
    """
    Takes in a structured csv of time data
    :return: status of call: success or error
    """
    if request.method == 'POST':
        allowed_extensions = ['csv']
        upload = request.files['file']
        lid = request.form['lid']
        f = UploadParse(upload, allowed_extensions, lid)
        if upload and f.allowed_extension():
            if f.data_check():
                return 'SUCCESS: {}'.format(f.status)
            else:
                raise InvalidFile('Wrong field names. Please conform to standards')
        else:
            raise InvalidFile('Wrong File Type')

    else:
        return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form action="" method=post enctype=multipart/form-data>
      <p><input type=file name=file>
         <input type="text" name="lid">
         <input type=submit value=Upload>
    </form>
    '''


class InvalidFile(Exception):
    """
    Error handling for upload endpoint
    """
    status_code = 400

    def __init__(self, message, status_code=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code

    def to_dict(self):
        rv = {'message': self.message}
        return rv


class RegisterParseError(Exception):
    """
    Error handling for register endpoint
    """
    status_code = 400

    def __init__(self, message, status_code=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code

    def to_dict(self):
        rv = {'message': self.message}
        return rv


class RawDataParseError(Exception):
    """
    Error handling for raw-data endpoint
    """
    status_code = 400

    def __init__(self, message, status_code=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code

    def to_dict(self):
        rv = {'message': self.message}
        return rv


@app.errorhandler(InvalidFile)
@crossdomain(origin='*')
def handle_invalid_file(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.errorhandler(RegisterParseError)
def handle_register_error(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.errorhandler(RawDataParseError)
def handle_register_error(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


if __name__ == '__main__':
    app.run(host='0.0.0.0')
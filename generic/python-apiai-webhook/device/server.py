# Flask app should start in global layout
from __future__ import print_function
from future.standard_library import install_aliases
install_aliases()

from urllib.parse import urlparse, urlencode
from urllib.request import urlopen, Request
from urllib.error import HTTPError

import json
import os
import thread

from flask import Flask
from flask import request
from flask import make_response

app = Flask(__name__)

callback_function = None

@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)

    res = callback_function(req)
    res = json.dumps(res, indent=4)

    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r


def init_server(port, request_function):
    print("Starting app on port %d" % port)
    global callback_function
    callback_function = request_function
    app.run(debug=False, port=port, host='0.0.0.0')

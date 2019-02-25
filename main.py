from flask import Flask, request, make_response, jsonify, send_file, session
from util import zju, pool
import json
app = Flask(__name__)
pool = pool()


@app.route('/')
def hello_world():
    return 'Hello World!'

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    obj = zju(username, password)
    status = obj.login()

    res =  {
        'status': status
    }

    if status:
        res['msg'] = 'login ok'
        pool.save(username, obj)
    else:
        res['msg'] = 'login fail'

    if not status:
        response = make_response(jsonify(res), 200)
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
    
    else:
        merc = obj.get_ecard()
        res['merc'] = merc
        response = make_response(jsonify(res), 200)
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response



if __name__ == '__main__':
    app.run(port=8000)

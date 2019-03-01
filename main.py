from flask import Flask, request, make_response, jsonify, send_file, session
from util import zju, pool
import threading
app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    sess = zju(username, password)

    res = {}

    try:
        status = sess.login()
    except Exception as e:
        res['status'] = False
        res['msg'] = 'login error'
        response = make_response(jsonify(res), 200)
        response.headers['Access-Control-Allow-Origin'] = '*'
        del sess
        return response

    res['status'] = status
    res['msg'] = 'login ok' if status else 'login fail'

    if not status:
        response = make_response(jsonify(res), 200)
        response.headers['Access-Control-Allow-Origin'] = '*'
        del sess
        return response
    else:
        try:
            sess.go(res)
        except Exception as e:
            res['status'] = False
            res['msg'] = 'fetch error'
            response = make_response(jsonify(res), 200)
            response.headers['Access-Control-Allow-Origin'] = '*'
            del sess
            return response
        response = make_response(jsonify(res), 200)
        response.headers['Access-Control-Allow-Origin'] = '*'
        del sess
        return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)

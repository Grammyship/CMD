import sys
sys.path.append('../')
from flask import Flask, render_template, request
import json
from search import CMD

searchHandler = CMD("../config.ini")
if searchHandler is None:
    print("CMD init failed")
    exit(0)

app = Flask(__name__)



@app.route('/')
def main():
    return render_template('index.html')

@app.route('/api/search', methods=['GET'])
def search():
    result = searchHandler.search_documents_by_keyword(request.args.get('keyword'), 20)
    print(request.args.get('keyword'))
    return result

@app.route('/api/detail', methods=['GET'])
def detail():
    data = searchHandler.search_document_by_ID(request.args.get('id'))
    print(request.args.get('id'))
    result = {
        "id": str(data["_id"]),
        "content": data["judgement"],
        "court": data["court"],
        "no": data["no"],
    }
    return result

@app.route('/api/related', methods=['GET'])
def related():
    data = searchHandler.analysis_related_issues(request.args.get('id'))
    return data

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
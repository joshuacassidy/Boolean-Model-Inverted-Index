import pandas as pd
import pickle
import os.path

import os
from flask import Flask, Response, request,render_template
import json
app = Flask(__name__)
import math

@app.route('/', methods=["GET"])
def recommendRecipes():
    query = request.args.get('q')
    displayAll = request.args.get('all')
    print(query)

    if query == None:
        return Response(json.dumps(
            {'message': "A query is required to retrive documents!"}
            ), mimetype='application/json', status='400')

    plays = {}
    dateCheck = False

    if os.path.isfile('plays.p'):
        playData = pickle.load( open( "plays.p", "rb" ) )
        playsFlattened = playData[0]
        dateCheck= os.stat('Shakespeare_data.csv').st_mtime == playData[1]

    if not dateCheck:
        df = pd.read_csv('Shakespeare_data.csv', header=0)
        for index, row in df.iterrows():
            play = row['Play']
            actorLine = str(row['Player']) + ":" + row['PlayerLine']
            if(play in plays):
                plays[play]["actorLine"] += " " + actorLine
            else:
                plays[row['Play']] = {"play": play, "actorLine": actorLine }
        playsFlattened = [i for i in plays.values()]
        pickle.dump( (playsFlattened, os.stat('Shakespeare_data.csv').st_mtime), open( "plays.p", "wb" ) )

    operators = ["AND", "NOT", "OR"]

    terms = query.split(" ")
    newQuery = ""
    skip = False
    for i in range(len(terms)):
        if skip:
            skip =False
        elif terms[i] in operators:
            if terms[i] == "AND":
                newQuery+="&"
            elif terms[i] == "OR":
                newQuery+="|"
            elif terms[i] == "NOT":
                newQuery += "set({ "
                index = 0
                for j in playsFlattened:
                    if terms[i].lower() not in j["actorLine"].lower():
                        newQuery+=str(index) + ","
                        if 'rank' in j:
                            j['rank'] +=1
                        else:
                            j['rank'] = 1
                    index+=1
                newQuery = newQuery[:-1]
                newQuery += "})"
                skip = True
        else:
            newQuery += "set({ "
            index = 0
            for j in playsFlattened:
                if terms[i].lower() in j["actorLine"].lower():
                    newQuery+=str(index) + ","
                    if 'rank' in j:
                        j['rank'] +=1
                    else:
                        j['rank'] = 1
                index+=1
            newQuery = newQuery[:-1]
            newQuery += "})"
    resultsSet = eval(newQuery)
    present = []
    for val in resultsSet:
        if displayAll != "true":
            playsFlattened[val]['actorLine'] = playsFlattened[val]['actorLine'][:200] +"..."
        present.append(playsFlattened[val])
    
    present = sorted(present, key=lambda k: k['rank'], reverse=True)
    return Response(json.dumps({"query":query, "results": present}), mimetype='application/json', status='200')

if __name__ == '__main__':
    app.run(debug=True)
"""
------------------------------------------------------------------------------
This file connects users with their assignment information and store them in
the lists edges. Edges only contains tuples in the format of
(assignment name,userid,score,user name). Run this file to generate edges.json and edges2.json to see
more details.
------------------------------------------------------------------------------
"""



from difflib import SequenceMatcher
from CanvasData import grab_canvas_data
import os.path
from os import path
import json

#data structure initialization
data = {}
grades = {}
gradesList = []
modulesList = []
gradeScores = []
edges = []

def create_edges(repull):
    edges = []

    # read in JSON file
    data, data2 = grab_canvas_data()

    # add edges
    for d in data:
        for d2 in data2:
            if d['user_id'] == d2:
                score_calc = float(d["score"]) / float(d["total"]) * 100
                edges.append((d['assignment'], d2, score_calc, d["user_name"]))
                # Pass all the information needed, including assignment name, Ids, scores, userName

    f = open("edges.json", "w")
    f.write(json.dumps(edges))
    f.close()

    # print(edges)
    return edges

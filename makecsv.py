import http.client
import json
import csv

conn = http.client.HTTPSConnection("api.d3fend.mitre.org")
conn.request("GET", "https://api.d3fend.mitre.org/techniques/table")
#conn = http.client.HTTPConnection("localhost:8000")
#conn.request("GET", "http://localhost:8000/techniques/table")
r1 = conn.getresponse()
d3fend = json.loads(r1.read())


lines = []
depths = []
def recurse_node(node, depth=0, indent_char=",", log=False):
    depths.append(depth)
    if "children" in node:
        depth += 1
        for child in node['children']:
            if log:
                print(indent_char * depth + child['rdfs:label'])
            if "children" in child:
                lines.append(indent_char * depth + child['rdfs:label'])
                recurse_node(child, depth=depth, log=log)
            else:
                try:
                    lines.append(indent_char * depth + child['rdfs:label'] + "," + child['d3f:definition'])
                # in the case there is no definition ignore the technique but warn
                except KeyError:
                    #lines.append(indent_char * depth + child['rdfs:label'])
                    print( "WARNING: EXCLUDED Technique - NO DEFINITION FOR: " + child['rdfs:label'])



for node in d3fend:
#    recurse_node(node, log=True)
    recurse_node(node)

# Create CSV Header
tech_depth_header = "".join([f",D3FEND Technique Level {i+1}" for i in range(max(depths) -1 ) ])
lines.insert(0, ",D3FEND Tactic,D3FEND Technique," + tech_depth_header + ",Definition" )

with open("d3fend.csv", "w") as f:
    for line in lines:
        f.write(line + "\n")

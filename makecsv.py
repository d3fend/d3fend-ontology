import http.client
import json
import csv

conn = http.client.HTTPConnection("d3fend.mitre.org")
conn.request("GET", "http://api.d3fend.mitre.org/techniques/table")
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
                lines.append(indent_char * depth + child['rdfs:label'])


for node in d3fend:
#    recurse_node(node, log=True)
    recurse_node(node)

# Create CSV Header
tech_depth_header = "".join([f",D3FEND Technique Level {i+1}" for i in range(max(depths) -1 ) ])
lines.insert(0, ",D3FEND Tactic, D3FEND Technique" + tech_depth_header )

with open("d3fend.csv", "w") as f:
    for line in lines:
        f.write(line + "\n")

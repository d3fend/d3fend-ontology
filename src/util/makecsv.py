import csv
import http.client
import json

# conn = http.client.HTTPSConnection("api.d3fend.mitre.org")
# conn.request("GET", "https://api.d3fend.mitre.org/techniques/table")
conn = http.client.HTTPConnection("localhost:8000")
conn.request("GET", "http://localhost:8000/techniques/table")
r1 = conn.getresponse()
d3fend = json.loads(r1.read())


lines = []
depths = []


def recurse_node(node, depth=1, indent_char=",", log=False, tactic=""):
    depths.append(depth)
    if "children" in node:
        depth += 1
        for child in node["children"]:
            if log:
                print(indent_char * depth + child["rdfs:label"])
            if "children" in child:
                ID = child.get("d3f:d3fend-id", "")
                lines.append([ID, tactic, child["rdfs:label"], depth])
                recurse_node(child, depth=depth, log=log, tactic=tactic)
            else:
                try:
                    # lines.append(indent_char * depth + child['rdfs:label'] + "," + child['d3f:definition'])
                    ID = child.get("d3f:d3fend-id", "")
                    lines.append(
                        [
                            ID,
                            tactic,
                            child["rdfs:label"],
                            child["d3f:definition"],
                            depth,
                        ]
                    )
                    # return depth, child['rdfs:label'], child['d3f:definition']
                # in the case there is no definition ignore the technique but warn
                except KeyError:
                    # lines.append(indent_char * depth + child['rdfs:label'])
                    print(
                        "WARNING: EXCLUDED Technique - NO DEFINITION FOR: "
                        + child["rdfs:label"]
                    )
                except:
                    print("tactic:" + str(tactic))
                    print("child:" + child)
                    print("depth:" + str(depth))
                    raise


for node in d3fend:
    recurse_node(node, tactic=node["@id"].split(":")[1])

# Create CSV Header
# tech_depth_header = "".join([f",D3FEND Technique Level {i+1}" for i in range(max(depths) -1 ) ])
# lines.insert(0, ",D3FEND Tactic,D3FEND Technique," + tech_depth_header + ",Definition" )


with open("build/d3fend.csv", "w") as f:

    #             0                1                   2                           3                           4
    fieldnames = [
        "ID",
        "D3FEND Tactic",
        "D3FEND Technique",
        "D3FEND Technique Level 0",
        "D3FEND Technique Level 1",
        "Definition",
    ]

    d3fend_writer = csv.writer(f, delimiter=",")
    d3fend_writer.writerow(fieldnames)

    for line in lines:
        # print(line)
        rlength = len(fieldnames)
        template = [""] * rlength
        # handle categories
        if len(line) == 4:
            template[0] = line[0]  # ID
            template[1] = line[1]  # tactic
            template[line[-1]] = line[2]  # technique name
            d3fend_writer.writerow(template)
        else:
            try:
                depth = min(4, line[-1])
                template[0] = line[0]  # ID
                template[1] = line[1]  # tactic
                template[depth] = line[2]  # technique name
                template[5] = line[3]  # definition
                d3fend_writer.writerow(template)
            except:
                print(line)

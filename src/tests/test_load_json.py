from rdflib import Graph, plugin
import sys, json
from rdflib.plugin import register, Serializer

g = Graph()
try: 
    g.parse(sys.argv[1], format="json-ld")
    print('Rdflib Parsed d3fend.json successfully.')
except Exception as e:
    sys.exit('Rdflib failed to parse d3fend.json: '+ str(e))
g.close()

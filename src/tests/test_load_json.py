from rdflib import Graph, plugin
import sys, json, rdflib_jsonld
from rdflib.plugin import register, Serializer

register('json-ld', Serializer, 'rdflib_jsonld.serializer', 'JsonLDSerializer')

g = Graph()
try: 
    g.parse(sys.argv[1], format="json-ld")
    print('Rdflib Parsed d3fend.json successfully.')
except Exception as e:
    sys.exit('Rdflib failed to parse d3fend.json: '+ str(e))
g.close()

import json
from rdflib import Graph, Namespace, URIRef
import pyld

PUBLIC_ONTOLOGY_FILEPATH = "build/d3fend-public.owl"

class colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'


def log(message, error=False, info=False):
    if error:
        print(colors.FAIL + message)
    elif info:
        print(colors.OKBLUE + message)
    else:
        print(colors.OKGREEN + message)


def get_graph():
    g = Graph()
    filename = PUBLIC_ONTOLOGY_FILEPATH
    g.parse(filename)
    log(filename)
    log(f"The graph has {len(g)} triples", info=True)
    return g

    
if __name__ == "__main__":
    output_fname = "d3fend"

    g = get_graph()

    _base = "http://d3fend.mitre.org/ontologies/d3fend.owl"
    _xmlns = _base + "#"

    xmlns = Namespace(_xmlns)
    g.namespace_manager.bind('', xmlns, override=True, replace=True)
    ## Unbind may be indicated if desire serialization to manifest
    ## 'd3f:' prefix instead of ':' (i.e., empty prefix). See
    ## https://github.com/RDFLib/rdflib/issues/543.  Unbind operator
    ## not available in latest release (5.0.0) yet.
    # g.namespace_manager.unbind('') 
    d3f = Namespace(_xmlns)
    g.namespace_manager.bind('d3f', d3f, override=True, replace=True)

    for ns in g.namespaces():
        log('%s:%s' % (ns), info=True)
    
    # Serialize to different formats
    base_uri = URIRef(_base)
    g.serialize(destination=f"{output_fname}.owl", base=base_uri, format="xml")
    log(f"Wrote: {output_fname}.owl")
    g.serialize(destination=f"{output_fname}.ttl", format="ttl")
    log(f"Wrote: {output_fname}.ttl")

    
    g.serialize(destination=f"{output_fname}.json", format="json-ld")
    log(f"wrote: {output_fname}.json")

    log(f"The graph now has {len(g)} triples", info=True)

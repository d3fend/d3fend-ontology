from rdflib import Graph, Namespace, URIRef


PUBLIC_ONTOLOGY_FILEPATH = "build/d3fend-public.owl"
PUBLIC_DEST_DIR = "build/"

DEFAULT_CONTEXT = {
    "d3f": "http://d3fend.mitre.org/ontologies/d3fend.owl#",
    "dbr" : "http://dbpedia.org/resource/",
    "dc" : "http://purl.org/dc/elements/1.1/",
    "dcterms" : "http://purl.org/dc/terms/",
    "owl" : "http://www.w3.org/2002/07/owl#",
    "rdf" : "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "skos": "http://www.w3.org/2004/02/skos/core#",
    "xml" : "http://www.w3.org/XML/1998/namespace",
    "xsd" : "http://www.w3.org/2001/XMLSchema#"
}


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
    output_fname = "d3fend-public"

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

     # Serialize to different formats
    base_uri = URIRef(_base)


    g.serialize(destination=f"{PUBLIC_DEST_DIR}{output_fname}.ttl", format="ttl", auto_compact=True)
    log(f"Wrote: {output_fname}.ttl")

    #g.serialize(destination=f"{PUBLIC_DEST_DIR}{output_fname}.json", context={k:v for k, v in g.namespaces()}, format="json-ld")
    g.serialize(destination=f"{PUBLIC_DEST_DIR}{output_fname}.json", context=DEFAULT_CONTEXT, format="json-ld")

    log(f"wrote: {output_fname}.json")

    log(f"The graph now has {len(g)} triples", info=True)

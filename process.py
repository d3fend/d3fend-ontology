import json
from rdflib import Graph, Namespace, URIRef
import pyld


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
    g.parse("d3fend-webprotege.owl")
    log("Parsed d3fend-webprotege.owl")
    log(f"The graph has {len(g)} triples", info=True)
    return g


remove_triple_sparql_sparql = """PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX d3f: <http://d3fend.mitre.org/ontologies/d3fend.owl#>


DELETE WHERE {
    ?rs %s ?ro .
}"""


remove_d3fend_private_sparql = """
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX d3f: <http://d3fend.mitre.org/ontologies/d3fend.owl#>

DELETE WHERE {
    ?s ?p ?o .
    ?p rdfs:subPropertyOf d3f:d3fend-private-annotation .
}
"""

    
if __name__ == "__main__":
    output_fname = "d3fend"

    g = get_graph()

    _base = "http://d3fend.mitre.org/ontologies/d3fend.owl"
    _xmlns = _base + "#"

    base = URIRef("http://d3fend.mitre.org/ontologies/d3fend.owl")
    xmlns = Namespace(_xmlns)
    d3f = Namespace(_xmlns)

    g.namespace_manager.bind('', xmlns, override = True, replace=True)
    #g.namespace_manager.bind('base', base, override = True, replace=True)
    g.namespace_manager.bind('d3f', d3f, override = True, replace=True)


    # Filter development content
    g.update(remove_d3fend_private_sparql)
    log("Deleted all: ?p rdfs:subPropertyOf* d3f:d3fend-private-annotation")

    triples = [
        "d3f:todo",
        "d3f:comment",
        "d3f:d3fend-private-annotation"
    ]
    for triple in triples:
        g.update(remove_triple_sparql_sparql % triple)
        log(f"Removing {triple} predicates")

    # Serialize to different formats
    #g.serialize(destination="d3fend-test.xml", base=base, format="pretty-xml")
    g.serialize(destination=f"{output_fname}.xml", base=base)
    log(f"Wrote: {output_fname}.xml")
    g.serialize(destination=f"{output_fname}.ttl", base=base, format="ttl")
    log(f"Wrote: {output_fname}.ttl")
    g.serialize(destination=f"{output_fname}.json", format="json-ld")
    log(f"wrote: {output_fname}.json")


    # with open(f"{output_fname}-rdflib.json") as f:
        
    #     expanded_jsonld = json.load(f)
    #     context = { x[0]:x[1].__str__() for x in g.namespaces() if x[0]}
    #     with open(f"{output_fname}.json", "+w") as output_file:
    #         output_file.write(pyld.jsonld.compact(expanded_jsonld, context, 
    #             options=dict(
    #                 compactArrays=False,
    #                 base=base
    #                 )
    #             )
    #         )
    #         log(f"wrote: {output_fname}.json")

    log(f"The graph now has {len(g)} triples", info=True)

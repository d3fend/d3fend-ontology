import numpy as np
import pandas # requires openpyxl in environment to do read_excel
from owlready2 import *

"""
This Python script reads the public ontology file and writes out a
mapping file that is folded back into the ontology by a command shell script
that calls this script.
"""

go = get_ontology("d3fend-protege.owl").load() # Only needed for defensive technique lookups

relation_map = {
    "broader" : ":broader",
    "narrower" : ":narrower",
    "exactly" : ":exactly",
    "same" : ":exactly",        # off-label usage of same; treat as exactly
    np.nan : ":related",       # If undefined in spreadsheet, use most general match :related
    "" : ":related" }          # If undefined in spreadsheet, use most general match :related

d3fend_technique_query = """
prefix : <http://d3fend.mitre.org/ontologies/d3fend.owl#>

SELECT ?x 
WHERE {{ ?x :d3fend-id '{}' . }}
"""


# > get_d3fend_technique_name('D3-AL')
# d3fend.AccountLocking
def get_d3fend_technique_name(d3fend_id):
    query = d3fend_technique_query.format(d3fend_id)
    result = list(default_world.sparql(query)) # owlready2 sparql query to lookup technique name; could cache
    # print("{} -> {}\n".format(d3fend_id, result))
    if result[0] and result[0][0]:
        return result[0][0].name # .namespace, .iri
    else:
        return None


def get_cci_iri(cci_id):
    return cci_id # pass through for now


# Use when adding CCI mappings to NIST controls, but if doing that,
# remember to use XML data for those NIST reference mappings, tying to
# CCI XML data from DoD Cyber Exchange, as the spreadsheet isn't
# faithful table mapping of that XML:
#
# https://dl.dod.cyber.mil/wp-content/uploads/stigs/zip/U_CCI_List.zip)
def get_sp800_53_control_iri_name(version, control_id):
    """Formats IRI for a NIST SP800-53 control by removing spaces and brackets and embedding the release version"""
    control_iri_name = control_id.replace(" ", "")
    control_iri_name = control_iri_name.replace(")", "")
    control_iri_name = control_iri_name.replace("(", "_")
    control_iri_name = "NIST_SP800-53_R{}_{}".format(str(version), control_iri_name)
    return control_iri_name


def write_cci_mappings(f, publishdate, control_id, contributor, status, definition, relation, techniques_string):
    """Writes mappings for one row in frame (spreadsheet.) to .ttl"""
    if status != "deprecated":
        # Comes in as pandas.Timestamp, which is fine for d3f:published, which is xsd:dateTime
        # publishdate = publishdate.date() # If using as xsd:date
        publishdate = str(publishdate).replace(" ", "T") # default not quite ISO; not quite xsd:dateTime worthy
        # print('<{}>, <{}>, <{}>, <{}>, <{}>, <{}>, <{}>, <{}>\n'.format(type(publishdate), publishdate, control_id, contributor, status, definition, relation, techniques_string))
        control_iri_name = get_cci_iri(control_id)
        # Write individual representing NIST control and provide annotation and data properties
        f.write(':{} a :CCIControl ;\n'.format(control_iri_name))
        f.write('    rdfs:label "{}" ;\n'.format(control_id))
        f.write('    :published "{}"^^xsd:dateTime ;\n'.format(publishdate))
        f.write('    :contributor "{}" ;\n'.format(contributor))
        f.write('    :definition "{}" .\n'.format(definition))
        # Write relations of this control to D3FEND countermeasures mapped in mapping file.
        if isinstance(relation, str): relation = relation.lower() # make lower for robust matching, but not if nan
        if relation: # np.nan or non-empty string
            d3fend_relation = relation_map[relation]
            if d3fend_relation: # If we can understand relation, do mappings
                for technique in techniques_string.split("|"): # Get multiple defensive techniques
                    technique = technique.strip() # Trim it
                    if technique: # if non-empty
                        technique_iri_name = get_d3fend_technique_name(technique)
                        if technique_iri_name: # if we got a good lookup, do it.
                            f.write(':{} {} :{} .\n'.format(control_iri_name, d3fend_relation, technique_iri_name))
        f.write('\n')


df = pandas.read_excel(io='extensions/cci/CCI_Mapping.xlsx', sheet_name='U_CCI_List')

df = df[~df['D3FEND'].isnull()]
# dataframe as read treats str 'NA' and np.nan the same; but if that
# changes, pull NA string fields explicitly
df = df[df['D3FEND'].str.contains('NA')==False]
df = df[df['D3FEND'].str.contains('TBD')==False] 
df = df[df['D3FEND'].str.contains('Duplicate')==False]
df = df[df['D3FEND'].str.contains('Review')==False]

with open('cci-to-d3fend-mapping.ttl', 'w') as f:
#     f.write("""@prefix : <http://d3fend.mitre.org/ontologies/d3fend.owl#> .
# @prefix owl: <http://www.w3.org/2002/07/owl#> .
# @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
# @prefix xml: <http://www.w3.org/XML/1998/namespace> .
# @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
# @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
# @prefix skos: <http://www.w3.org/2004/02/skos/core#> .
# @prefix dcterms: <http://purl.org/dc/terms/> .
# @base <http://d3fend.mitre.org/ontologies/d3fend.owl> .
    
# """)
    df.apply(lambda x: write_cci_mappings(f,
                                          # no versioning on CCI data; pub date instead; versions are on NIST pubs
                                          x['publishdate'], # Just the date, no time
                                          x['_id'],         # this is the CCI-nnnnnn formated id
                                          x['contributor'], # DISA-FSO or DISA-FSP
                                          x['status'],      # deprecated or draft (dump deprecated)
                                          x['definition'],
                                          x['Relation'],
                                          x['D3FEND']),
                                          axis=1)

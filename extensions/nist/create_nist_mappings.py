import numpy as np
import pandas  # requires openpyxl to do read_excel
from owlready2 import default_world

""" This Python script reads the public ontology file and a mapping
file and writes out .ttl file with mappings that may be
appended to the public ontology. """

default_world.get_ontology(
    "build/d3fend-public.owl"
).load()  # Only needed for defensive technique lookups
d3fend_world = default_world

relation_map = {
    "broader": "d3f:broader",
    "narrower": "d3f:narrower",
    "exactly": "d3f:exactly",
    "same": "d3f:exactly",  # off-label usage of same; treat as exactly
    np.nan: "d3f:related",  # If undefined in spreadsheet, use most general match :related
    "": "d3f:related",
}  # If undefined in spreadsheet, use most general match :related

d3fend_technique_query = """
prefix : <http://d3fend.mitre.org/ontologies/d3fend.owl#>

SELECT ?x
WHERE {{ ?x :d3fend-id '{}' . }}
"""


# > get_d3fend_technique_name('D3-AL')
# d3fend.AccountLocking
def get_d3fend_technique_name(d3fend_id):
    query = d3fend_technique_query.format(d3fend_id)
    result = list(
        d3fend_world.sparql(query)
    )  # owlready2 sparql query to lookup technique name; could cache
    # print("{} -> {}\n".format(d3fend_id, result))
    if result[0] and result[0][0]:
        return result[0][0].name  # .namespace, .iri
    else:
        return None


def get_cci_iri(cci_id):
    return cci_id


def get_sp800_53_control_iri_name(version, control_id):
    """Formats IRI for a NIST SP 800-53 control by removing spaces and brackets and embedding the release version"""
    control_iri_name = control_id.replace(" ", "")
    control_iri_name = control_iri_name.replace(")", "")
    control_iri_name = control_iri_name.replace("(", "_")
    control_iri_name = "NIST_SP_800-53_R{}_{}".format(str(version), control_iri_name)
    return control_iri_name


def write_nist_control_mappings(
    f,
    version,
    control_id,
    control_name,
    relation,
    techniques_string,
    nist_catalog_iri="NIST_SP_800-53_R5",
):
    """Writes mappings for one row in frame (spreadsheet.) to .ttl"""
    version = str(version)
    # print('<{}>, <{}>, <{}>\n'.format(control_id, relation, techniques_string))
    control_iri_name = get_sp800_53_control_iri_name(version, control_id)
    # Write individual representing NIST control and provide annotation and data properties
    f.write("d3f:{} a d3f:NISTControl ;\n".format(control_iri_name))
    f.write("    d3f:member-of d3f:{} ;\n".format(nist_catalog_iri))
    f.write('    rdfs:label "{}" ;\n'.format(control_id))
    f.write('    d3f:control-name "{}" .\n'.format(control_name))
    f.write(
        "d3f:{} d3f:has-member d3f:{} .\n".format(nist_catalog_iri, control_iri_name)
    )
    # Write relations of this control to D3FEND countermeasures mapped in mapping file.
    if isinstance(relation, str):
        relation = relation.lower()  # make lower for robust matching, but not if nan
    if relation:  # np.nan or non-empty string
        d3fend_relation = relation_map[relation]
        if d3fend_relation:  # If we can understand relation, do mappings
            for technique in techniques_string.split(
                "|"
            ):  # Get multiple defensive techniques
                technique = technique.strip()  # Trim it
                if technique:  # if non-empty
                    technique_iri_name = get_d3fend_technique_name(technique)
                    if technique_iri_name:  # if we got a good lookup, do it.
                        f.write(
                            "d3f:{} {} d3f:{} .\n".format(
                                control_iri_name, d3fend_relation, technique_iri_name
                            )
                        )
    f.write("\n")


# Corrected D3-LIC to D3-DLIC
df = pandas.read_excel(
    io="extensions/nist/sp800-53r5-control-catalog-d3fend-mapping.xlsx",
    sheet_name="SP 800-53 Revision 5--d3fend",
)
techniques_column = "D3FEND Techniques"  # Corrected typo 'qes'->'ques' on column name original in spreadsheet

df = df[~df[techniques_column].isnull()]
# dataframe as read treats str 'NA' and np.nan the same; but if that
# changes, pull NA string fields explicitly
df = df[~df[techniques_column].str.contains("NA")]

with open("build/sp800-53r5-control-to-d3fend-mapping.ttl", "w") as f:
    df.apply(
        lambda x: write_nist_control_mappings(
            f,
            "5",
            x["Control Identifier"],
            x["Control (or Control Enhancement) Name"],
            x["Relation"],
            x[techniques_column],
        ),
        axis=1,
    )

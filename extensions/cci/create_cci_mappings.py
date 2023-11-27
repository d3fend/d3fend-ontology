import numpy as np
import pandas  # requires openpyxl in environment to do read_excel
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
    return cci_id  # pass through for now


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


def write_cci_mappings(
    f,
    publishdate,
    control_id,
    contributor,
    status,
    definition,
    relation,
    techniques_string,
    cci_catalog_prefix="CCICatalog",
    cci_catalog_version_date="2022-04-05",
):
    """Writes mappings for one row in frame (spreadsheet.) to .ttl"""
    if status != "deprecated":
        # Comes in as pandas.Timestamp, which is fine for d3f:published, which is xsd:dateTime
        # publishdate = publishdate.date() # If using as xsd:date
        publishdate = str(publishdate).replace(
            " ", "T"
        )  # default not quite ISO; not quite xsd:dateTime worthy
        if contributor == "DISA  FSO":
            contributor_iri_name = (
                "DISA_FSO"  # Fix the typos in original data with double spaces
            )
        else:
            contributor_iri_name = contributor.replace(" ", "_")
        # print('<{}>, <{}>, <{}>, <{}>, <{}>, <{}>, <{}>, <{}>\n'.
        #       format(type(publishdate), publishdate, control_id, contributor, status,
        #              definition, relation, techniques_string))
        control_iri_name = get_cci_iri(control_id) + "_v" + cci_catalog_version_date
        cci_catalog_iri = cci_catalog_prefix + "_v" + cci_catalog_version_date
        # Write individual representing NIST control and provide annotation and data properties
        f.write("d3f:{} a d3f:CCIControl ;\n".format(control_iri_name))
        f.write("    d3f:member-of d3f:{} ;\n".format(cci_catalog_iri))
        f.write('    rdfs:label "{}" ;\n'.format(control_id))
        f.write('    d3f:published "{}"^^xsd:dateTime ;\n'.format(publishdate))
        f.write("    d3f:contributor d3f:{} ;\n".format(contributor_iri_name))
        f.write('    d3f:definition "{}" .\n'.format(definition))
        f.write(
            "d3f:{} d3f:has-member d3f:{} .\n".format(cci_catalog_iri, control_iri_name)
        )
        # Write relations of this control to D3FEND countermeasures mapped in mapping file.
        if isinstance(relation, str):
            relation = (
                relation.lower()
            )  # make lower for robust matching, but not if nan
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
                                    control_iri_name,
                                    d3fend_relation,
                                    technique_iri_name,
                                )
                            )
        f.write("\n")


df = pandas.read_excel(io="extensions/cci/CCI_Mapping.xlsx", sheet_name="U_CCI_List")

df = df[~df["D3FEND"].isnull()]
# dataframe as read treats str 'NA' and np.nan the same; but if that
# changes, pull NA string fields explicitly
df = df[~df["D3FEND"].str.contains("NA")]
df = df[~df["D3FEND"].str.contains("TBD")]
df = df[~df["D3FEND"].str.contains("Duplicate")]
df = df[~df["D3FEND"].str.contains("Review")]

with open("build/cci-to-d3fend-mapping.ttl", "w") as f:
    df.apply(
        lambda x: write_cci_mappings(
            f,
            # no versioning on CCI data; pub date instead; versions are on NIST pubs
            x["publishdate"],  # Just the date, no time
            x["_id"],  # this is the CCI-nnnnnn formated id
            x["contributor"],  # DISA-FSO or DISA-FSP
            x["status"],  # deprecated or draft (dump deprecated)
            x["definition"],
            x["Relation"],
            x["D3FEND"],
        ),
        axis=1,
    )

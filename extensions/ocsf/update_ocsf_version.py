import os
import re
import json

# Constants for regular expressions
ONTOLOGY_VERSION_REGEX = r"(ocsf-schema/)[^/]+(/ontology)"
GENERATE_VERSION_REGEX = r"(schema\.ocsf\.io/)[^/]+(/[^ ]+)"

def replace_version(content, version):
    """
    Replace version numbers in ontology IRIs and GENERATE clauses.
    """
    # Replace version in ontology IRIs
    content = re.sub(ONTOLOGY_VERSION_REGEX, rf"\g<1>{version}\g<2>", content)
    # Replace version in GENERATE clauses
    content = re.sub(GENERATE_VERSION_REGEX, rf"\g<1>{version}\g<2>", content)
    return content


def update_reusable_rqg_files(files, version):
    """
    Updates version numbers in reusable .rqg files.
    """
    for file_path in files:
        file_path = os.path.expanduser(file_path)
        with open(file_path, "r") as f:
            content = f.read()

        # Replace version numbers
        updated_content = replace_version(content, version)

        with open(file_path, "w") as f:
            f.write(updated_content)

        print(f"Updated version in reusable file: {file_path}")

def update_sparql_generate_conf(conf_file, version):
    """
    Updates version numbers in sparql-generate-conf.json.
    """
    conf_file = os.path.expanduser(conf_file)
    with open(conf_file, "r") as f:
        conf_data = json.load(f)

    for query in conf_data["namedqueries"]:
        query["uri"] = replace_version(query["uri"], version)

    with open(conf_file, "w") as f:
        json.dump(conf_data, f, indent=4)

    print(f"Updated version in configuration file: {conf_file}")

def generate_plural_rqg(repo_dir, output_dir, version, construct_name, subdir):
    """
    Generates a plural-named .rqg file for a given construct (events, objects, restrictions).
    """
    repo_dir = os.path.expanduser(repo_dir)
    output_dir = os.path.expanduser(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    plural_path = os.path.join(output_dir, f"{construct_name}s.rqg")

    generate_section_plural = f"GENERATE <https://schema.ocsf.io/{version}/{construct_name}s> () {{\n"
    where_section_plural = "WHERE {\n"

    for root, _, files in os.walk(os.path.join(repo_dir, subdir)):
        for file in files:
            if file.endswith(".json"):
                variable_name = os.path.splitext(file)[0]
                relative_path = os.path.relpath(os.path.join(root, file), repo_dir)
                # iri = f"file://{os.path.join(repo_dir, relative_path).replace(os.sep, '/')}"

                # Add to plural GENERATE and WHERE sections
                generate_section_plural += f"  GENERATE <https://schema.ocsf.io/{version}/{construct_name}> ( ?{variable_name} ) .\n"
                where_section_plural += f"  BIND ( <{relaive_path}> AS ?{variable_name} )\n"

    generate_section_plural += "}\n\n"
    where_section_plural += "}\n"

    # Write plural file
    with open(plural_path, "w") as f:
        f.write(generate_section_plural + where_section_plural)
    print(f"Generated: {plural_path}")

# Quick check with grep:
# grep "1\.3\.0" * |  egrep -v '(objects|events|restrictions)'
def generate_all_dynamic_scripts(repo_dir, output_dir, version):
    """
    Generates all dynamic scripts for events, objects, erestrictions, and orestrictions.
    """
    generate_plural_rqg(repo_dir, output_dir, version, "event", "events")
    generate_plural_rqg(repo_dir, output_dir, version, "object", "objects")
    generate_plural_rqg(repo_dir, output_dir, version, "erestriction", "events")
    generate_plural_rqg(repo_dir, output_dir, version, "orestriction", "objects")

if __name__ == "__main__":
    repo_dir = "~/github/ocsf-schema"  # Replace with your relative path
    output_dir = "."  # Directory for generated .rqg files
    reusable_files = [
        "attribute.rqg",
        "base.rqg",
        "category.rqg",
        "categories.rqg",  
        "dictionary.rqg",  
        "event.rqg",
        "erestriction.rqg",
        "jsonschema.rqg",
        "object.rqg",
        "orestriction.rqg",
        "superclasses.rqg",
        "test.rqg",
        "type.rqg"
    ]
    conf_file = "./sparql-generate-conf.json"  # Configuration file
    version = "1.4.0"  # Schema version

    # Update reusable files
    update_reusable_rqg_files(reusable_files, version)

    # Generate dynamic scripts
    generate_all_dynamic_scripts(repo_dir, output_dir, version)

    # Update configuration file
    update_sparql_generate_conf(conf_file, version)

import csv

output_csv = []
level_0 = []

order = ["Model", "Harden", "Detect", "Isolate", "Deceive", "Evict", "Restore"]

with open("build/d3fend.csv") as csv_file:
    csv_reader = csv.DictReader(csv_file, delimiter=",")

    for row in csv_reader:
        new_entry = {
            "ID": row["def_tech_id"],
            "D3FEND Tactic": row["def_tactic_label"],
            "D3FEND Technique": "",
            "D3FEND Technique Level 0": "",
            "D3FEND Technique Level 1": "",
            "Definition": "",
        }

        # If parent is 'Defensive Technique', it is a baseline technique
        if row["parent_label"] == "Defensive Technique":
            new_entry["D3FEND Technique"] = row["def_tech_label"]
            level_0.append(row)
        # If parent is a baseline technique, this technique is Level 0
        elif any(x["def_tech_label"] == row["parent_label"] for x in level_0):
            new_entry["D3FEND Technique Level 0"] = row["def_tech_label"]
            new_entry["Definition"] = row["def_tech_definition"]
        # Otherwise, Level 1
        else:
            new_entry["D3FEND Technique Level 1"] = row["def_tech_label"]
            new_entry["Definition"] = row["def_tech_definition"]

        output_csv.append(new_entry)


with open("build/d3fend.csv", "w") as csv_file:
    writer = csv.writer(csv_file)
    writer.writerow(
        [
            "ID",
            "D3FEND Tactic",
            "D3FEND Technique",
            "D3FEND Technique Level 0",
            "D3FEND Technique Level 1",
            "Definition",
        ]
    )

    for tactic in order:
        for row in output_csv:
            if row["D3FEND Tactic"] == tactic:
                writer.writerow(row.values())

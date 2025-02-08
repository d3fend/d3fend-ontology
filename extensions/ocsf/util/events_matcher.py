def extract_info_from_file(file_path):
    result = []
    with open(file_path, 'r') as file:
        for line in file:
            # Split the line into path and extends part
            path_part, extends_part = line.split(':  "extends": ')
            # Clean up the parts
            path = path_part.strip()
            extends = extends_part.strip().strip('",')
            
            # Extract directory and JSON file name
            parts = path.split('/')
            directory = parts[2]
            json_file_name = parts[3].replace('.json', '')
            
            # Determine if there's a match
            match = (directory == extends) or (extends == "base_event")
            result.append((directory, json_file_name, extends, "" if match else "*"))
    return result

def print_table(data):
    print(f"{'Directory':<15} {'JSON File Name':<35} {'Extends':<20} {'Match':<5}")
    print("-" * 80)
    for row in data:
        print(f"{row[0]:<15} {row[1]:<35} {row[2]:<20} {row[3]:<5}")

# Path to the file containing the data
file_path = 'events_data.txt'
extracted_data = extract_info_from_file(file_path)
print_table(extracted_data)

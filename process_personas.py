import json

try:
    with open('personas.json', 'r') as file:
        personas = json.load(file)
except FileNotFoundError:
    print("The file personas.json was not found.")
    exit(1)
except json.JSONDecodeError:
    print("Error decoding JSON from the file.")
    exit(1)

# Iterate through the list and output the message
for person in personas:
    print(f"Hello to SAP, {person['name']}!")

import json

# Load the personas.json file
with open('personas.json', 'r') as file:
    personas = json.load(file)

# Iterate through the people and output the message
for person in personas['people']:
    print(f"Hello to SAP, {person['name']}!")

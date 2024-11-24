import json
import os

# File to store greeted people
greeted_file = 'greeted_people.txt'

# Load the personas.json file
try:
    with open('personas.json', 'r') as file:
        personas = json.load(file)
except FileNotFoundError:
    print("The file personas.json was not found.")
    exit(1)
except json.JSONDecodeError:
    print("Error decoding JSON from the file.")
    exit(1)

# Load greeted people from file
if os.path.exists(greeted_file):
    with open(greeted_file, 'r') as file:
        greeted_people = set(file.read().splitlines())
else:
    greeted_people = set()

# Iterate through the list and output the message
new_greeted_people = set()
for person in personas:
    name = person['name']
    if name in greeted_people:
        print(f"Person {name} is already welcomed.")
    else:
        print(f"Hello to SAP, {name}!")
        new_greeted_people.add(name)

# Update the greeted people file
with open(greeted_file, 'a') as file:
    for name in new_greeted_people:
        file.write(name + '\n')

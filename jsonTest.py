import json

data = {}
data['plates'] = []

data['plates'].append({
    'name': 'Adan',
    'plate': 'AFY010',
    'make': 'Nissan',
    'model': 'MARCH',
    'year': '2019'
})


with open('plates.json', 'w') as outfile:
    json.dump(data, outfile)
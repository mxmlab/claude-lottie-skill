import sys, json, os
name = sys.argv[1]
j = json.load(open(f'tgs/{name}.json', encoding='utf-8'))
files = []
for i, L in enumerate(j['layers']):
    k = dict(j); k['layers'] = [L]
    json.dump(k, open(f'iso/{name}_{i}.json', 'w')); files.append(f'iso/{name}_{i}.json')
    print(i, L['nm'])
print('URL files=' + ','.join(files))

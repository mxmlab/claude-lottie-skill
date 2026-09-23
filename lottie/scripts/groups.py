import sys, json
sys.path.insert(0,'.')
from lot import *
name, layer = sys.argv[1], sys.argv[2]
C = Comp.load(name); L = C.L(layer)
for i, g in enumerate(L['shapes']):
    if g['ty'] != 'gr': continue
    b = group_bbox(g)
    print(i, g['nm'], [round(v) for v in b] if b else None, group_colors(g)[:3])

"""Find jerky animated properties: per-frame velocity, flag frames where |acceleration| spikes.
Reports the worst offenders per sticker (layer name, prop, frame, velocity jump)."""
import json, sys, math
sys.path.insert(0, '.')
from lot7 import prop_at

T = 180

def shape_centroid(ks, t):
    keys = ks['k']
    if t <= keys[0]['t']: P = keys[0]['s'][0]
    elif t >= keys[-1]['t']: P = keys[-1]['s'][0]
    else:
        for k0, k1 in zip(keys, keys[1:]):
            if k0['t'] <= t < k1['t']:
                f = (t - k0['t']) / (k1['t'] - k0['t'])
                if k0.get('h'): f = 0
                elif 'o' in k0:
                    from lot7 import _bez
                    g = lambda q: q[0] if isinstance(q, list) else q
                    f = _bez(g(k0['o']['x']), g(k0['o']['y']), g(k0['i']['x']), g(k0['i']['y']), f)
                a, b = k0['s'][0]['v'], k1['s'][0]['v']
                P = {'v': [[x + (y - x) * f for x, y in zip(p, q)] for p, q in zip(a, b)]}
                break
    xs = [v[0] for v in P['v']]; ys = [v[1] for v in P['v']]
    return [sum(xs) / len(xs), sum(ys) / len(ys), max(xs) - min(xs), max(ys) - min(ys)]

def series(fn):
    return [fn(t) for t in range(0, T)]

def jerk_score(vals):
    """max velocity change between consecutive frames, relative to typical velocity"""
    best = (0, 0)
    for i in range(1, len(vals) - 1):
        v0 = [b - a for a, b in zip(vals[i - 1], vals[i])]
        v1 = [b - a for a, b in zip(vals[i], vals[i + 1])]
        dv = math.sqrt(sum((b - a) ** 2 for a, b in zip(v0, v1)))
        if dv > best[0]: best = (dv, i)
    return best

name = sys.argv[1]
j = json.load(open(f'out/{name}.json', encoding='utf-8'))
rows = []
def walk(o, where):
    if isinstance(o, dict):
        if o.get('ty') == 'sh' and o['ks'].get('a') == 1:
            s = series(lambda t: shape_centroid(o['ks'], t))
            rows.append((jerk_score(s), where + '/morph'))
        for key in ('p', 'r', 's'):
            v = o.get(key)
            if isinstance(v, dict) and v.get('a') == 1 and o.get('ty') in (None, 'tr') and isinstance(v.get('k'), list) and 't' in v['k'][0]:
                s = series(lambda t: [float(x) for x in prop_at(v, t, [0])][:2])
                rows.append((jerk_score(s), where + '/' + key))
        for k, v in o.items():
            walk(v, where + ('/' + o.get('nm', '') if k in ('shapes', 'it') else ''))
    elif isinstance(o, list):
        for v in o: walk(v, where)
for L in j['layers']:
    if L['nm'] in ('spark', 'rain', 'bill', 'tear', 'splash', 'pt', 'bub', 'bolt', 'puff', 'note', 'comet', 'heart', 'z', '!', 'sweat', 'ring', 'burst', 'shake', 'jolt', 'accent', 'flash', 'whoosh'):
        continue
    walk(L, L['nm'])
rows.sort(key=lambda r: -r[0][0])
for (dv, fr), w in rows[:8]:
    print(f'  {dv:6.2f} @f{fr:3}  {w[:70]}')

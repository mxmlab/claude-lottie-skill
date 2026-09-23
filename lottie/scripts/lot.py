"""Tiny Lottie authoring kit for the Backbony pack."""
import json, gzip, math, copy, os

T = 180
SCR = os.getcwd()          # work dir: tgs/ (unpacked json), out/ (built json)

# ------------------------------------------------------------------ primitives
def r2(x):
    if isinstance(x, (list, tuple)): return [r2(v) for v in x]
    if isinstance(x, dict): return {k: r2(v) for k, v in x.items()}
    return round(x, 2) if isinstance(x, float) else x

EASE = {
    'io':   ({'x': [0.42], 'y': [1]}, {'x': [0.58], 'y': [0]}),
    'out':  ({'x': [0.2], 'y': [1]}, {'x': [0.33], 'y': [0]}),
    'in':   ({'x': [0.67], 'y': [1]}, {'x': [0.7], 'y': [0]}),
    'lin':  ({'x': [0.5], 'y': [0.5]}, {'x': [0.5], 'y': [0.5]}),
    'snap': ({'x': [0.1], 'y': [1]}, {'x': [0.6], 'y': [0]}),
}

def anim(pairs, hold=False, ease='io'):
    """pairs: [(t, value)] or [(t, value, ease)]; value list or scalar."""
    pairs = sorted(pairs, key=lambda p: p[0])
    ks = []
    for n, p in enumerate(pairs):
        t, v = p[0], p[1]
        e = p[2] if len(p) > 2 else ease
        v = v if isinstance(v, list) else [v]
        k = {'t': t, 's': r2(v)}
        if n < len(pairs) - 1:
            if hold or e == 'hold': k['h'] = 1
            else:
                i, o = EASE[e]
                k['i'], k['o'] = i, o
        ks.append(k)
    return {'a': 1, 'k': ks}

def st(v): return {'a': 0, 'k': r2(v)}

def _prop(v):
    if isinstance(v, dict): return v
    return st(list(v) if isinstance(v, tuple) else v)

def tr(p=(0, 0), a=(0, 0), s=(100, 100), r=0, o=100):
    return {'ty': 'tr', 'p': _prop(p), 'a': _prop(a), 's': _prop(s), 'r': _prop(r), 'o': _prop(o),
            'sk': st(0), 'sa': st(0)}

def lks(p=(0, 0), a=(0, 0), s=(100, 100), r=0, o=100):
    return {'p': _prop(p), 'a': _prop(a), 's': _prop(s), 'r': _prop(r), 'o': _prop(o)}

def col(c): return c if isinstance(c, dict) else st(list(c)[:3] + [1])
def fill(c, o=100): return {'ty': 'fl', 'c': col(c), 'o': _prop(o), 'r': 1}
def stroke(c, w, o=100):
    return {'ty': 'st', 'c': col(c), 'o': _prop(o), 'w': _prop(w), 'lc': 2, 'lj': 2}
def ellipse(size, p=(0, 0)): return {'ty': 'el', 'p': _prop(p), 's': _prop(size), 'd': 1}
def rect(size, p=(0, 0), r=0): return {'ty': 'rc', 'p': _prop(p), 's': _prop(size), 'r': _prop(r), 'd': 1}
def trim(s=0, e=100, o=0): return {'ty': 'tm', 's': _prop(s), 'e': _prop(e), 'o': _prop(o), 'm': 1}
def group(items, t=None, nm='g'): return {'ty': 'gr', 'nm': nm, 'it': items + [t or tr()]}
def shape(pathv): return {'ty': 'sh', 'ks': pathv if isinstance(pathv, dict) and 'a' in pathv else st(pathv)}

def path(pts, closed=True, smooth=0.0):
    """pts list of (x,y). smooth>0 -> Catmull-Rom style tangents."""
    n = len(pts)
    if not smooth:
        z = [[0, 0]] * n
        return {'i': z, 'o': z, 'v': r2([list(p) for p in pts]), 'c': closed}
    ii, oo = [], []
    for k in range(n):
        if not closed and (k == 0 or k == n - 1):
            ii.append([0, 0]); oo.append([0, 0]); continue
        a, b = pts[(k - 1) % n], pts[(k + 1) % n]
        tx, ty = (b[0] - a[0]) * smooth / 2, (b[1] - a[1]) * smooth / 2
        ii.append([-tx, -ty]); oo.append([tx, ty])
    return {'i': r2(ii), 'o': r2(oo), 'v': r2([list(p) for p in pts]), 'c': closed}

class Comp:
    def __init__(self, data):
        self.j = data
        self.j['ip'], self.j['op'] = 0, T
        self.ind = 2000
        for L in self.j['layers']:
            L['op'] = T; L['ip'] = 0
    @classmethod
    def load(cls, name):
        return cls(json.load(open(os.path.join(SCR, 'tgs', name + '.json'), encoding='utf-8')))
    def L(self, prefix):
        return next(L for L in self.j['layers'] if L['nm'].startswith(prefix))
    def new_ind(self):
        self.ind += 1; return self.ind
    def null(self, nm, ks, parent=None):
        L = {'ddd': 0, 'ind': self.new_ind(), 'ty': 3, 'nm': nm, 'sr': 1, 'ks': ks, 'ao': 0,
             'ip': 0, 'op': T, 'st': 0, 'bm': 0}
        if parent is not None: L['parent'] = parent
        return L
    def layer(self, nm, shapes, ks, ip=0, op=T, parent=None):
        L = {'ddd': 0, 'ind': self.new_ind(), 'ty': 4, 'nm': nm, 'sr': 1, 'ks': ks, 'ao': 0,
             'shapes': shapes, 'ip': ip, 'op': op, 'st': 0, 'bm': 0}
        if parent is not None: L['parent'] = parent
        return L
    def insert(self, layers, above=None, below=None, top=False, bottom=False):
        """layers list; first = frontmost."""
        Ls = self.j['layers']
        if top: idx = 0
        elif bottom: idx = len(Ls)
        elif above is not None: idx = Ls.index(above)
        else: idx = Ls.index(below) + 1
        Ls[idx:idx] = layers
    def pivot(self, L, pt, **kw):
        """re-anchor a layer (whose p=a=256 identity) at pt, keeping look; kw -> animated props."""
        L['ks'] = lks(p=kw.get('p', pt), a=pt, s=kw.get('s', (100, 100)), r=kw.get('r', 0), o=kw.get('o', 100))
    def save(self, name, outdir):
        raw = json.dumps(self.j, ensure_ascii=False, separators=(',', ':'))
        os.makedirs(outdir, exist_ok=True)
        open(os.path.join(SCR, 'out', name + '.json'), 'w', encoding='utf-8').write(raw)
        gz = gzip.compress(raw.encode('utf-8'), 9)
        open(os.path.join(outdir, name + '.tgs'), 'wb').write(gz)
        report = check(self.j, len(gz))
        print(f'{name}: layers={len(self.j["layers"])} tgs={len(gz)}B', report)
        return len(gz)

def check(j, size):
    bad = set()
    def walk(o):
        if isinstance(o, dict):
            if isinstance(o.get('x'), str): bad.add('expression')
            if o.get('hasMask') or o.get('masksProperties'): bad.add('mask')
            if 'tt' in o: bad.add('matte')
            if o.get('ddd') == 1: bad.add('3d')
            if o.get('ty') == 2: bad.add('image')
            if 'ef' in o and o['ef']: bad.add('effects')
            for v in o.values(): walk(v)
        elif isinstance(o, list):
            for v in o: walk(v)
    walk(j)
    ok = j['w'] == 512 and j['h'] == 512 and j['fr'] == 60 and j['op'] - j['ip'] <= 180 and size <= 65536
    return ('OK' if ok and not bad else 'FAIL') + (f' {sorted(bad)}' if bad else '')

# ------------------------------------------------------------------ geometry helpers
def group_bbox(g, off=(0, 0)):
    xs, ys = [], []
    trs = [t for t in g['it'] if t['ty'] == 'tr']
    p = trs[0]['p']['k'][:2] if trs and trs[0]['p'].get('a') == 0 else [0, 0]
    a = trs[0]['a']['k'][:2] if trs and trs[0]['a'].get('a') == 0 else [0, 0]
    ox, oy = off[0] + p[0] - a[0], off[1] + p[1] - a[1]
    for it in g['it']:
        if it['ty'] == 'gr':
            b = group_bbox(it, (ox, oy))
            if b: xs += [b[0], b[2]]; ys += [b[1], b[3]]
        elif it['ty'] == 'sh':
            k = it['ks']['k']
            k = k[0]['s'][0] if isinstance(k, list) else k
            for v in k['v']: xs.append(v[0] + ox); ys.append(v[1] + oy)
    return (min(xs), min(ys), max(xs), max(ys)) if xs else None

def group_colors(g):
    out = []
    for it in g['it']:
        if it['ty'] in ('fl', 'st') and it['c'].get('a') == 0:
            out.append((it['ty'], tuple(round(c, 2) for c in it['c']['k'][:3])))
        elif it['ty'] == 'gr': out += group_colors(it)
    return out

def gtr(g): return next(t for t in g['it'] if t['ty'] == 'tr')

def rot(pt, c, deg, s=(1, 1)):
    a = math.radians(deg)
    x, y = (pt[0] - c[0]) * s[0], (pt[1] - c[1]) * s[1]
    return (c[0] + x * math.cos(a) - y * math.sin(a), c[1] + x * math.sin(a) + y * math.cos(a))

def looped(pairs):
    pairs = sorted(pairs, key=lambda p: p[0])
    if pairs[-1][0] != T: pairs = pairs + [(T,) + tuple(pairs[0][1:])]
    return pairs

def star_path(r, k=0.28, n=4):
    pts = []
    for i in range(2 * n):
        a = i * math.pi / n - math.pi / 2
        rr = r if i % 2 == 0 else r * k
        pts.append((rr * math.cos(a), rr * math.sin(a)))
    return path(pts)

# ------------------------------------------------------------------ reusable FX
def sparkle(C, t0, pos, r, color=(1, 1, 0.85), parent=None, dur=16, spin=90):
    return C.layer('spark', [group([shape(star_path(r)), fill(color)])],
                   lks(p=pos, s=anim([(t0, [0, 0]), (t0 + dur * 0.38, [120, 120], 'out'), (t0 + dur, [0, 0])]),
                       r=anim([(t0, 0), (t0 + dur, spin)])), ip=t0, op=t0 + dur + 1, parent=parent)

def loop_copies(fn, t0, life, *a, **kw):
    """call fn(t0,...) and also t0-T when it wraps the loop end."""
    out = [fn(t0, *a, **kw)]
    if t0 + life > T: out.append(fn(t0 - T, *a, **kw))
    return out

def gxf(g, c, s=None, r=None, dp=None, o=None):
    """animate a shape group around point c (parent coords). dp: [(t,[dx,dy])]."""
    t = gtr(g)
    P = t['p']['k'][:2]; A = t['a']['k'][:2]
    t['a'] = st([A[0] + c[0] - P[0], A[1] + c[1] - P[1]])
    t['p'] = anim([(k[0], [c[0] + k[1][0], c[1] + k[1][1]]) + tuple(k[2:]) for k in dp]) if dp else st(list(c))
    if s is not None: t['s'] = s
    if r is not None: t['r'] = r
    if o is not None: t['o'] = o

def drop_path(r):
    """teardrop pointing up, centered on the round part"""
    k = 0.55 * r
    return {'c': True, 'v': [[0, -2.2 * r], [r, 0], [0, r], [-r, 0]],
            'i': [[0, 0], [0, -k], [k, 0], [0, k]], 'o': [[0, 0], [0, k], [-k, 0], [0, -k]]}

def line_path(a, b): return path([a, b], closed=False)

# ------------------------------------------------------------------ path deformation (morphing artwork)
def _static(prop, default):
    if prop.get('a') == 1: return prop['k'][0]['s']
    return prop['k'] if isinstance(prop['k'], list) else [prop['k']]

def _grp_off(g, off):
    t = gtr(g)
    p = _static(t['p'], [0, 0])[:2]; a = _static(t['a'], [0, 0])[:2]
    return (off[0] + p[0] - a[0], off[1] + p[1] - a[1])

def iter_shapes(g, off=(0, 0)):
    """yield (sh_item, comp_offset) for every path in a group (orig static transforms)."""
    o = _grp_off(g, off)
    for it in g['it']:
        if it['ty'] == 'sh': yield it, o
        elif it['ty'] == 'gr': yield from iter_shapes(it, o)

def deform(P, fn, off, prec=1):
    vs, ii, oo = [], [], []
    for v, i, o in zip(P['v'], P['i'], P['o']):
        V = (v[0] + off[0], v[1] + off[1])
        nv = fn(V)
        ni = fn((V[0] + i[0], V[1] + i[1])); no = fn((V[0] + o[0], V[1] + o[1]))
        vs.append([round(nv[0] - off[0], prec), round(nv[1] - off[1], prec)])
        ii.append([round(ni[0] - nv[0], prec), round(ni[1] - nv[1], prec)])
        oo.append([round(no[0] - nv[0], prec), round(no[1] - nv[1], prec)])
    return {'i': ii, 'o': oo, 'v': vs, 'c': P['c']}

def morph_groups(groups, keys, make_fn):
    """keys: [(t, amount[, ease])]; make_fn(amount) -> point fn. Replaces each path with a morph."""
    for g in groups:
        for sh, off in iter_shapes(g):
            P = sh['ks']['k']
            if isinstance(P, list): P = P[0]['s'][0]
            sh['ks'] = anim([(k[0], [deform(P, make_fn(k[1]), off)]) + tuple(k[2:]) for k in keys])

def smoothstep(a, b, x):
    if b == a: return 1.0 if x >= b else 0.0
    u = min(1, max(0, (x - a) / (b - a)))
    return u * u * (3 - 2 * u)

def bend_fn(pivot, ang, R):
    """rotate points around pivot by ang * min(1, dist/R): a flexible bend/smear."""
    def f(p):
        dx, dy = p[0] - pivot[0], p[1] - pivot[1]
        d = math.hypot(dx, dy)
        a = math.radians(ang) * min(1.0, d / R)
        return (pivot[0] + dx * math.cos(a) - dy * math.sin(a), pivot[1] + dx * math.sin(a) + dy * math.cos(a))
    return f

def split_layer(C, L, parts):
    """parts: [(name, [shape indices])] in front-to-back order. Replaces L in the stack."""
    out = []
    for nm, idx in parts:
        N = copy.deepcopy(L)
        N['shapes'] = [L['shapes'][i] for i in idx]
        N['nm'] = nm; N['ind'] = C.new_ind()
        out.append(N)
    Ls = C.j['layers']; k = Ls.index(L)
    Ls[k:k + 1] = out
    return out

def mouth_rig(skull_shapes, teeth_idx, insert_at, Y0, x0, x1, Hk, jaw_groups, jaw_c, open_k,
              dark=(0.28, 0.1, 0.16), outl=(0.33, 0.39, 0.45), tongue_col=(0.96, 0.45, 0.52), jaw_gain=0.8, D=None):
    """generic open-mouth rig for the Backbony skulls (upper teeth block belongs to the skull).
    teeth_idx: skull+teeth-line groups to compress below Y0. Hk: [(t, depth)] ; open_k: [(t, k)]"""
    def compress(k):
        return lambda p: (p[0], p[1] if p[1] <= Y0 else Y0 + (p[1] - Y0) * (1 - k))
    if D is not None: D.add([skull_shapes[i] for i in teeth_idx], open_k, compress)
    else: morph_groups([skull_shapes[i] for i in teeth_idx], open_k, compress)
    xm = (x0 + x1) / 2; w = x1 - x0
    def interior(h):
        return path([(x0 - 2, Y0 - 4), (xm, Y0 - 8), (x1 + 2, Y0 - 4), (x1 - 4, Y0 + h * 0.65), (xm, Y0 + h), (x0 + 4, Y0 + h * 0.65)],
                    smooth=0.55)
    def band(h):
        a, b = x0 + w * 0.12, x1 - w * 0.12
        top = [(a, Y0 + h * 0.62 - 12), (xm, Y0 + h - 15), (b, Y0 + h * 0.62 - 12)]
        bot = [(b, Y0 + h * 0.62 + 2), (xm, Y0 + h + 1), (a, Y0 + h * 0.62 + 2)]
        return path(top + bot, smooth=0.5)
    def tongue(h):
        return path([(x0 + w * 0.22, Y0 + h * 0.8 - 2), (xm, Y0 + h * 0.55), (x1 - w * 0.22, Y0 + h * 0.8 - 2), (xm, Y0 + h * 1.02)], smooth=0.7)
    def tl(h, fx):
        x = x0 + w * fx
        return path([(x, Y0 + h * 0.8 - 11), (x + 1, Y0 + h * 0.8 + 3)], closed=False)
    groups = [
        group([shape(anim([(t, [tl(h, 0.36)]) for t, h in Hk])), stroke(outl, 3)], nm='tl1'),
        group([shape(anim([(t, [tl(h, 0.64)]) for t, h in Hk])), stroke(outl, 3)], nm='tl2'),
        group([shape(anim([(t, [band(h)]) for t, h in Hk])), fill((1, 1, 1)), stroke(outl, 3.5)], nm='lower teeth'),
        group([shape(anim([(t, [tongue(h)]) for t, h in Hk])), fill(tongue_col)], nm='tongue'),
        group([shape(anim([(t, [interior(h)]) for t, h in Hk])), fill(dark), stroke(outl, 4)], nm='mouth'),
    ]
    skull_shapes_list = skull_shapes
    for g in jaw_groups:
        gxf(g, jaw_c, dp=[(t, [0, (h - 3) * jaw_gain]) for t, h in Hk])
    return groups

def puff(C, t0, pos, vel, r=22, life=26, parent=None, col=(1, 1, 1), edge=(0.78, 0.84, 0.88)):
    items = []
    for dx, dy, rr in ((-r * 0.55, r * 0.15, r * 0.75), (r * 0.55, r * 0.2, r * 0.7), (0, -r * 0.3, r)):
        items.append(group([ellipse((rr * 2, rr * 2), (dx, dy)), fill(col), stroke(edge, 3)]))
    return C.layer('puff', items,
                   lks(p=anim([(t0, list(pos)), (t0 + life, [pos[0] + vel[0], pos[1] + vel[1]])], ease='out'),
                       s=anim([(t0, [20, 20]), (t0 + 7, [115, 115], 'out'), (t0 + life, [70, 70])]),
                       o=anim([(t0, 100), (t0 + life - 8, 100), (t0 + life, 0)])),
                   ip=t0, op=t0 + life, parent=parent)

def wrap_copies(C, layers):
    """for layers running past the loop end, add a copy shifted by -T so the tail shows at the start."""
    out = []
    def shift(o):
        if isinstance(o, dict):
            if 't' in o and isinstance(o['t'], (int, float)): o['t'] -= T
            for v in o.values(): shift(v)
        elif isinstance(o, list):
            for v in o: shift(v)
    for L in layers:
        if L['op'] > T:
            c = copy.deepcopy(L); c['ind'] = C.new_ind()
            shift(c['ks']); shift(c.get('shapes', [])); c['ip'] -= T; c['op'] -= T
            out.append(c)
    return out

# ------------------------------------------------------------------ smooth motion engine
def _target_at(keys, t):
    t = t % T
    v = keys[-1][1]
    for k in keys:
        if k[0] <= t: v = k[1]
    return v

def spring(keys, f=2.5, z=0.5, idle=None, step=2, loops=3):
    """keys: [(t, value)] piecewise-constant targets (value scalar or list).
    A damped spring (freq f Hz, damping ratio z) chases the targets; periodic idle(t)->value added.
    Returns samples [(t, value)] for t in 0..T step, periodic."""
    keys = sorted(keys, key=lambda k: k[0])
    vec = isinstance(keys[0][1], (list, tuple))
    n = len(keys[0][1]) if vec else 1
    x = list(keys[0][1]) if vec else [keys[0][1]]
    v = [0.0] * n
    w = 2 * math.pi * f
    sub = 4; dt = 1 / 60 / sub
    rec = {}
    for L in range(loops):
        for fr in range(T):
            tg = _target_at(keys, fr)
            tg = list(tg) if vec else [tg]
            if L == loops - 1: rec[fr] = list(x)
            for _ in range(sub):
                for i in range(n):
                    a = w * w * (tg[i] - x[i]) - 2 * z * w * v[i]
                    v[i] += a * dt; x[i] += v[i] * dt
    rec[T] = rec[0]
    out = []
    for fr in list(range(0, T, step)) + [T]:
        val = list(rec[fr])
        if idle:
            iv = idle(fr); iv = list(iv) if isinstance(iv, (list, tuple)) else [iv]
            val = [a + b for a, b in zip(val, iv)]
        out.append((fr, val if vec else val[0]))
    return out

def sampled(fn, step=2, t0=0, t1=T):
    return [(t, fn(t)) for t in list(range(t0, t1, step)) + [t1]]

def lin(samples):
    """anim with linear segments between dense samples (smooth when samples are smooth)."""
    return anim([(t, v if isinstance(v, list) else v, 'lin') for t, v in samples])

def add(a, b):
    """add two sample lists with identical times"""
    out = []
    for (t, x), (_, y) in zip(a, b):
        if isinstance(x, list): out.append((t, [p + q for p, q in zip(x, y)]))
        else: out.append((t, x + y))
    return out

def wave(amp, cycles, ph=0.0):
    """periodic sine that loops seamlessly over T"""
    return lambda t: amp * math.sin(2 * math.pi * cycles * t / T + ph)

def gfill(stops, c, r, o=100, anim_stops=None):
    """radial gradient fill. stops: [(pos, (r,g,b), alpha)]"""
    cols = []; alph = []
    for p, c3, a in stops:
        cols += [p] + list(c3); alph += [p, a]
    g = {'p': len(stops), 'k': anim_stops if anim_stops else st(cols + alph)}
    return {'ty': 'gf', 'o': _prop(o), 'r': 1, 's': _prop(c), 'e': _prop((c[0] + r, c[1])), 't': 2, 'g': g,
            'h': st(0), 'a': st(0)}

def glow(C, c, r, color, o, parent=None, ip=0, op=None, core=0.55):
    """soft radial glow layer; o may be an anim"""
    return C.layer('glow', [group([ellipse((2 * r, 2 * r)), gfill([(0, color, 1), (core, color, 0.45), (1, color, 0)], (0, 0), r)])],
                   lks(p=c, o=o), ip=ip, op=op if op is not None else T, parent=parent)


# ------------------------------------------------------------------ deformation composer
def _interp(keys, t):
    """keys [(t, v)] (v scalar or list) -> eased value at t"""
    if t <= keys[0][0]: return keys[0][1]
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t0 <= t <= t1:
            u = 0 if t1 == t0 else (t - t0) / (t1 - t0)
            u = u * u * (3 - 2 * u)
            if isinstance(v0, (list, tuple)): return [a + (b - a) * u for a, b in zip(v0, v1)]
            return v0 + (v1 - v0) * u
    return keys[-1][1]

class Deformer:
    """collect several deformation channels per shape group; build() writes one combined morph."""
    def __init__(self): self.g = {}
    def add(self, groups, keys, factory, exact=False):
        """keys [(t, param)], factory(param) -> point fn. exact=True: its key times are sampled points (dense)."""
        keys = sorted([(k[0], k[1]) for k in keys], key=lambda k: k[0])
        for g in groups:
            self.g.setdefault(id(g), [g, []])[1].append((keys, factory, exact))
    def build(self, ease='io', prec=1):
        for g, chans in self.g.values():
            times = sorted(set(t for keys, _, _ in chans for t, _ in keys))
            dense = any(ex for _, _, ex in chans)
            for sh, off in iter_shapes(g):
                P = sh['ks']['k']
                if isinstance(P, list): P = P[0]['s'][0]
                ks = []
                for t in times:
                    fns = [fac(_interp(keys, t)) for keys, fac, _ in chans]
                    def comp(p, fns=fns):
                        for f in fns: p = f(p)
                        return p
                    ks.append((t, [deform(P, comp, off, prec)], 'lin' if dense else ease))
                sh['ks'] = anim(ks)

def turn_fn(c, R, mode='surface', depth=1.0, zfloor=0.25):
    """factory for a fake-3D head turn. param = (yaw_deg, pitch_deg).
    surface: point lifted onto a sphere (z from radius), rotated, projected -> real parallax
    silhouette: outline only nudges toward the turn; back: parts behind the head move opposite."""
    def mk(par):
        yaw, pitch = math.radians(par[0]), math.radians(par[1])
        def f(p):
            x, y = p[0] - c[0], p[1] - c[1]
            if mode == 'surface':
                z = math.sqrt(max(R * R - x * x - y * y, (zfloor * R) ** 2)) * depth
                x1 = x * math.cos(yaw) + z * math.sin(yaw)
                z1 = -x * math.sin(yaw) + z * math.cos(yaw)
                y1 = y * math.cos(pitch) - z1 * math.sin(pitch)
                return (c[0] + x1, c[1] + y1)
            if mode == 'silhouette':
                k = 1 - 0.05 * abs(math.sin(yaw))
                return (c[0] + x * k + 0.12 * R * depth * math.sin(yaw), c[1] + y * (1 - 0.04 * abs(math.sin(pitch))) - 0.1 * R * depth * math.sin(pitch))
            if mode == 'back':
                return (c[0] + x - 0.2 * R * depth * math.sin(yaw), c[1] + y + 0.15 * R * depth * math.sin(pitch))
            return p
        return f
    return mk

# ------------------------------------------------------------------ volume shading pass
def _mixc(a, b, k): return [a[i] + (b[i] - a[i]) * k for i in range(3)]

def shade_group(g, light=(-0.55, -0.8), hi=0.38, sh=0.42, shade_col=(0.12, 0.16, 0.42), spread=0.95):
    """insert a radial gradient above the group's solid fill, clipped by the group's own path."""
    fl = next((it for it in g['it'] if it['ty'] == 'fl' and it['c'].get('a') == 0), None)
    shp = next((it for it in g['it'] if it['ty'] == 'sh'), None)
    if not fl or not shp: return False
    base = fl['c']['k'][:3]
    if max(base) < 0.12: return False                       # black: leave
    P = shp['ks']['k']
    if isinstance(P, list): P = P[0]['s'][0]
    xs = [v[0] for v in P['v']]; ys = [v[1] for v in P['v']]
    w, h = max(xs) - min(xs), max(ys) - min(ys)
    if w * h < 250: return False
    cx, cy = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
    size = max(w, h)
    c = (cx + light[0] * 0.32 * w, cy + light[1] * 0.32 * h)
    hic = _mixc(base, (1, 1, 1), 0.65); shc = _mixc(base, shade_col, 0.5)
    gf = gfill([(0, hic, hi), (0.42, base, 0), (1, shc, sh)], c, size * spread)
    gf['nm'] = 'shade'
    g['it'].insert(g['it'].index(fl), gf)
    return True

def shade_layer(L, **kw):
    n = 0
    def rec(items):
        nonlocal n
        for it in items:
            if it['ty'] == 'gr':
                if shade_group(it, **kw): n += 1
                rec(it['it'])
    rec(L.get('shapes', []))
    return n

def comet(C, t0, c, radius, a0, a1, width, color, dur=12, lag=0.4, parent=None, core=(1, 1, 1)):
    """tapered motion streak along an arc (filled, not a stroke): head leads, tail follows and thins."""
    def band(u, wk):
        head = a0 + (a1 - a0) * min(1, u)
        tail = a0 + (a1 - a0) * max(0, min(1, u - lag))
        n = 9; outer = []; inner = []
        for i in range(n + 1):
            k = i / n
            a = math.radians(tail + (head - tail) * k)
            w = width * wk * math.sin(math.pi * 0.5 * k) ** 1.2          # 0 at tail -> full at head
            outer.append((radius * math.cos(a) + math.cos(a) * w / 2, radius * math.sin(a) + math.sin(a) * w / 2))
            inner.append((radius * math.cos(a) - math.cos(a) * w / 2, radius * math.sin(a) - math.sin(a) * w / 2))
        return path(outer + inner[::-1], smooth=0.3)
    keys, keys2 = [], []
    for f in range(0, dur + 1, 2):
        u = f / dur * (1 + lag)
        e = u * u * (3 - 2 * u) if u < 1 else 1 + (u - 1)
        fade = 1 if u < 1 else max(0.01, 1 - (u - 1) / lag)
        keys.append((t0 + f, [band(e, fade)], 'lin')); keys2.append((t0 + f, [band(e, fade * 0.4)], 'lin'))
    return C.layer('comet', [group([shape(anim(keys2)), fill(core, 90)]), group([shape(anim(keys)), fill(color, 85)])],
                   lks(p=c), ip=t0, op=t0 + dur + 1, parent=parent)

# ------------------------------------------------------------------ cel shading (hard terminator, shared light, moves with the head turn)
ART_SHADOW = (0.71, 0.82, 0.85)
def cel_group(g, turn=None, light=(-0.6, -0.75), k=0.8, alpha=1.0):
    fl = next((it for it in g['it'] if it['ty'] == 'fl' and it['c'].get('a') == 0), None)
    shp = next((it for it in g['it'] if it['ty'] == 'sh'), None)
    if not fl or not shp: return False
    base = fl['c']['k'][:3]
    if max(base) < 0.12: return False
    if all(abs(a - b) < 0.03 for a, b in zip(base, ART_SHADOW)): return False     # already a drawn shadow
    P = shp['ks']['k']
    if isinstance(P, list): P = P[0]['s'][0]
    xs = [v[0] for v in P['v']]; ys = [v[1] for v in P['v']]
    w, h = max(xs) - min(xs), max(ys) - min(ys)
    if w * h < 1500 or min(w, h) < 18: return False
    cx, cy = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
    if min(base) > 0.9: sc = list(ART_SHADOW)                                  # white bone -> the artwork's own blue shadow
    else: sc = [c * 0.72 + d * 0.12 for c, d in zip(base, (0.25, 0.15, 0.55))]
    R = math.hypot(w, h) * 0.5 * 1.05
    def centre(yaw=0.0, pitch=0.0):
        return [cx + light[0] * 0.42 * w - math.sin(math.radians(yaw)) * 0.5 * w,
                cy + light[1] * 0.42 * h - math.sin(math.radians(pitch)) * 0.5 * h]
    stops = [0] + sc + [k] + sc + [k + 0.015] + sc + [1] + sc + [0, 0, k, 0, k + 0.015, alpha, 1, alpha]
    gf = {'ty': 'gf', 'nm': 'cel', 'o': st(100), 'r': 1, 't': 2, 'h': st(0), 'a': st(0), 'g': {'p': 4, 'k': st(stops)}}
    if turn:
        gf['s'] = anim([(t, centre(*v), 'lin') for t, v in turn])
        gf['e'] = anim([(t, [centre(*v)[0] + R * 1.25, centre(*v)[1]], 'lin') for t, v in turn])
    else:
        c0 = centre(); gf['s'] = st(c0); gf['e'] = st([c0[0] + R * 1.25, c0[1]])
    g['it'].insert(g['it'].index(fl), gf)
    return True

def cel_layer(L, turn=None, **kw):
    n = 0
    def rec(items):
        nonlocal n
        for it in items:
            if it['ty'] == 'gr':
                if cel_group(it, turn, **kw): n += 1
                rec(it['it'])
    rec(L.get('shapes', []))
    return n

def shade_all(C, layers, YP=None, head_ind=None):
    """cel-shade layers; parts riding the head get a terminator that follows the head turn"""
    YPd = None
    if YP:
        YPd = [(t, list(v)) for t, v in YP]
        dense = []
        for t in list(range(0, T, 6)) + [T]: dense.append((t, _interp(YPd, t)))
        YPd = dense
    for L in layers:
        cel_layer(L, YPd if (YPd and L.get('parent') == head_ind) else None)

# ------------------------------------------------------------------ cel shading v2: highlight + terminator + bounce, cast AO
def _gstops(entries):
    """entries: [(pos, rgb, alpha)] -> lottie gradient k (same positions for colour & opacity)"""
    col = []; op = []
    for p, c, a in entries: col += [p] + list(c); op += [p, a]
    return col + op

def _verts_abs(g):
    pts = []
    for sh, off in iter_shapes(g):
        P = sh['ks']['k']
        if isinstance(P, list): P = P[0]['s'][0]
        pts += [(v[0] + off[0], v[1] + off[1]) for v in P['v']]
    return pts

def cel2_group(g, turn=None, light=(-0.6, -0.75), k=0.7, hk=0.13, bounce=0.93, gloss=True):
    fl = next((it for it in g['it'] if it['ty'] == 'fl' and it['c'].get('a') == 0), None)
    shp = next((it for it in g['it'] if it['ty'] == 'sh'), None)
    if not fl or not shp: return False
    base = fl['c']['k'][:3]
    if max(base) < 0.12: return False
    if all(abs(a - b) < 0.03 for a, b in zip(base, ART_SHADOW)): return False
    P = shp['ks']['k']
    if isinstance(P, list): P = P[0]['s'][0]
    vs = P['v']; xs = [v[0] for v in vs]; ys = [v[1] for v in vs]
    w, h = max(xs) - min(xs), max(ys) - min(ys)
    if w * h < 1500 or min(w, h) < 18: return False
    cx, cy = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
    white = min(base) > 0.9
    sh = list(ART_SHADOW) if white else [c * 0.7 + d * 0.13 for c, d in zip(base, (0.3, 0.12, 0.55))]
    bc = [a + (b - a) * 0.55 for a, b in zip(sh, base)]
    hi = [a + (1 - a) * 0.6 for a in base]
    hiA = 0 if (white or not gloss or w * h < 3500) else 0.7
    def centre(yaw=0.0, pitch=0.0):
        return (cx + light[0] * 0.38 * w - math.sin(math.radians(yaw)) * 0.5 * w,
                cy + light[1] * 0.38 * h - math.sin(math.radians(pitch)) * 0.5 * h)
    def dmax(c): return max(math.hypot(v[0] - c[0], v[1] - c[1]) for v in vs) * 1.01
    e = 0.012
    stops = _gstops([(0, hi, hiA), (hk, hi, hiA), (hk + e, sh, 0), (k, sh, 0), (k + e, sh, 1),
                     (bounce, sh, 1), (bounce + e, bc, 1), (1, bc, 1)])
    gf = {'ty': 'gf', 'nm': 'cel2', 'o': st(100), 'r': 1, 't': 2, 'h': st(0), 'a': st(0), 'g': {'p': 8, 'k': st(stops)}}
    if turn:
        cs = [(t, centre(*v)) for t, v in turn]
        gf['s'] = anim([(t, list(c), 'lin') for t, c in cs])
        gf['e'] = anim([(t, [c[0] + dmax(c), c[1]], 'lin') for t, c in cs])
    else:
        c0 = centre(); gf['s'] = st(list(c0)); gf['e'] = st([c0[0] + dmax(c0), c0[1]])
    g['it'].insert(g['it'].index(fl), gf)
    return True

def ao_group(g, c, r, alpha=0.5, soft=0.35):
    """cast-shadow blob clipped by this group's own path"""
    fl = next((it for it in g['it'] if it['ty'] == 'fl' and it['c'].get('a') == 0), None)
    if not fl or not any(it['ty'] == 'sh' for it in g['it']): return False
    base = fl['c']['k'][:3]
    if max(base) < 0.12: return False
    sh = list(ART_SHADOW) if min(base) > 0.9 else [c_ * 0.62 + d * 0.12 for c_, d in zip(base, (0.3, 0.12, 0.55))]
    stops = _gstops([(0, sh, alpha), (1 - soft, sh, alpha), (1, sh, 0)])
    gf = {'ty': 'gf', 'nm': 'ao', 'o': st(100), 'r': 1, 't': 2, 'h': st(0), 'a': st(0), 'g': {'p': 3, 'k': st(stops)},
          's': st(list(c)), 'e': st([c[0] + r, c[1]])}
    g['it'].insert(g['it'].index(fl), gf)
    return True

def _layer_groups(L):
    out = []
    def rec(items):
        for it in items:
            if it['ty'] == 'gr': out.append(it); rec(it['it'])
    rec(L.get('shapes', []))
    return out

def _bbox(pts):
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)

def shade_all(C, layers, YP=None, head_ind=None, step=12):
    YPd = None
    if YP:
        YPd = [(t, list(v)) for t, v in YP]
        YPd = [(t, _interp(YPd, t)) for t in list(range(0, T, step)) + [T]]
    order = {id(L): i for i, L in enumerate(C.j['layers'])}
    layers = [L for L in layers if id(L) in order]
    # --- cast shadows: compact casters above -> big receivers below (clipped to receiver shapes)
    info = {}
    for L in layers:
        pts = [p for g in L.get('shapes', []) if g['ty'] == 'gr' for p in _verts_abs(g)]
        if pts: info[id(L)] = _bbox(pts)
    for R in layers:
        if id(R) not in info: continue
        for Cst in layers:
            if Cst is R or id(Cst) not in info or order[id(Cst)] >= order[id(R)]: continue
            x0, y0, x1, y1 = info[id(Cst)]; w, h = x1 - x0, y1 - y0
            if w * h < 2500 or max(w, h) / max(1, min(w, h)) > 2.2: continue
            c = ((x0 + x1) / 2 + 0.1 * w, (y0 + y1) / 2 + 0.16 * h)
            r = min(w, h) * 0.55
            for g in _layer_groups(R):
                pts = _verts_abs(g)
                if not pts: continue
                gx0, gy0, gx1, gy1 = _bbox(pts)
                if (gx1 - gx0) * (gy1 - gy0) < 2500: continue
                if gx1 < c[0] - r or gx0 > c[0] + r or gy1 < c[1] - r or gy0 > c[1] + r: continue
                ao_group(g, c, r)
    # --- form shading
    for L in layers:
        tn = YPd if (YPd and L.get('parent') == head_ind) else None
        cloth = any(k_ in L['nm'].lower() for k_ in ('тело', 'рубах', 'футб', 'штан', 'body', 'shirt', 'pants', 'ручка', 'sleeve'))
        for g in _layer_groups(L):
            cel2_group(g, tn, gloss=not cloth)

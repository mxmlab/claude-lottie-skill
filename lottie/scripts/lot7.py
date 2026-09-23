"""v7 additions: smooth (monotone cubic) deformation interpolation, world-space cel light."""
import math
from lot import *
import lot


def _mono_interp(keys, t):
    """monotone cubic (Fritsch-Carlson) through pose keys; scalar or list values; no overshoot, C1."""
    ts = [k[0] for k in keys]
    if t <= ts[0]: return keys[0][1]
    if t >= ts[-1]: return keys[-1][1]
    vec = isinstance(keys[0][1], (list, tuple))
    vals = [list(k[1]) if vec else [k[1]] for k in keys]
    n = len(keys); dim = len(vals[0])
    i = max(j for j in range(n - 1) if ts[j] <= t)
    h = ts[i + 1] - ts[i]
    if h == 0: return keys[i + 1][1]
    u = (t - ts[i]) / h
    out = []
    for d in range(dim):
        y = [v[d] for v in vals]

        def slope(j):
            if j == 0 or j == n - 1: return 0.0
            if ts[j] == ts[j - 1] or ts[j + 1] == ts[j]: return 0.0
            d0 = (y[j] - y[j - 1]) / (ts[j] - ts[j - 1]); d1 = (y[j + 1] - y[j]) / (ts[j + 1] - ts[j])
            if d0 * d1 <= 0: return 0.0
            return 2 / (1 / d0 + 1 / d1)
        m0, m1 = slope(i) * h, slope(i + 1) * h
        u2, u3 = u * u, u * u * u
        out.append((2 * u3 - 3 * u2 + 1) * y[i] + (u3 - 2 * u2 + u) * m0 + (-2 * u3 + 3 * u2) * y[i + 1] + (u3 - u2) * m1)
    return out if vec else out[0]


def _deformer_build(self, step=12, prec=1):
    for g, chans in self.g.values():
        times = set(list(range(0, T, step)) + [T])
        for keys, _, exact in chans:
            if not exact: times |= set(t for t, _ in keys if 0 <= t <= T)
        times = sorted(times)
        for sh, off in iter_shapes(g):
            P = sh['ks']['k']
            if isinstance(P, list): P = P[0]['s'][0]
            ks = []
            for t in times:
                fns = [fac(lot._interp(keys, t) if exact else _mono_interp(keys, t)) for keys, fac, exact in chans]

                def comp(p, fns=fns):
                    for f in fns: p = f(p)
                    return p
                dp = deform(P, comp, off, prec)
                dp['i'] = [[round(a), round(b)] for a, b in dp['i']]; dp['o'] = [[round(a), round(b)] for a, b in dp['o']]
                ks.append((t, [dp], 'lin'))
            sh['ks'] = anim(ks)


Deformer.build = _deformer_build


# ---------------- transform evaluation
def _bez(ox, oy, ix, iy, x):
    lo, hi = 0.0, 1.0
    for _ in range(30):
        u = (lo + hi) / 2
        bx = 3 * (1 - u) ** 2 * u * ox + 3 * (1 - u) * u * u * ix + u ** 3
        if bx < x: lo = u
        else: hi = u
    u = (lo + hi) / 2
    return 3 * (1 - u) ** 2 * u * oy + 3 * (1 - u) * u * u * iy + u ** 3


def prop_at(prop, t, default):
    if prop is None: return default
    if prop.get('a') != 1:
        v = prop['k']; return v if isinstance(v, list) else [v]
    ks = prop['k']
    if t <= ks[0]['t']: return ks[0]['s']
    for k0, k1 in zip(ks, ks[1:]):
        if k0['t'] <= t < k1['t']:
            if k0.get('h'): return k0['s']
            f = (t - k0['t']) / (k1['t'] - k0['t'])
            if 'o' in k0 and 'i' in k0:
                g = lambda q: q[0] if isinstance(q, list) else q
                f = _bez(g(k0['o']['x']), g(k0['o']['y']), g(k0['i']['x']), g(k0['i']['y']), f)
            e = k0.get('e', k1['s'])
            return [a + (b - a) * f for a, b in zip(k0['s'], e)]
    return ks[-1]['s']


def _mat(p, a, s, r):
    c, sn = math.cos(math.radians(r)), math.sin(math.radians(r))
    sx, sy = s[0] / 100, s[1] / 100
    m = [c * sx, -sn * sy, sn * sx, c * sy]
    tx = p[0] - (m[0] * a[0] + m[1] * a[1]); ty = p[1] - (m[2] * a[0] + m[3] * a[1])
    return (m[0], m[1], m[2], m[3], tx, ty)


def _mul(A, B):
    return (A[0] * B[0] + A[1] * B[2], A[0] * B[1] + A[1] * B[3], A[2] * B[0] + A[3] * B[2], A[2] * B[1] + A[3] * B[3],
            A[0] * B[4] + A[1] * B[5] + A[4], A[2] * B[4] + A[3] * B[5] + A[5])


def _apply(M, p): return (M[0] * p[0] + M[1] * p[1] + M[4], M[2] * p[0] + M[3] * p[1] + M[5])


def _inv(M):
    det = M[0] * M[3] - M[1] * M[2]
    if abs(det) < 1e-9: det = 1e-9
    a, b, c, d = M[3] / det, -M[1] / det, -M[2] / det, M[0] / det
    return (a, b, c, d, -(a * M[4] + b * M[5]), -(c * M[4] + d * M[5]))


def _ks_mat(ks, t):
    return _mat(prop_at(ks.get('p'), t, [0, 0]), prop_at(ks.get('a'), t, [0, 0]),
                prop_at(ks.get('s'), t, [100, 100]), prop_at(ks.get('r'), t, [0])[0])


def _group_chains(L):
    def rec(items, chain):
        for it in items:
            if it['ty'] == 'gr':
                c2 = chain + [gtr(it)]
                yield it, c2
                yield from rec(it['it'], c2)
    yield from rec(L.get('shapes', []), [])


CLOTH = ('тело', 'рубах', 'футб', 'штан', 'body', 'shirt', 'pants', 'ручка', 'sleeve')


def cel3_group(g, Mt, turn=None, light=(-0.6, -0.75), k=0.7, hk=0.13, bounce=0.93, gloss=True, step=6):
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
    if w * h < 1800 or min(w, h) < 18: return False
    cx, cy = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
    white = min(base) > 0.9
    sh = list(ART_SHADOW) if white else [c * 0.7 + d * 0.13 for c, d in zip(base, (0.3, 0.12, 0.55))]
    bc = [a + (b - a) * 0.55 for a, b in zip(sh, base)]
    hi = [a + (1 - a) * 0.6 for a in base]
    hiA = 0 if (white or not gloss or w * h < 3500) else 0.7
    e = 0.012
    stops = lot._gstops([(0, hi, hiA), (hk, hi, hiA), (hk + e, sh, 0), (k, sh, 0), (k + e, sh, 1),
                         (bounce, sh, 1), (bounce + e, bc, 1), (1, bc, 1)])

    def local_centre(t):
        M = Mt(t); Mi = _inv(M)
        cw = _apply(M, (cx, cy))
        sc = math.sqrt(abs(M[0] * M[3] - M[1] * M[2]))
        yaw, pitch = (turn(t) if turn else (0, 0))
        pw = (cw[0] + (light[0] * 0.38 * w - math.sin(math.radians(yaw)) * 0.5 * w) * sc,
              cw[1] + (light[1] * 0.38 * h - math.sin(math.radians(pitch)) * 0.5 * h) * sc)
        return _apply(Mi, pw)

    def dmax(c): return max(math.hypot(v[0] - c[0], v[1] - c[1]) for v in vs) * 1.01
    samples = [(t, local_centre(t)) for t in list(range(0, T, step)) + [T]]
    moving = max(math.hypot(c[0] - samples[0][1][0], c[1] - samples[0][1][1]) for _, c in samples) > 0.6
    gf = {'ty': 'gf', 'nm': 'cel3', 'o': st(100), 'r': 1, 't': 2, 'h': st(0), 'a': st(0), 'g': {'p': 8, 'k': st(stops)}}
    if moving:
        gf['s'] = anim([(t, [c[0], c[1]], 'lin') for t, c in samples])
        gf['e'] = anim([(t, [c[0] + dmax(c), c[1]], 'lin') for t, c in samples])
    else:
        c0 = samples[0][1]; gf['s'] = st(list(c0)); gf['e'] = st([c0[0] + dmax(c0), c0[1]])
    g['it'].insert(g['it'].index(fl), gf)
    return True


def shade_world(C, layers, YP=None, head_ind=None, step=10):
    turn = None
    if YP:
        YPd = [(t, list(v)) for t, v in YP]
        turn = lambda t: _mono_interp(YPd, t)
    byind = {x['ind']: x for x in C.j['layers']}
    cache = {}

    def W(L, t):
        key = (L['ind'], t)
        if key not in cache:
            M = _ks_mat(L['ks'], t); cur = L
            while cur.get('parent') in byind:
                cur = byind[cur['parent']]; M = _mul(_ks_mat(cur['ks'], t), M)
            cache[key] = M
        return cache[key]
    for L in layers:
        rides = False; cur = L
        while cur is not None:
            if cur['ind'] == head_ind: rides = True; break
            cur = byind.get(cur.get('parent'))
        cloth = any(k_ in L['nm'].lower() for k_ in CLOTH)
        for g, chain in list(_group_chains(L)):
            def Mt(t, L=L, chain=chain):
                M = W(L, t)
                for tr_ in chain: M = _mul(M, _ks_mat(tr_, t))
                return M
            cel3_group(g, Mt, turn if rides else None, gloss=not cloth, step=step)

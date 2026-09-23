"""Magic lamp v3 in the Telegram-gift 3D style (learned from the 25 refs):
- no ink: gradient outlines (gs) in darker metal
- metal = multi-band linear gradients (7-9 stops); vertical alpha overlay for roundness
- tubes = one morphing envelope; gradient axis follows the tube (reflections slide)
- perspective projection; running trim-path glints along edges; sphere gems."""
import sys, math, json
from lot import *

OUT = sys.argv[1]
T = 180
PHI = math.radians(22)
CX, CY = 256, 318
FOC = 900.0
TT = list(range(0, T, 4)) + [T]
TIMES = list(range(0, T, 3)) + [T]

def theta(t): return 2 * math.pi * t / T

def proj(x, y, z):
    sy = y * math.cos(PHI) - z * math.sin(PHI)
    d = z * math.cos(PHI) + y * math.sin(PHI)
    k = FOC / (FOC - d)
    return (CX + x * k, CY - sy * k), d

# ---------------------------------------------------------------- materials
def hexc(h): return [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
GOLD_BANDS = [(0, '#6e3f04'), (0.1, '#b87a10'), (0.24, '#f2c043'), (0.33, '#fff4c4'), (0.42, '#f6cd57'),
              (0.6, '#cf8f16'), (0.76, '#9c5d09'), (0.88, '#d9a032'), (1, '#7a4705')]
EDGE_BANDS = [(0, '#4a2702'), (0.3, '#8f5507'), (0.45, '#d7a13a'), (0.6, '#8f5507'), (1, '#4a2702')]
def gstops(bands, alphas=None):
    col = []; op = []
    for i, (p, h) in enumerate(bands):
        col += [p] + hexc(h)
        if alphas: op += [p, alphas[i]]
    return col + op
def gfill_lin(bands, s, e, alphas=None):
    return {'ty': 'gf', 'o': st(100), 'r': 1, 't': 1, 'h': st(0), 'a': st(0),
            'g': {'p': len(bands), 'k': st(gstops(bands, alphas))}, 's': _p(s), 'e': _p(e)}
def gstroke_lin(bands, s, e, w):
    return {'ty': 'gs', 'o': st(100), 'w': st(w), 'lc': 2, 'lj': 2, 't': 1, 'h': st(0), 'a': st(0),
            'g': {'p': len(bands), 'k': st(gstops(bands))}, 's': _p(s), 'e': _p(e)}
def _p(v): return v if isinstance(v, dict) else st(list(v))
ROUND = [(0, '#fff6d0'), (0.35, '#ffffff'), (0.7, '#000000'), (1, '#3a1e00')]
ROUND_A = [0.35, 0, 0, 0.35]

C = Comp({'v': '5.5.2', 'fr': 60, 'ip': 0, 'op': T, 'w': 512, 'h': 512, 'nm': 'magic lamp', 'ddd': 0, 'assets': [], 'layers': []})
def precomp(pid, layers): C.j['assets'].append({'id': pid, 'layers': layers})
def pre_layer(pid, nm, ks, ip=0, op=T, st_=0, parent=None):
    L = {'ddd': 0, 'ind': C.new_ind(), 'ty': 0, 'nm': nm, 'refId': pid, 'sr': 1, 'ks': ks, 'ao': 0,
         'w': 512, 'h': 512, 'ip': ip, 'op': op, 'st': st_, 'bm': 0}
    if parent is not None: L['parent'] = parent
    return L
rig = C.null('FLOAT', lks(p=lin(sampled(lambda t: [256, 256 + 7 * math.sin(2 * math.pi * t / T)], 4)), a=(256, 256)))

# ---------------------------------------------------------------- body of revolution
PARTS = {
    'foot': [(0, 30), (4, 34), (10, 28), (14, 24)],
    'bowl': [(12, 26), (20, 58), (32, 78), (44, 80), (56, 68), (64, 46), (68, 34)],
    'neck': [(64, 34), (70, 32), (74, 36)],
    'lid':  [(72, 38), (80, 34), (88, 25), (95, 14), (99, 5), (100, 0)],
    'knob': [(99, 4), (103, 9), (109, 10), (115, 8), (119, 3), (120, 0)],
}
def hull(pts):
    pts = sorted(set((round(p[0], 2), round(p[1], 2)) for p in pts))
    def cross(o, a, b): return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0: up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]
def part_outline(rings, n=48):
    pts = []
    for y, r in rings:
        for k in range(n):
            a = 2 * math.pi * k / n
            pts.append(proj(r * math.sin(a), y, r * math.cos(a))[0])
    return hull(pts)
def bowl_r(y):
    pr = PARTS['bowl']
    for (y0, r0), (y1, r1) in zip(pr, pr[1:]):
        if y0 <= y <= y1: return r0 + (r1 - r0) * (y - y0) / (y1 - y0)
    return pr[-1][1]

body_layers = []
for name in ('foot', 'bowl', 'neck', 'lid', 'knob'):
    pts = part_outline(PARTS[name])
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    items = [shape(path(pts, closed=True, smooth=0.2)),
             gstroke_lin(EDGE_BANDS, (x0, 0), (x1, 0), 5),
             gfill_lin(ROUND, (0, y0), (0, y1), ROUND_A),                     # vertical roundness overlay
             gfill_lin(GOLD_BANDS, (x0 - 2, 0), (x1 + 2, 0))]                  # anisotropic metal bands
    body_layers.append(C.layer(name, [group(items, nm=name)], lks(), parent=rig['ind']))

def front_arc(y, r, n=24, a0=-math.pi / 2, a1=math.pi / 2):
    return [proj(r * math.sin(a), y, r * math.cos(a))[0] for a in [a0 + (a1 - a0) * k / n for k in range(n + 1)]]
def band_ring(y, r, w, dark='#7a4705', lite='#ffe79a'):
    pts = front_arc(y, r)
    xs = [p[0] for p in pts]
    return [group([shape(path(pts, closed=False, smooth=0.9)), stroke(hexc(lite), 2.5)], tr(p=(0, -w * 0.35))),
            group([shape(path(pts, closed=False, smooth=0.9)), gstroke_lin(GOLD_BANDS, (min(xs), 0), (max(xs), 0), w)]),
            group([shape(path(pts, closed=False, smooth=0.9)), stroke(hexc(dark), w + 4)])]
rims = C.layer('rims', band_ring(38, 80.5, 9) + band_ring(66, 42, 6) + band_ring(13, 27, 5), lks(), parent=rig['ind'])

# ---------------------------------------------------------------- engraving (period 18, precomp reused 10x)
meridians = []
for m in range(10):
    a0 = 2 * math.pi * m / 10
    def mer(t, a0=a0):
        a = a0 + theta(t)
        ys = [16 + 6 * k for k in range(0, 9)]
        return [proj(bowl_r(y) * 0.995 * math.sin(a), y, bowl_r(y) * 0.995 * math.cos(a))[0] for y in ys], math.cos(a)
    PT = list(range(0, 19, 2))
    shp = anim([(t, [path(mer(t)[0], closed=False, smooth=0.9)], 'lin') for t in PT])
    op = anim([(t, 100 * smoothstep(0.05, 0.35, mer(t)[1]), 'lin') for t in PT])
    meridians.append(group([{'ty': 'sh', 'ks': shp}, stroke(hexc('#fff0b0'), 2)], tr(o=op, p=(1.5, 0))))
    meridians.append(group([{'ty': 'sh', 'ks': shp}, stroke(hexc('#8a5208'), 3)], tr(o=op)))
precomp('eng', [C.layer('engraving', meridians, lks(), ip=0, op=19)])
mer_layers = [pre_layer('eng', 'engraving', lks(), ip=18 * k, op=18 * (k + 1), st_=18 * k, parent=rig['ind']) for k in range(10)]

# ---------------------------------------------------------------- gems: glossy spheres in gold bezels
GEMS = [(0, '#e0203a'), (2 * math.pi / 3, '#2a74f0'), (4 * math.pi / 3, '#2fc15a')]
gem_groups = []
for a0, colr in GEMS:
    def gem(t, a0=a0, lift=0.0):
        a = a0 + theta(t)
        return proj((81 + lift) * math.sin(a), 38, (81 + lift) * math.cos(a))[0], math.cos(a)
    op = anim([(t, 100 * smoothstep(-0.02, 0.22, gem(t)[1]), 'lin') for t in TIMES])
    c = hexc(colr)
    bands = [(0, '#ffffff'), (0.18, '#' + ''.join('%02x' % int((v + (1 - v) * 0.5) * 255) for v in c)), (0.5, colr),
             (0.8, '#' + ''.join('%02x' % int(v * 0.45 * 255) for v in c)), (1, '#' + ''.join('%02x' % int((v * 0.8 + 0.2) * 255) for v in c))]
    sphere = group([group([ellipse((5, 4), (-5, -6)), fill((1, 1, 1))]),
                    group([ellipse((22, 22)), {'ty': 'gf', 'o': st(100), 'r': 1, 't': 2, 'h': st(0), 'a': st(0),
                                              'g': {'p': 5, 'k': st(gstops(bands))}, 's': st([-5, -6]), 'e': st([13, -6])}])],
                   tr(p=anim([(t, list(gem(t, lift=5)[0]), 'lin') for t in TIMES]), o=op))
    bezel = group([ellipse((32, 32)), gstroke_lin(EDGE_BANDS, (-16, 0), (16, 0), 3), gfill_lin(GOLD_BANDS, (-16, 0), (16, 0))],
                  tr(p=anim([(t, list(gem(t)[0]), 'lin') for t in TIMES]),
                     s=anim([(t, [max(1, 100 * gem(t)[1]), 100], 'lin') for t in TIMES]), o=op))
    gem_groups += [sphere, bezel]
gem_layer = C.layer('gems', gem_groups, lks(), parent=rig['ind'])

# ---------------------------------------------------------------- tubes as one envelope each
def spout_center(s):
    y = 40 + 52 * s ** 2.2; r = 18 * (1 - s) + 7 * s
    u = bowl_r(40) - 9 + 125 * s
    return u, y, r
def handle_center(s):
    psi = -1.3 + 2.6 * s
    y = 39 - 23 * math.sin(psi)
    u = bowl_r(y) - 4 + 46 * (math.cos(psi) - math.cos(1.3)); r = 8.5
    return u, y, r
BODY_SIL = [part_outline(PARTS[n]) for n in PARTS]
def inside_body(p):
    for poly in BODY_SIL:
        inside = False
        for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):
            if (y0 > p[1]) != (y1 > p[1]) and p[0] < x0 + (x1 - x0) * (p[1] - y0) / (y1 - y0):
                inside = not inside
        if inside: return True
    return False
def centre_at(t, fn, side, s_):
    a = theta(t) + side
    u, y, r = fn(s_)
    p, d = proj(u * math.sin(a), y, u * math.cos(a))
    return p, r * FOC / (FOC - d), math.cos(a)
def visible_interval(t, fn, side, m=80):
    """front: whole tube. behind: longest run of the centreline outside the body silhouette."""
    if math.cos(theta(t) + side) >= 0: return 0.0, 1.0
    out = [not inside_body(centre_at(t, fn, side, k / m)[0]) for k in range(m + 1)]
    best, cur = (0, -1), None
    for k, o in enumerate(out + [False]):
        if o and cur is None: cur = k
        if not o and cur is not None:
            if k - 1 - cur > best[1] - best[0]: best = (cur, k - 1)
            cur = None
    if best[1] < best[0]: return 1.0, 1.0
    return best[0] / m, best[1] / m
def smooth_iv(fn, side, TK):
    """visible interval per key, lightly smoothed in time (no hard jumps from the discrete test)"""
    raw = {t: visible_interval(t, fn, side) for t in range(0, T + 1)}
    out = {}
    for t in TK:
        ws = [raw[max(0, min(T, t + d))] for d in (-2, -1, 0, 1, 2)]
        out[t] = (sum(w[0] for w in ws) / 5, sum(w[1] for w in ws) / 5)
    return out

def tube_env(t, fn, side, n=9, s0=0.0, s1=1.0, prev_n=None):
    cs = [centre_at(t, fn, side, s0 + (s1 - s0) * k / n)[:2] for k in range(n + 1)]
    L, R = [], []
    for k in range(len(cs)):
        p0 = cs[max(0, k - 1)][0]; p1 = cs[min(len(cs) - 1, k + 1)][0]
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]; ln = math.hypot(dx, dy) or 1
        nx, ny = -dy / ln, dx / ln
        p, r = cs[k]
        L.append((p[0] + nx * r, p[1] + ny * r)); R.append((p[0] - nx * r, p[1] - ny * r))
    tip, rt = cs[-1]
    ang0 = math.atan2(L[-1][1] - tip[1], L[-1][0] - tip[0])
    cap = [(tip[0] + rt * math.cos(ang0 - math.pi * k / 4), tip[1] + rt * math.sin(ang0 - math.pi * k / 4)) for k in range(1, 4)]
    root, r0 = cs[0]
    angr = math.atan2(R[0][1] - root[1], R[0][0] - root[0])
    capr = [(root[0] + r0 * math.cos(angr - math.pi * k / 4), root[1] + r0 * math.sin(angr - math.pi * k / 4)) for k in range(1, 4)]
    m = len(cs) // 2
    pm, rm = cs[m]
    d = (cs[min(len(cs) - 1, m + 2)][0][0] - cs[max(0, m - 2)][0][0], cs[min(len(cs) - 1, m + 2)][0][1] - cs[max(0, m - 2)][0][1])
    ln = math.hypot(*d) or 1
    nx, ny = -d[1] / ln, d[0] / ln
    # lit side from 3D: cross-section normal facing the light, projected to screen
    sm = s0 + (s1 - s0) * m / n
    ang = theta(t) + side
    def w3(sv):
        u_, y_, _ = fn(sv); return (u_ * math.sin(ang), y_, u_ * math.cos(ang))
    P0, P1 = w3(max(0, sm - 0.05)), w3(min(1, sm + 0.05))
    D = [P1[i] - P0[i] for i in range(3)]; dl = math.sqrt(sum(v * v for v in D)) or 1; D = [v / dl for v in D]
    Lg = (-0.4, 1.0, 0.05)
    nn = [Lg[i] - sum(Lg[j] * D[j] for j in range(3)) * D[i] for i in range(3)]
    nl = math.sqrt(sum(v * v for v in nn)) or 1; nn = [v / nl for v in nn]
    Pm = w3(sm)
    q0 = proj(*Pm)[0]; q1 = proj(Pm[0] + nn[0] * 10, Pm[1] + nn[1] * 10, Pm[2] + nn[2] * 10)[0]
    nx, ny = q1[0] - q0[0], q1[1] - q0[1]; ln2 = math.hypot(nx, ny) or 1; nx, ny = nx / ln2, ny / ln2
    s = (pm[0] + nx * rm * 1.1, pm[1] + ny * rm * 1.1); e = (pm[0] - nx * rm * 1.1, pm[1] - ny * rm * 1.1)
    return L + cap + R[::-1] + capr, s, e, (nx, ny), tip, rt
def tip_at(t): return centre_at(t % T, spout_center, 0.0, 1.0)[0]

LIGHT3 = (-0.4, 1.0, 0.05)
def lit_sections(t, fn, side, s0, s1, n):
    """per section: screen centre, screen radius, screen unit vector toward the lit side"""
    ang = theta(t) + side
    def w3(sv):
        u_, y_, r_ = fn(sv); return (u_ * math.sin(ang), y_, u_ * math.cos(ang)), r_
    out = []
    for k in range(n + 1):
        sv = s0 + (s1 - s0) * k / n
        P, r = w3(sv)
        Pa, _ = w3(max(0, sv - 0.03)); Pb, _ = w3(min(1, sv + 0.03))
        D = [Pb[i] - Pa[i] for i in range(3)]; dl = math.sqrt(sum(v * v for v in D)) or 1; D = [v / dl for v in D]
        dot = sum(LIGHT3[i] * D[i] for i in range(3))
        nn = [LIGHT3[i] - dot * D[i] for i in range(3)]; nl = math.sqrt(sum(v * v for v in nn)) or 1; nn = [v / nl for v in nn]
        (q0, d0) = proj(*P); q1 = proj(P[0] + nn[0] * 10, P[1] + nn[1] * 10, P[2] + nn[2] * 10)[0]
        lx, ly = q1[0] - q0[0], q1[1] - q0[1]; ll = math.hypot(lx, ly) or 1
        out.append((q0, r * FOC / (FOC - d0), (lx / ll, ly / ll)))
    return out
def envelope(secs, rk, off):
    """closed outline around circles (centre + light*off*r, radius rk*r)"""
    cs = [((c[0] + l[0] * off * r, c[1] + l[1] * off * r), rk * r) for c, r, l in secs]
    L, R = [], []
    for k in range(len(cs)):
        p0 = cs[max(0, k - 1)][0]; p1 = cs[min(len(cs) - 1, k + 1)][0]
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]; ln = math.hypot(dx, dy) or 1
        nx, ny = -dy / ln, dx / ln
        p, r = cs[k]
        L.append((p[0] + nx * r, p[1] + ny * r)); R.append((p[0] - nx * r, p[1] - ny * r))
    tip, rt = cs[-1]; root, r0 = cs[0]
    a0 = math.atan2(L[-1][1] - tip[1], L[-1][0] - tip[0]); ar = math.atan2(R[0][1] - root[1], R[0][0] - root[0])
    cap = [(tip[0] + rt * math.cos(a0 - math.pi * k / 4), tip[1] + rt * math.sin(a0 - math.pi * k / 4)) for k in range(1, 4)]
    capr = [(root[0] + r0 * math.cos(ar - math.pi * k / 4), root[1] + r0 * math.sin(ar - math.pi * k / 4)) for k in range(1, 4)]
    P = path(L + cap + R[::-1], closed=True, smooth=0.25)
    for k_ in ('v', 'i', 'o'): P[k_] = [[round(a_), round(b_)] for a_, b_ in P[k_]]
    return P
def swap_pair(name, items, side):
    precomp(name, [C.layer(name, items, lks())])
    # back copy always on; front copy fades in/out around the sideways pose -> only the part overlapping the body changes
    fo = anim([(t, 100 * smoothstep(-0.12, 0.12, math.cos(theta(t) + side)), 'lin') for t in range(0, T + 1)])
    return pre_layer(name, name + ' front', lks(o=fo), parent=rig['ind']), pre_layer(name, name + ' back', lks(), parent=rig['ind'])
def tube_layer(fn, side, name, opening=False, n=8):
    TK = list(range(0, T, 5)) + [T]
    secs = {t: lit_sections(t, fn, side, 0.0, 1.0, n) for t in TK}
    passes = [(1.0, 0.0, '#4a2702', 2.5), (1.0, 0.0, '#9c5d09', 0), (0.72, 0.26, '#d89a22', 0),
              (0.44, 0.46, '#f6cd57', 0), (0.16, 0.66, '#fff4c4', 0)]
    items = []
    for rk, off, col, grow in reversed(passes):
        shp = anim([(t, [envelope([(c, r + grow, l) for c, r, l in secs[t]], rk, off)], 'lin') for t in TK])
        items.append(group([{'ty': 'sh', 'ks': shp}, fill(hexc(col))], nm=col))
    if opening:
        items.insert(0, group([ellipse((1, 1)), fill(hexc('#2b1300')), gstroke_lin(EDGE_BANDS, (-0.5, 0), (0.5, 0), 0.12)],
                              tr(p=anim([(t, list(secs[t][-1][0]), 'lin') for t in TK]),
                                 s=anim([(t, [secs[t][-1][1] * 190, secs[t][-1][1] * 110], 'lin') for t in TK]),
                                 r=anim([(t, -14 * math.sin(theta(t) + side), 'lin') for t in TK]))))
    return swap_pair(name, items, side)
spoutF, spoutB = tube_layer(spout_center, 0.0, 'spout', opening=True)

def stroke_tube(fn, side, name, r=8.5, n=12):
    TK = list(range(0, T, 5)) + [T]
    def rp(P):
        for k_ in ('v', 'i', 'o'): P[k_] = [[round(a_, 1), round(b_, 1)] for a_, b_ in P[k_]]
        return P
    shp = anim([(t, [rp(path([centre_at(t, fn, side, k / n)[0] for k in range(n + 1)], closed=False, smooth=0.8))], 'lin') for t in TK])
    layers_ = [(2 * r + 5, '#4a2702', (0, 0)), (2 * r, '#9c5d09', (0, 0)), (1.35 * r, '#e0a52a', (-0.22 * r, -0.28 * r)),
               (0.75 * r, '#f6cd57', (-0.38 * r, -0.46 * r)), (0.3 * r, '#fff4c4', (-0.5 * r, -0.62 * r))]
    items = []
    for w, col, off in reversed(layers_):
        stk = stroke(hexc(col), w); stk['lc'] = 1                     # butt caps: flat ends on the body surface
        trimmed = w < 2 * r                                           # offset light strokes: keep them off the very ends
        its = [{'ty': 'sh', 'ks': shp}] + ([trim(s=6, e=94)] if trimmed else []) + [stk]
        items.append(group(its, tr(p=off)))
    return swap_pair(name, items, side)
handleF, handleB = stroke_tube(handle_center, math.pi, 'handle')

# ---------------------------------------------------------------- running glints (trim paths) along edges
def glint_edge(pts, t0, dur=26, w=3.5, span=14):
    p = path(pts, closed=False, smooth=0.9)
    return group([shape(p), trim(s=anim([(t0, 0), (t0 + dur, 100 - span)], ease='io'), e=anim([(t0, span), (t0 + dur, 100)], ease='io')),
                  stroke((1, 1, 0.9), w)], tr(o=anim([(t0 - 1, 0), (t0, 100), (t0 + dur, 100), (t0 + dur + 1, 0)], hold=True)))
bowl_sil = part_outline(PARTS['bowl'])
left_edge = sorted([p for p in bowl_sil if p[0] < CX - 20], key=lambda p: p[1])
lid_sil = sorted([p for p in part_outline(PARTS['lid']) if p[0] < CX], key=lambda p: p[1])
glints = C.layer('glints', [glint_edge(left_edge, 20), glint_edge(front_arc(38, 82), 70, 34, 3), glint_edge(lid_sil, 110, 22, 3),
                            glint_edge(left_edge, 140)], lks(), parent=rig['ind'])
# fixed window reflections on the bowl (soft vertical streaks)
refl = C.layer('refl', [group([shape(path([(-6, -26), (4, -30), (6, 24), (-4, 28)], smooth=0.5)), fill((1, 1, 0.95), 55)], tr(p=proj(-44, 44, 66)[0], r=8)),
                        group([shape(path([(-3, -18), (2, -20), (3, 16), (-2, 18)], smooth=0.5)), fill((1, 1, 0.95), 45)], tr(p=proj(-24, 44, 76)[0], r=4))],
               lks(), parent=rig['ind'])

# ---------------------------------------------------------------- smoke, sparkles, glow, floor
smoke = []
for k in range(6):
    t0 = k * 30; life = 70
    keys = []
    for u in range(0, life + 1, 10):
        base = tip_at(t0 + u)
        h = u * 1.6
        pts = [(base[0] + 18 * math.sin(i * 0.9 + u * 0.12 + k) * (i / 5), base[1] - 8 - h * (i / 5)) for i in range(6)]
        keys.append((t0 + u, [path(pts, closed=False, smooth=0.9)], 'lin'))
    col = (0.62, 0.45, 1.0) if k % 2 else (0.45, 0.8, 1.0)
    smoke.append(C.layer('smoke', [group([{'ty': 'sh', 'ks': anim(keys)},
                                          trim(s=anim([(t0, 0), (t0 + life, 100)]), e=anim([(t0, 0), (t0 + life * 0.45, 100)])),
                                          stroke(col, anim([(t0, 14), (t0 + life, 3)]), o=anim([(t0, 80), (t0 + life, 0)]))])],
                         lks(), ip=t0, op=t0 + life, parent=rig['ind']))
smoke += wrap_copies(C, smoke)
fx = [sparkle(C, t, p, r, color=(1, 0.97, 0.75), parent=rig['ind'], dur=24) for t, p, r in
      ((8, (150, 190), 14), (40, (380, 170), 12), (75, (130, 300), 10), (110, (400, 290), 14), (150, (200, 140), 11))]
fx += wrap_copies(C, fx)
glowL = glow(C, (256, 260), 210, (1, 0.82, 0.4), lin(sampled(lambda t: 45 + 12 * math.sin(2 * math.pi * 2 * t / T), 6)), parent=rig['ind'])
shadow = C.layer('floor', [group([ellipse((200, 36)), {'ty': 'gf', 'o': st(100), 'r': 1, 't': 2, 'h': st(0), 'a': st(0),
                                                       'g': {'p': 2, 'k': st(gstops([(0, '#000000'), (1, '#000000')], [0.35, 0]))},
                                                       's': st([0, 0]), 'e': st([100, 0])}])],
                 lks(p=(256, 354), s=lin(sampled(lambda t: [100 - 8 * math.sin(2 * math.pi * t / T), 100 - 8 * math.sin(2 * math.pi * t / T)], 6))))

C.j['layers'] = smoke + fx + [spoutF, handleF, glints, gem_layer] + mer_layers + [rims] + body_layers[::-1] + [spoutB, handleB, glowL, shadow, rig]
C.save('lamp', OUT)

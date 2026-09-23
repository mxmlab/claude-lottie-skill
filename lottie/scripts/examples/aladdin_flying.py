"""Aladdin flying on the carpet, smiling. Built from aladdin_design.PARTS (the same data as the SVG)."""
import sys, math, random
from lot import *
from lot7 import *
from lot7 import _mono_interp
import aladdin_design as AD

OUT = sys.argv[1]
random.seed(2)
C = Comp({'v': '5.5.2', 'fr': 60, 'ip': 0, 'op': T, 'w': 512, 'h': 512, 'nm': 'aladdin', 'ddd': 0, 'assets': [], 'layers': []})

def ellipse_pts(cx, cy, w, h, n=16):
    return [(cx + w / 2 * math.cos(2 * math.pi * k / n), cy + h / 2 * math.sin(2 * math.pi * k / n)) for k in range(n)]

GROUPS = {}
def part_group(p):
    g = p['geom']
    items = []
    if isinstance(g, tuple) and g[0] == 'ellipse':
        pts = ellipse_pts(*g[1:])
        items.append(shape(path(pts, closed=True, smooth=0.55)))
    else:
        items.append(shape(path(g, closed=p['closed'], smooth=p['smooth'])))
    if p['stroke'] is not None and p['w']: items.append(stroke(p['stroke'], p['w']))
    if p['fill'] is not None: items.append(fill(p['fill'], p['alpha']))
    grp = group(items, nm=p['name'])
    GROUPS[p['name']] = grp
    return grp

LAY = {}
for lname in AD.LAYER_ORDER:
    parts = [p for p in AD.PARTS if p['layer'] == lname]
    LAY[lname] = C.layer(lname, [part_group(p) for p in reversed(parts)], lks())   # first part = back -> list reversed (first = top)

# ---------------------------------------------------------------- rig
rig = C.null('FLY', lks(p=lin(sampled(lambda t: [256, 256 + 9 * math.sin(2 * math.pi * 2 * t / T)], 4)), a=(256, 256),
                          r=lin(sampled(lambda t: 2.5 * math.sin(2 * math.pi * 2 * t / T - 0.9), 4))))
def wave_dy(x, t):
    env = 0.3 + 0.9 * (abs(x - 256) / 220) ** 1.3
    return 8 * env * math.sin(2 * math.pi * (x - 40) / 300 + 2 * math.pi * 3 * t / T)
char = C.null('CHAR', lks(p=lin(sampled(lambda t: [256, 274 + wave_dy(256, t) * 0.8], 3)), a=(256, 256)), parent=rig['ind'])
for n in ('carpet', 'tasselL', 'tasselR'): LAY[n]['parent'] = rig['ind']
for n in ('legs', 'body', 'armBack'): LAY[n]['parent'] = char['ind']
# body: breathing / wind jelly
C.pivot(LAY['body'], (256, 346), s=lin(sampled(lambda t: [100 + 1.5 * math.sin(2 * math.pi * 3 * t / T), 100 + 3 * math.sin(2 * math.pi * 3 * t / T)])))

NECK = (256, 272)
headR = spring([(0, 0), (40, -2), (60, 3), (100, 1), (140, 3), (160, 0)], f=1.4, z=0.55, idle=wave(1.5, 2, 0.4))
head = C.null('HEAD', lks(p=NECK, a=NECK, r=lin(headR)), parent=char['ind'])
for n in ('head', 'face', 'turban', 'ears'): LAY[n]['parent'] = head['ind']

# ---------------------------------------------------------------- waving arm: shoulder -> hand with lag
SH_R, WR_R = (304, 282), (378, 222)
armW = spring([(0, 0), (10, 8), (26, -6), (42, 8), (58, -6), (74, 8), (90, -6), (106, 8), (122, -6), (138, 8), (154, -6), (170, 0)],
              f=1.6, z=0.5)
LAY['armFront']['parent'] = char['ind']
C.pivot(LAY['armFront'], SH_R, r=lin(armW))
handW = spring([(t + 4, -v * 1.8) for t, v in [(0, 0), (10, 8), (26, -6), (42, 8), (58, -6), (74, 8), (90, -6), (106, 8), (122, -6), (138, 8), (154, -6), (170, 0)]],
               f=2.0, z=0.45)
gxf(GROUPS['handR'], WR_R, r=lin(handW))
C.pivot(LAY['armBack'], (208, 282), r=lin(sampled(lambda t: 1.5 * math.sin(2 * math.pi * 2 * t / T + 1))))

# ---------------------------------------------------------------- deformations (one composer)
D = Deformer()
TS = list(range(0, T, 6)) + [T]
# carpet wave
def carpet_fn(t):
    return lambda p: (p[0], p[1] + wave_dy(p[0], t))
D.add([GROUPS[n] for n in ('thickness', 'carpet', 'border', 'pattern')], [(t, t) for t in TS], carpet_fn, exact=True)
# tassels: ride the edge wave + trail behind with lag
def tassel_fn(side):
    def mk(t):
        def f(p):
            base = wave_dy(p[0], t)
            sway = 6 * math.sin(2 * math.pi * 3 * (t - 8) / T + (0 if side == 'L' else 1.3))
            k = min(1, abs(p[0] - (40 if side == 'L' else 470)) / 26) if False else 1
            return (p[0], p[1] + base + sway * (0.3 if side == 'R' else 1))
        return f
    return mk
D.add([GROUPS[f'tasselL{i}'] for i in range(4)], [(t, t) for t in TS], tassel_fn('L'), exact=True)
D.add([GROUPS[f'tasselR{i}'] for i in range(4)], [(t, t) for t in TS], tassel_fn('R'), exact=True)
# wind: plume + sash tail flutter (bend from the root)
D.add([GROUPS['plume']], [(t, 10 * math.sin(2 * math.pi * 4 * t / T) - 6) for t in TS], lambda a: bend_fn((262, 118), a, 70), exact=True)
D.add([GROUPS['sashTail']], [(t, 12 * math.sin(2 * math.pi * 4 * t / T + 1)) for t in TS], lambda a: bend_fn((300, 344), a, 50), exact=True)
# smile: closed -> open grin, with laugh pulses
OPEN = [(0, 0), (34, 0), (46, 1.0), (70, 0.85), (82, 1.0), (104, 0.85), (116, 1.0), (140, 1.0), (156, 0), (T, 0)]
def upper_y(x): t = (x - 256) / 32; return 246 + 9 * max(0.0, 1 - t * t)
def mouth_fn(k):
    """corners stay (slightly lifted); lower lip drops in a round arc; upper lip lifts a touch"""
    def f(p):
        t = (p[0] - 256) / 33; u = max(0.0, 1 - t * t)
        lift = -2 * k * (1 - u)                                # corners curl up
        if p[1] > upper_y(p[0]) + 1.2:
            return (p[0], p[1] + k * 22 * u ** 0.8 + lift)
        return (p[0], p[1] - k * 3 * u + lift)
    return f
# teeth (under the upper lip) + tongue, only while open
face_L = LAY['face']
teeth = group([shape(path([(232, 247), (256, 254), (280, 247), (278, 251), (256, 259), (234, 251)], smooth=0.5)), fill((1, 1, 1))],
              tr(o=anim([(t, 100 * smoothstep(0.35, 0.6, k), 'lin') for t, k in [(0, 0), (34, 0), (46, 1.0), (70, 0.85), (82, 1.0), (104, 0.85), (116, 1.0), (140, 1.0), (156, 0), (T, 0)]])), nm='teeth')
tongue = group([ellipse((26, 12)), fill((0.95, 0.45, 0.5))],
               tr(p=(256, 266), s=anim([(t, [100 * k, 100 * k], 'lin') for t, k in [(0, 0), (34, 0), (46, 1.0), (70, 0.85), (82, 1.0), (104, 0.85), (116, 1.0), (140, 1.0), (156, 0), (T, 0)]])), nm='tongue')
mi = face_L['shapes'].index(GROUPS['mouth'])
face_L['shapes'][mi:mi] = [teeth, tongue]
GROUPS['teeth'] = teeth
D.add([GROUPS['mouth']], OPEN, mouth_fn)
def teeth_fn(k):
    def f(p):
        u = max(0.0, 1 - ((p[0] - 256) / 34) ** 2)
        return (p[0], p[1] - k * 3 * u - 2 * k * (1 - u))
    return f
D.add([GROUPS['teeth']], OPEN, teeth_fn)
# eyes -> happy arcs while grinning, blinks
def eye_fn(c, w, arch):
    def mk(k):
        def f(p):
            dx = (p[0] - c[0]) / w
            return (c[0] + (p[0] - c[0]) * (1 + 0.1 * k), c[1] + (p[1] - c[1]) * (1 - 0.8 * k) - k * arch * (1 - min(1, dx * dx)) + k * 6)
        return f
    return mk
EYE = [(0, 0), (16, 0), (19, 1), (22, 0), (36, 0), (48, 0.9), (138, 0.9), (154, 0), (164, 0), (167, 1), (170, 0), (T, 0)]
D.add([GROUPS['eyeL']], EYE, eye_fn((212, 206), 17, 12))
D.add([GROUPS['eyeR']], EYE, eye_fn((300, 206), 17, 12))
hl = anim([(t, [100 * (1 - k), 100 * (1 - k)], 'lin') for t, k in EYE])
gxf(GROUPS['hlL'], (204, 194), s=hl); gxf(GROUPS['hlR'], (292, 194), s=hl)
BR = [(0, [0, 0]), (36, [0, 0]), (48, [0, -8]), (138, [0, -8]), (154, [0, 0]), (T, [0, 0])]
gxf(GROUPS['browL'], (212, 168), dp=[(t, v, 'io') for t, v in BR], r=anim([(0, 0), (36, 0), (48, -6), (138, -6), (154, 0), (T, 0)]))
gxf(GROUPS['browR'], (300, 168), dp=[(t, v, 'io') for t, v in BR], r=anim([(0, 0), (36, 0), (48, 6), (138, 6), (154, 0), (T, 0)]))
blush = anim([(0, 45), (36, 45), (48, 75), (138, 75), (154, 45), (T, 45)])
for n in ('blushL', 'blushR'):
    for it in GROUPS[n]['it']:
        if it['ty'] == 'fl': it['o'] = blush
# fake-3D head turn: one field for the whole head
HC, HRD = (256, 190), 110
YP = [(0, (-8, 0)), (46, (6, -5)), (90, (9, -3)), (130, (2, -6)), (160, (-8, 0)), (T, (-8, 0))]
head_groups = [g for n in ('head', 'face', 'turban', 'ears') for g in LAY[n]['shapes'] if g['ty'] == 'gr']
D.add(head_groups, YP, turn_fn(HC, HRD, 'surface', 1.0))
D.build(step=10)

# ---------------------------------------------------------------- FX: wind streaks, clouds, sparkle trail
fx_front, fx_back = [], []
def streak(t0, y, x0, L, w, dur=24):
    shp = path([(0, 0), (L * 0.15, -w / 2), (L, -w * 0.12), (L, w * 0.12), (L * 0.15, w / 2)], smooth=0.35)
    return C.layer('streak', [group([shape(shp), fill((1, 1, 1), 85)])],
                   lks(p=anim([(t0, [x0, y]), (t0 + dur, [x0 - 420, y])], ease='lin'),
                       s=anim([(t0, [30, 100]), (t0 + dur * 0.4, [100, 100]), (t0 + dur, [60, 60])]),
                       o=anim([(t0, 0), (t0 + 5, 100), (t0 + dur - 6, 100), (t0 + dur, 0)])), ip=t0, op=t0 + dur + 1)
for k in range(8):
    t0 = (k * 23 + random.randint(0, 8)) % T
    front = k % 3 == 0
    y = random.choice([22, 482]) if front else random.choice([70, 110, 300, 350, 470, 250, 30])
    lay = streak(t0, y, random.uniform(520, 600), random.uniform(90, 150), random.uniform(6, 10))
    (fx_front if front else fx_back).append(lay)
def cloud(t0, y, sc, life=150):
    items = []
    for dx, dy, r in ((-40, 6, 30), (0, -10, 42), (40, 4, 32), (0, 14, 30)):
        items.append(group([ellipse((2 * r, 2 * r), (dx, dy)), fill((1, 1, 1), 80)]))
    return C.layer('cloud', items, lks(p=anim([(t0, [600, y]), (t0 + life, [-100, y])], ease='lin'), s=(sc, sc)), ip=t0, op=t0 + life)
fx_back += [cloud(0, 120, 70), cloud(60, 420, 90), cloud(120, 60, 55)]
fx_back += wrap_copies(C, fx_back)
fx_front += wrap_copies(C, fx_front)
spark = []
for k, t in enumerate(range(0, T, 20)):
    spark.append(sparkle(C, t, (30 + 10 * (k % 2), 400 + 16 * (k % 3)), 9 + 3 * (k % 2), color=(1, 0.9, 0.5), dur=22))
spark += wrap_copies(C, spark)

order = fx_front + spark + [LAY[n] for n in AD.LAYER_ORDER] + fx_back + [head, char, rig]
C.j['layers'] = order
shade_world(C, [LAY[n] for n in AD.LAYER_ORDER], YP, head['ind'])
C.save('aladdin', OUT)

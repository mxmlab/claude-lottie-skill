"""finger: fist -> wind-up -> hand thrusts, middle finger pops up joint by joint
with overshoot (impact burst) -> emphatic shakes + smug 'hehe' -> tongue out wiggle
-> finger folds back -> fist."""
import sys, math
from lot import *
from lot7 import *
from lot7 import _mono_interp

OUT = sys.argv[1]
C = Comp.load('finger')
hand, phones_top, cap, sleeve, skull, body, phones, capb = C.j['layers']
G = list(skull['shapes'])
D = Deformer()

rig = C.null('RIG', lks(p=(256, 500), a=(256, 500), s=(92, 92)))

# ---------------------------------------------------------------- hand: split middle finger into 3 bones
H = list(range(len(hand['shapes'])))
fing = {'tip': [8, 9], 'mid': [10, 11], 'base': [12, 13]}
rest = [i for i in H if i not in sum(fing.values(), [])]
tipL, midL, baseL, palm = split_layer(C, hand, [('tip', fing['tip']), ('mid', fing['mid']), ('base', fing['base']), ('palm', rest)])
K_BASE, K_MID, K_TIP = (394, 298), (394, 226), (395, 152)      # joints (bottom of each segment)
WRIST = (385, 470)

# finger extension: base phalanx always up; mid + tip unfold on springs (overshoot), tip lags
EXT = [(0, 0), (24, 1), (136, 1), (146, 0)]
def seg(delay, f):
    return spring([(t + (delay if v else 0), v) for t, v in EXT], f=f, z=0.4)
em, et = seg(0, 2.6), seg(3, 2.8)
baseL['ks'] = lks(p=K_BASE, a=K_BASE, s=lin(spring([(0, [100, 100]), (24, [96, 108]), (32, [100, 100]), (136, [100, 100])], f=3, z=0.4)))
midL['ks'] = lks(p=K_MID, a=K_MID, s=lin([(t, [100, max(0.5, 100 * v)]) for t, v in em]),
                o=lin([(t, 100 * smoothstep(0.04, 0.14, v)) for t, v in em]))
tipL['ks'] = lks(p=K_TIP, a=K_TIP, s=lin([(t, [100, max(0.5, 100 * v)]) for t, v in et]),
                o=lin([(t, 100 * smoothstep(0.04, 0.14, v)) for t, v in et]))
# gentle whip while shaking: each joint lags the previous
shk = lambda t, lag: math.sin(2 * math.pi * (t - lag) / 16) * smoothstep(40, 52, t) * smoothstep(100, 84, t)
for L, amp, lag in ((baseL, 2, 0), (midL, 4, 2), (tipL, 6, 4)):
    L['ks']['r'] = lin(sampled(lambda t, amp=amp, lag=lag: amp * shk(t, lag)))
baseL['parent'] = palm['ind']; midL['parent'] = baseL['ind']; tipL['parent'] = midL['ind']

# whole hand: wind-up dip, thrust, emphatic shakes
HP = spring([(0, [0, 0]), (14, [4, 14]), (24, [-2, -18]), (36, [0, -10]), (136, [2, -14]), (146, [0, 4]), (156, [0, 0])], f=2.2, z=0.45)
HRr = spring([(0, 0), (14, 6), (24, -7), (36, 0), (136, -3), (146, 3), (156, 0)], f=2.2, z=0.45,
             idle=lambda t: 6 * math.sin(2 * math.pi * t / 16) * smoothstep(40, 52, t) * smoothstep(100, 84, t))
palm['parent'] = rig['ind']
palm['ks'] = lks(p=lin([(t, [WRIST[0] + v[0], WRIST[1] + v[1]]) for t, v in HP]), a=WRIST, r=lin(HRr),
                 s=lin(spring([(0, [100, 100]), (14, [104, 95]), (24, [96, 106]), (34, [100, 100])], f=2.6, z=0.4)))

# ---------------------------------------------------------------- head: smug, leans in on the thrust
NECK = (225, 322)
HR_ = spring([(0, 4), (14, 6), (24, -4), (38, 2), (136, 4), (146, 1), (156, 4)], f=1.8, z=0.5,
              idle=lambda t: 2 * math.sin(2 * math.pi * t / 16 + 1) * smoothstep(40, 52, t) * smoothstep(100, 84, t) + wave(1, 2)(t))
HY_ = spring([(0, 0), (14, 4), (24, -8), (38, -2), (136, 0), (146, 3), (156, 0)], f=1.8, z=0.5)
head = C.null('HEAD', lks(p=lin([(t, [NECK[0], NECK[1] + y]) for t, y in HY_]), a=NECK, r=lin(HR_)), parent=rig['ind'])
for L in (skull, cap, phones, phones_top, capb): L['parent'] = head['ind']
for L in (sleeve, body): L['parent'] = rig['ind']
C.pivot(sleeve, (300, 440), r=lin(spring([(0, 0), (14, 2), (24, -3), (36, 0)], f=2, z=0.5)))

# smug half-lidded eyes (except wide 'ha!' on the thrust)
def lids(c):
    def mk(k):
        def f(p):
            if p[1] >= c[1] + 2: return p
            return (p[0], c[1] + 2 - (c[1] + 2 - p[1]) * (1 - 0.6 * k))
        return f
    return mk
for i, c in ((1, (167, 192)), (2, (167, 192)), (3, (231, 190)), (4, (231, 190))):
    gxf(G[i], c, dp=[(0, [3, 4]), (24, [3, 4]), (28, [0, 0]), (40, [0, 0]), (46, [3, 4]), (96, [3, 4]), (104, [6, 5]), (130, [6, 5]), (138, [3, 4]), (T, [3, 4])])

# tongue: 'blep' from behind the teeth, wiggles
TP = (203, 237)
def tongue_path(k):
    L = 6 + 34 * k; w = 15
    return path([(-w, 0), (w, 0), (w * 0.95, L * 0.7), (0, L), (-w * 0.95, L * 0.7)], smooth=0.55)
tk = [(0, 0), (100, 0), (108, 1.0), (126, 1.0), (134, 0), (T, 0)]
tongue = group([group([shape(path([(0, 6), (0, 22)], closed=False)), stroke((0.78, 0.25, 0.35), 3)]),
                shape(anim([(t, [tongue_path(k)]) + tuple(r) for t, k, *r in tk])),
                fill((0.96, 0.45, 0.55)), stroke((0.62, 0.2, 0.3), 3.5)],
               tr(p=TP, a=(0, 0), o=anim([(0, 0), (100, 0), (104, 100), (130, 100), (134, 0), (T, 0)]), r=lin(sampled(lambda t: 9 * math.sin(2 * math.pi * (t - 104) / 14) * smoothstep(104, 110, t) * smoothstep(130, 122, t)))), nm='tongue')
skull['shapes'].insert(0, tongue)

# ---------------------------------------------------------------- FX
def burst(t0, c, n=8, r0=26, r1=62, w=7, col=(1, 0.85, 0.2)):
    items = []
    for k in range(n):
        a = 2 * math.pi * k / n + 0.3
        p0 = (math.cos(a) * r0, math.sin(a) * r0); p1 = (math.cos(a) * r1, math.sin(a) * r1)
        items.append(group([shape(line_path(p0, p1)), trim(s=anim([(t0 + 4, 0), (t0 + 12, 100)]), e=anim([(t0, 0), (t0 + 6, 100)])),
                            stroke(col, w)]))
    return C.layer('burst', items, lks(p=c), ip=t0, op=t0 + 13, parent=rig['ind'])
fx = [burst(27, (398, 100)), sparkle(C, 29, (440, 90), 18, dur=22), sparkle(C, 32, (350, 120), 12, dur=20)]
def shake_lines(t0, c, ang):
    items = []
    for off in (-14, 0, 14):
        a = math.radians(ang)
        nx, ny = math.cos(a + math.pi / 2) * off, math.sin(a + math.pi / 2) * off
        items.append(group([shape(line_path((nx + math.cos(a) * 18, ny + math.sin(a) * 18), (nx + math.cos(a) * 40, ny + math.sin(a) * 40))),
                            trim(s=anim([(t0 + 3, 0), (t0 + 8, 100)]), e=anim([(t0, 0), (t0 + 4, 100)])), stroke((1, 1, 1), 6)]))
    return C.layer('shake', items, lks(p=c), ip=t0, op=t0 + 9, parent=rig['ind'])
for t in range(46, 92, 16):
    fx.append(shake_lines(t, (340, 110), -160)); fx.append(shake_lines(t + 8, (452, 110), -20))

C.insert(fx, top=True)
C.insert([head, rig], bottom=True)
# ---------------------------------------------------------------- real eyelids (skull-coloured lid + lid line), smug <-> wide
LIDK = spring([(0, 0.55), (18, 0.6), (24, 0.0), (44, 0.0), (56, 0.55), (68, 0.95), (72, 0.55), (100, 0.6), (104, 0.3), (130, 0.3), (138, 0.55)], f=3, z=0.6, step=2)
def lid_groups(c, w, h):
    def lid_path(k):
        top = c[1] - h * 0.5 - 1
        bot = c[1] - h * 0.5 + h * 0.95 * k
        return path([(c[0] - w * 0.6, top), (c[0] + w * 0.6, top), (c[0] + w * 0.58, bot - 2), (c[0], bot + 3), (c[0] - w * 0.58, bot - 2)], smooth=0.35)
    def line_path_(k):
        bot = c[1] - h * 0.5 + h * 0.95 * k
        return path([(c[0] - w * 0.55, bot - 2), (c[0], bot + 3), (c[0] + w * 0.55, bot - 2)], closed=False, smooth=0.9)
    lid = group([shape(anim([(t, [lid_path(k)], 'lin') for t, k in LIDK])), fill((0.97, 0.98, 1))], nm='lid')
    ln = group([shape(anim([(t, [line_path_(k)], 'lin') for t, k in LIDK])), stroke((0.33, 0.39, 0.45), 4)],
               tr(o=anim([(t, 100 * smoothstep(0.03, 0.12, k), 'lin') for t, k in LIDK])), nm='lid line')
    return [ln, lid]
_ei = skull['shapes'].index(G[1])
skull['shapes'][_ei:_ei] = lid_groups((162, 195), 32, 42) + lid_groups((225, 192), 35, 48)

# brows: cocky, jump on the thrust, twitch with the shakes, one up for the tongue
BL = spring([(0, [0, -4]), (20, [0, 0]), (24, [0, -14]), (40, [0, -8]), (100, [0, -12]), (132, [0, -6])], f=2.4, z=0.4,
            idle=lambda t: [0, 3 * math.sin(2 * math.pi * t / 16) * smoothstep(40, 52, t) * smoothstep(100, 84, t)])
BR = spring([(0, [0, -8]), (20, [0, -2]), (24, [0, -16]), (40, [0, -10]), (100, [0, -2]), (132, [0, -8])], f=2.4, z=0.4,
            idle=lambda t: [0, -3 * math.sin(2 * math.pi * t / 16) * smoothstep(40, 52, t) * smoothstep(100, 84, t)])
for i in (10, 11): gxf(G[i], (220, 162), dp=[(t, v, 'lin') for t, v in BR], r=lin(spring([(0, 12), (24, 4), (40, 10), (100, 16), (132, 12)], f=2, z=0.5)))
for i in (12, 13): gxf(G[i], (164, 166), dp=[(t, v, 'lin') for t, v in BL], r=lin(spring([(0, -6), (24, -2), (40, -6), (100, 2), (132, -6)], f=2, z=0.5)))

# fake-3D head
HC, HRD = (205, 190), 90
HRD_ = 90
YP = [(0, (6, -2)), (18, (4, -4)), (26, (-5, 7)), (40, (-2, 3)), (64, (3, 2)), (84, (-3, 3)), (104, (9, -4)), (130, (7, -3)), (146, (6, -2)), (T, (6, -2))]
D.add([G[i] for i in range(0, 19)], YP, turn_fn(HC, HRD_, 'surface', 1.0))
tf = turn_fn(HC, HRD_, 'surface', 1.0)
YPl = [(t, list(v)) for t, v in YP]
for gi, c in ((0, (162, 195)), (1, (162, 195)), (2, (225, 192)), (3, (225, 192))):
    g = skull['shapes'][_ei + gi]
    gtr(g)['p'] = anim([(t, [tf(_mono_interp(YPl, t))(c)[0] - c[0], tf(_mono_interp(YPl, t))(c)[1] - c[1]], 'lin') for t in list(range(0, T, 6)) + [T]])
gtr(tongue)['p'] = anim([(t, list(tf(_mono_interp(YPl, t))(TP)), 'lin') for t in list(range(0, T, 6)) + [T]])
D.add([G[19], G[20]], YP, turn_fn(HC, HRD_, 'surface', 1.0))
D.add([G[21], G[22]], YP, turn_fn(HC, HRD_, 'surface', 1.0))
D.add([g for g in cap['shapes'] if g['ty'] == 'gr'], YP, turn_fn(HC, HRD_, 'surface', 1.0))
D.add([g for g in phones['shapes'] if g['ty'] == 'gr'] + [g for g in phones_top['shapes'] if g['ty'] == 'gr'], YP, turn_fn(HC, HRD_, 'surface', 1.0))
D.add([g for g in capb['shapes'] if g['ty'] == 'gr'], YP, turn_fn(HC, HRD, 'back', 1.0))
D.build()
shade_world(C, (tipL, midL, baseL, palm, phones_top, cap, sleeve, skull, body, phones, capb), YP, head['ind'])
C.save('finger', OUT)

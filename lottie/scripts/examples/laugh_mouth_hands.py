"""HEHEHE v3: one laughing fit, all on springs. Laugh beat every 14f, head leans back
and bounces, mouth opens on each 'ha', happy-arc eyes throughout, hands wave with a
finger ripple + palm turn, cap lags, tears fly on ballistic arcs tail-first."""
import sys, math, random
from lot import *
from lot7 import *

OUT = sys.argv[1]
random.seed(3)
C = Comp.load('HEHEHE')
hand, hand_b, cap, sleeve, skull, body, phones, capb = [C.L(n) for n in (
    'рука', 'задняя рука', 'кепарь', 'ручка', 'скелет', 'тело', 'наушники', 'зад кепки')]
G = list(skull['shapes'])
D = Deformer()

BEAT = 14
beats = list(range(18, 158, BEAT))                    # 'ha' moments
env = spring([(0, 0.25), (14, 1.0), (150, 1.0), (162, 0.25)], f=0.8, z=1.0)   # laugh intensity
E = dict(env)
def e(t): return E[min(E, key=lambda k: abs(k - t))]

rig = C.null('RIG', lks(p=(256, 504), a=(256, 500), s=(90, 90)))
NECK = (220, 330)
# head: slow lean back with intensity + a bounce on each beat
hr_t, hy_t, hs_t = [(0, 0)], [(0, 0)], [(0, [100, 100])]
for t in beats:
    hr_t += [(t, -9), (t + 7, -4)]; hy_t += [(t, -12), (t + 7, 0)]; hs_t += [(t, [97, 104]), (t + 7, [103, 97])]
hr_t.append((160, 0)); hy_t.append((160, 0)); hs_t.append((160, [100, 100]))
HR = spring(hr_t, f=2.6, z=0.45, idle=wave(1.2, 2))
HY = spring(hy_t, f=2.8, z=0.45)
HS = spring(hs_t, f=2.8, z=0.4)
head = C.null('HEAD', lks(p=lin([(t, [NECK[0], NECK[1] + y]) for t, y in HY]), a=NECK, r=lin(HR), s=lin(HS)), parent=rig['ind'])
for L in (skull, phones, cap, capb): L['parent'] = head['ind']
lagR = spring(hr_t, f=1.5, z=0.4, idle=wave(1.2, 2, -0.7))
capR = [(t, (a - b) * 1.3) for (t, a), (_, b) in zip(lagR, HR)]
C.pivot(cap, (250, 130), r=lin(capR))
C.pivot(capb, (160, 140), r=lin([(t, v * 1.8) for t, v in capR]))

# body bounce, a touch behind the head
bs_t = [(0, [100, 100])] + [(t + 3, [99, 102.5]) for t in beats] + [(t + 10, [101, 98]) for t in beats] + [(163, [100, 100])]
BS = spring(sorted(bs_t), f=2.4, z=0.5, idle=lambda t: [wave(0.4, 3)(t), wave(0.8, 3)(t)])
BS = [(t, [100 + (v[0] - 100) * 2.2, 100 + (v[1] - 100) * 2.2]) for t, v in BS]
for L in (body, sleeve):
    L['parent'] = rig['ind']; C.pivot(L, (200, 462), s=lin(BS))

# ---------------------------------------------------------------- hands: palm turn + finger ripple
def hand_rig(L, wrist, palm_c, amp, phase):
    """rigid hand: waves from the wrist and turns in 3D (fingers foreshorten), no paper flutter"""
    L['parent'] = rig['ind']
    rt = [(0, 0)]
    for n, t in enumerate(range(10 + phase, 160, BEAT * 2)):
        rt += [(t, amp), (t + BEAT, -amp * 0.5)]
    rt.append((166, 0))
    R = spring(rt, f=1.6, z=0.55, idle=wave(1.2, 3, phase))
    C.pivot(L, wrist, r=lin(R))
    yk = [(0, (0, 0))]
    for n, t in enumerate(range(10 + phase + 3, 160, BEAT * 2)):
        yk += [(t, (24 * (1 if amp > 0 else -1), 6)), (t + BEAT, (-16 * (1 if amp > 0 else -1), -4))]
    yk = [k for k in yk if k[0] <= 150]
    yk.append((170, (0, 0))); yk.append((T, (0, 0)))
    D.add([g for g in L['shapes'] if g['ty'] == 'gr'], yk, turn_fn(palm_c, 95, 'surface', 0.75))
hand_rig(hand, (268, 468), (400, 360), 9, 0)
hand_rig(hand_b, (330, 440), (405, 330), -7, 7)

# ---------------------------------------------------------------- face: happy arcs all the way, brows up, mouth 'ha'
def eye_fn(c, w, arch):
    def mk(k):
        def f(p):
            dx = (p[0] - c[0]) / w
            return (c[0] + (p[0] - c[0]) * (1 + 0.12 * k),
                    c[1] + (p[1] - c[1]) * (1 - 0.8 * k) - k * arch * (1 - min(1, dx * dx)) + k * 5)
        return f
    return mk
for grp, c, w in (((2, 3), (207, 154), 28), ((14, 15), (303, 161), 24)):
    for i in grp:
        for sh, off in iter_shapes(G[i]):
            P = sh['ks']['k']; sh['ks'] = st(deform(P, eye_fn(c, w, 13)(1), off))
for i in (0, 1, 10, 11, 12, 13): gxf(G[i], (250, 170), s=st([0, 0]))
BR = spring([(0, 0.6), (14, 1), (150, 1), (162, 0.6)], f=1, z=0.8, idle=wave(0.15, 6))
for i, c, sgn in ((4, (228, 101), -1), (5, (228, 101), -1), (6, (302, 108), 1), (7, (302, 108), 1)):
    gxf(G[i], c, dp=[(t, [0, -10 * k], 'lin') for t, k in BR], r=lin([(t, sgn * 10 * k) for t, k in BR]))

Y0 = 240
open_k = [(0, 0.45), (14, 0.74), (152, 0.74), (166, 0.45), (T, 0.45)]
H_t = [(0, 14)]
for t in beats: H_t += [(t, 46), (t + 7, 24)]
H_t.append((160, 14))
Hs = spring(H_t, f=3.2, z=0.5)
Hk = [(t, max(3, h)) for t, h in Hs]
mouth = mouth_rig(G, list(range(16, 27)), 27, Y0, 196, 306, Hk, G[27:30], (250, 250), open_k, D=D)
skull['shapes'][27:27] = mouth

# ---------------------------------------------------------------- tears: ballistic, tail-first
BLUE, BLUE_D = (0.55, 0.85, 1.0), (0.2, 0.55, 0.9)
def tear(t0, p0, v0, life=30, r=11):
    g = 0.55
    pts, rots = [], []
    for t in range(t0, t0 + life + 1, 2):
        u = t - t0
        x, y = p0[0] + v0[0] * u, p0[1] + v0[1] * u + 0.5 * g * u * u
        vx, vy = v0[0], v0[1] + g * u
        pts.append((t, [x, y])); rots.append((t, math.degrees(math.atan2(-vx, vy))))
    return C.layer('tear', [group([shape(path([(-r * 0.3, -r * 0.35), (0, 0)], closed=False)), stroke((1, 1, 1), 2.4)]),
                            group([shape(drop_path(r)), fill(BLUE), stroke(BLUE_D, 2.5)])],
                   lks(p=lin(pts), r=lin(rots), s=anim([(t0, [0, 0]), (t0 + 5, [110, 110], 'out'), (t0 + life, [75, 75])]),
                       o=anim([(t0, 100), (t0 + life - 6, 100), (t0 + life, 0)])),
                   ip=t0, op=t0 + life, parent=rig['ind'])
tears = []
for n, t in enumerate(beats[:-1]):
    tears.append(tear(t + 2, (168, 150), (-3.4 - 0.4 * (n % 2), -5.5)))
    tears.append(tear(t + 4, (338, 156), (3.4 + 0.4 * (n % 2), -5.5)))
tears += wrap_copies(C, tears)

C.insert(tears, top=True)
C.insert([head, rig], bottom=True)
# head tilted back in 3D while laughing (features ride the sphere), slight yaw drift
HC, HR_ = (250, 190), 110
HRD_ = 110
YP = [(0, (-3, 2)), (16, (4, -9)), (80, (-4, -7)), (150, (3, -9)), (166, (-3, 2)), (T, (-3, 2))]
D.add([G[i] for i in list(range(0, 16))], YP, turn_fn(HC, HRD_, 'surface', 1.0))
D.add([G[24], G[25], G[26]], YP, turn_fn(HC, HRD_, 'surface', 1.0))
D.add([g for g in cap['shapes'] if g['ty'] == 'gr'], YP, turn_fn(HC, HRD_, 'surface', 1.0))
D.add([g for g in capb['shapes'] if g['ty'] == 'gr'], YP, turn_fn(HC, HR_, 'back', 1.0))
D.add([g for g in phones['shapes'] if g['ty'] == 'gr'], YP, turn_fn(HC, HRD_, 'surface', 1.0))
D.build()
shade_world(C, (hand, hand_b, cap, sleeve, skull, body, phones, capb), YP, head['ind'])
C.save('HEHEHE', OUT)

"""KLASS: original animation untouched, only the three stars are redone:
staggered spring pop-in, twinkle, slow spin, gentle float, soft glow, white glint core,
tiny satellite sparkles; staggered exit with a last flash."""
import sys, math, copy
import lot
lot.T = 145
from lot import *
T = 145

OUT = sys.argv[1]
C = Comp.load('KLASS')
stars = [L for L in C.j['layers'] if L['nm'].startswith('звезды')]
CENTERS = [(239.3, 111.8), (194.1, 355.9), (400.9, 366.8)]     # group positions in stars 3, 2, 1 order
# find each layer's star centre from its group transform
def centre(L):
    g = L['shapes'][0]
    t = gtr(g); return tuple(t['p']['k'][:2])
IN, OUT_ = 40, 96
fx = []
for n, L in enumerate(stars):
    c = centre(L)
    d = [0, 5, 9][n]
    # appear / disappear on a spring (overshoot), twinkle on top
    sc = spring([(0, 0), (IN + d, 100), (OUT_ + d, 118), (OUT_ + 5 + d, 0)], f=3.2, z=0.38, step=1)
    tw = lambda t, n=n: 1 + 0.16 * math.sin(2 * math.pi * 3 * t / T + n * 2.1)
    S = [(t, [max(0, v) * tw(t), max(0, v) * tw(t)]) for t, v in sc][::2] + [(T, [0, 0])]
    L['ks'] = lks(p=lin(sampled(lambda t, n=n: [c[0] + 4 * math.sin(2 * math.pi * t / T + n), c[1] + 5 * math.sin(2 * math.pi * 2 * t / T + n * 1.7)], 3, 0, T)),
                  a=c, s=lin(sorted(dict(S).items())),
                  r=lin(sampled(lambda t, n=n: 14 * math.sin(2 * math.pi * t / T + n * 1.3), 3, 0, T)))
    L['ip'], L['op'] = 0, T
    # white glint core: a smaller copy of the star on top
    g = L['shapes'][0]
    core = copy.deepcopy(g)
    for it in core['it']:
        if it['ty'] == 'fl': it['c'] = st([1, 1, 0.92, 1])
        if it['ty'] == 'st': it['w'] = st(0.01); it['o'] = st(0)
    ct = gtr(core)
    ct['a'] = st([0, 0]); ct['s'] = lin(sampled(lambda t, n=n: [38 + 12 * math.sin(2 * math.pi * 3 * t / T + n * 2.1 + 0.8)] * 2, 3, 0, T))
    L['shapes'].insert(0, core)
    # soft glow behind, parented to the star so it follows everything
    gl = C.layer('star glow', [group([ellipse((170, 170)), gfill([(0, (1, 0.9, 0.35), 0.75), (0.45, (1, 0.8, 0.2), 0.25), (1, (1, 0.8, 0.2), 0)], (0, 0), 85)])],
                 lks(p=c, s=lin(sampled(lambda t, n=n: [90 + 20 * math.sin(2 * math.pi * 3 * t / T + n * 2.1)] * 2, 3, 0, T)),
                     o=lin(sampled(lambda t, n=n: 70 + 25 * math.sin(2 * math.pi * 3 * t / T + n * 2.1), 3, 0, T))),
                 parent=L['ind'])
    C.insert([gl], below=L)
    # little satellite sparkles popping around each star while it is shown
    for k, (dx, dy, t0) in enumerate(((42, -30, 58), (-38, 26, 78), (30, 40, 96))):
        tt = t0 + d + 4 * n
        if tt + 18 < T:
            fx.append(sparkle(C, tt, (c[0] + dx, c[1] + dy), 9 + 2 * (k % 2), color=(1, 0.95, 0.6), dur=18))

C.insert(fx, top=True)
C.save('KLASS', OUT)

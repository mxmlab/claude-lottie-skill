"""Aladdin, funko-style, designed as vector parts (description -> SVG).
Original folk-tale design: cream turban with ruby + plume, purple vest, red sash, baggy white
trousers, curled slippers, sitting cross-legged on a flying carpet. Big head, solid black eyes.
Each part: (layer, name, points or ('ellipse', cx, cy, w, h), fill, stroke, smooth, closed)."""
import math

INK = (0.2, 0.11, 0.1)
SKIN = (0.89, 0.66, 0.46); SKIN_D = (0.78, 0.52, 0.36)
TURBAN = (0.97, 0.91, 0.78); TURBAN_D = (0.84, 0.74, 0.58)
RUBY = (0.86, 0.1, 0.2); GOLD = (0.98, 0.76, 0.2)
VEST = (0.47, 0.22, 0.62); SASH = (0.86, 0.18, 0.2); PANTS = (0.97, 0.95, 0.9)
SHOE = (0.85, 0.2, 0.22); CARPET = (0.72, 0.1, 0.16); CARPET_B = (0.98, 0.76, 0.2); HAIR = (0.12, 0.08, 0.08)
BLUSH = (0.98, 0.55, 0.55)

def superellipse(cx, cy, a, b, n=3.2, k=40, top_only=False):
    pts = []
    rng = range(k + 1) if top_only else range(k)
    for i in rng:
        t = (math.pi * i / k + math.pi) if top_only else 2 * math.pi * i / k
        c, s = math.cos(t), math.sin(t)
        pts.append((cx + a * math.copysign(abs(c) ** (2 / n), c), cy + b * math.copysign(abs(s) ** (2 / n), s)))
    return pts

HEAD_C = (256, 188)
PARTS = []
def P(layer, name, geom, fill=None, stroke=INK, w=5, smooth=0.0, closed=True, alpha=100):
    PARTS.append(dict(layer=layer, name=name, geom=geom, fill=fill, stroke=stroke, w=w, smooth=smooth, closed=closed, alpha=alpha))

# ---- carpet (flat parallelogram in perspective, drawn as polylines so it can wave)
CARPET_Q = [(58, 392), (452, 380), (478, 432), (34, 448)]
def edge(a, b, n):
    return [(a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n) for i in range(n)]
def carpet_poly(q, n=14):
    return edge(q[0], q[1], n) + edge(q[1], q[2], 3) + edge(q[2], q[3], n) + edge(q[3], q[0], 3)
def inset(q, d):
    cx = sum(p[0] for p in q) / 4; cy = sum(p[1] for p in q) / 4
    return [(cx + (p[0] - cx) * (1 - d), cy + (p[1] - cy) * (1 - d * 1.6)) for p in q]
P('carpet', 'thickness', carpet_poly([(p[0], p[1] + 9) for p in CARPET_Q]), (0.45, 0.05, 0.1))
P('carpet', 'carpet', carpet_poly(CARPET_Q), CARPET)
P('carpet', 'border', carpet_poly(inset(CARPET_Q, 0.08)), None, CARPET_B, 5)
P('carpet', 'pattern', carpet_poly(inset(CARPET_Q, 0.3)), (0.95, 0.66, 0.15), INK, 3)
# tassels on the short edges
for side, (a, b) in (('L', (CARPET_Q[3], CARPET_Q[0])), ('R', (CARPET_Q[1], CARPET_Q[2]))):
    for i in range(4):
        u = (i + 0.5) / 4
        x, y = a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u
        dx = -26 if side == 'L' else 26
        P('tassel' + side, f'tassel{side}{i}', [(x, y), (x + dx * 0.6, y + 2), (x + dx, y + 4)], None, CARPET_B, 4, 0.8, False)

# ---- legs (cross-legged baggy trousers) + slippers
P('legs', 'pants', [(176, 338), (338, 338), (358, 356), (372, 380), (352, 398), (300, 392), (256, 400), (212, 392),
                     (160, 398), (140, 380), (154, 356)], PANTS, INK, 5, 0.45)
P('legs', 'fold', [(256, 352), (250, 372), (256, 392)], None, (0.8, 0.76, 0.7), 3, 0.8, False)
P('legs', 'shoeL', [(150, 384), (126, 386), (104, 378), (98, 366), (110, 372), (128, 372), (158, 372)], SHOE, INK, 4, 0.5)
P('legs', 'shoeR', [(362, 384), (386, 386), (408, 378), (414, 366), (402, 372), (384, 372), (354, 372)], SHOE, INK, 4, 0.5)

# ---- torso: chest, vest panels, sash
P('body', 'chest', [(210, 266), (302, 266), (314, 300), (300, 346), (212, 346), (198, 300)], SKIN, INK, 5, 0.3)
P('body', 'vestL', [(206, 266), (240, 268), (232, 300), (238, 346), (210, 346), (196, 300)], VEST, INK, 5, 0.3)
P('body', 'vestR', [(306, 266), (272, 268), (280, 300), (274, 346), (302, 346), (316, 300)], VEST, INK, 5, 0.3)
P('body', 'sash', [(206, 334), (306, 334), (310, 352), (202, 352)], SASH, INK, 4, 0.2)
P('body', 'sashTail', [(300, 344), (330, 350), (348, 366), (330, 372), (312, 360)], SASH, INK, 4, 0.5)

# ---- arms (tubes = stroke outline + stroke skin), hands
P('armBack', 'armL_o', [(208, 282), (178, 322), (162, 372)], None, INK, 30, 0.8, False)
P('armBack', 'armL', [(208, 282), (178, 322), (162, 372)], None, SKIN, 20, 0.8, False)
P('armBack', 'handL', ('ellipse', 160, 376, 30, 28), SKIN)
P('armFront', 'armR_o', [(304, 282), (346, 262), (378, 222)], None, INK, 30, 0.8, False)
P('armFront', 'armR', [(304, 282), (346, 262), (378, 222)], None, SKIN, 20, 0.8, False)
P('armFront', 'handR', [(366, 216), (372, 190), (384, 184), (392, 196), (398, 186), (408, 190), (404, 214), (390, 232), (372, 232)], SKIN, INK, 5, 0.5)

# ---- head
P('ears', 'earL', ('ellipse', 150, 200, 30, 42), SKIN)
P('ears', 'earR', ('ellipse', 362, 200, 30, 42), SKIN)
P('head', 'face', superellipse(HEAD_C[0], HEAD_C[1], 106, 92, 3.0), SKIN)
P('head', 'hairL', [(152, 150), (166, 176), (172, 160), (184, 182), (190, 150)], HAIR, HAIR, 3, 0.2)
P('head', 'hairR', [(360, 150), (346, 176), (340, 160), (328, 182), (322, 150)], HAIR, HAIR, 3, 0.2)
P('head', 'fringe', [(214, 148), (226, 172), (238, 154), (252, 176), (264, 152), (280, 170), (292, 148)], HAIR, HAIR, 3, 0.2)
P('face', 'blushL', ('ellipse', 188, 238, 34, 18), BLUSH, None, 0, alpha=45)
P('face', 'blushR', ('ellipse', 324, 238, 34, 18), BLUSH, None, 0, alpha=45)
P('face', 'eyeL', ('ellipse', 212, 206, 34, 44), (0.08, 0.05, 0.05), None)
P('face', 'eyeR', ('ellipse', 300, 206, 34, 44), (0.08, 0.05, 0.05), None)
P('face', 'hlL', ('ellipse', 204, 194, 11, 13), (1, 1, 1), None)
P('face', 'hlR', ('ellipse', 292, 194, 11, 13), (1, 1, 1), None)
P('face', 'browL', [(190, 172), (212, 164), (232, 170)], None, HAIR, 8, 0.8, False)
P('face', 'browR', [(280, 170), (300, 164), (322, 172)], None, HAIR, 8, 0.8, False)
P('face', 'nose', ('ellipse', 256, 228, 18, 12), SKIN_D, None)
# mouth: closed smile (same vertex count as the open grin, morphed in the animation)
def _uy(x): t = (x - 256) / 32; return 246 + 9 * max(0.0, 1 - t * t)
_XS = [226, 238, 256, 274, 286]
MOUTH_CLOSED = [(222, 241)] + [(x, _uy(x)) for x in _XS] + [(290, 241)] + [(x, _uy(x) + 3) for x in reversed(_XS)]
MOUTH_OPEN = MOUTH_CLOSED
P('face', 'mouth', MOUTH_CLOSED, (0.35, 0.08, 0.1), INK, 4, 0.4)

# ---- turban
P('turban', 'turban', superellipse(256, 150, 122, 84, 2.4, 40, top_only=True) + [(366, 162), (256, 172), (146, 162)], TURBAN, INK, 5, 0.0)
P('turban', 'wrap1', [(150, 132), (256, 112), (362, 132)], None, TURBAN_D, 4, 0.9, False)
P('turban', 'wrap2', [(170, 104), (256, 86), (342, 104)], None, TURBAN_D, 4, 0.9, False)
P('turban', 'plume', [(262, 118), (276, 80), (300, 50), (312, 46), (300, 70), (282, 110)], (0.3, 0.75, 0.55), INK, 4, 0.5)
P('turban', 'jewel_ring', ('ellipse', 256, 130, 38, 38), GOLD)
P('turban', 'jewel', ('ellipse', 256, 130, 24, 26), RUBY, INK, 3)

LAYER_ORDER = ['armFront', 'turban', 'face', 'head', 'ears', 'body', 'armBack', 'legs', 'tasselR', 'carpet', 'tasselL']   # front -> back


def to_svg(path_out):
    """static SVG of the base pose (back-to-front)"""
    def fmt(c): return 'none' if c is None else '#%02x%02x%02x' % tuple(int(v * 255) for v in c)
    def d_of(pts, closed, smooth):
        if not smooth:
            s = 'M' + ' L'.join(f'{x:.1f},{y:.1f}' for x, y in pts)
            return s + (' Z' if closed else '')
        n = len(pts); s = f'M{pts[0][0]:.1f},{pts[0][1]:.1f}'
        rng = range(n) if closed else range(n - 1)
        for i in rng:
            p0 = pts[(i - 1) % n] if (closed or i > 0) else pts[i]
            p1 = pts[i]; p2 = pts[(i + 1) % n]
            p3 = pts[(i + 2) % n] if (closed or i + 2 < n) else p2
            c1 = (p1[0] + (p2[0] - p0[0]) * smooth / 2, p1[1] + (p2[1] - p0[1]) * smooth / 2)
            c2 = (p2[0] - (p3[0] - p1[0]) * smooth / 2, p2[1] - (p3[1] - p1[1]) * smooth / 2)
            s += f' C{c1[0]:.1f},{c1[1]:.1f} {c2[0]:.1f},{c2[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}'
        return s + (' Z' if closed else '')
    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">']
    for layer in reversed(LAYER_ORDER):
        out.append(f'<g id="{layer}">')
        for p in PARTS:
            if p['layer'] != layer: continue
            fill = fmt(p['fill']); st = fmt(p['stroke']) if p['w'] else 'none'
            common = f'fill="{fill}" fill-opacity="{p["alpha"] / 100}" stroke="{st}" stroke-width="{p["w"]}" stroke-linecap="round" stroke-linejoin="round"'
            g = p['geom']
            if isinstance(g, tuple) and g[0] == 'ellipse':
                out.append(f'<ellipse id="{p["name"]}" cx="{g[1]}" cy="{g[2]}" rx="{g[3] / 2}" ry="{g[4] / 2}" {common}/>')
            else:
                out.append(f'<path id="{p["name"]}" d="{d_of(g, p["closed"], p["smooth"])}" {common}/>')
        out.append('</g>')
    out.append('</svg>')
    open(path_out, 'w', encoding='utf-8').write('\n'.join(out))

if __name__ == '__main__':
    import sys
    to_svg(sys.argv[1])
    print('parts', len(PARTS))

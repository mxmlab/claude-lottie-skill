"""Find visual pops: python popdiff.py sheets/<strip>.png <cell_size> [thr]
Strip = strip.html output (all frames side by side). Prints frame pairs with most changed pixels
(ignoring semi-transparent glow noise) relative to the median; then crop the suspect frames at 512px."""
import sys
import numpy as np
from PIL import Image
im = Image.open(sys.argv[1]).convert('RGBA'); S = int(sys.argv[2]); thr = int(sys.argv[3]) if len(sys.argv) > 3 else 60
n = im.width // S
fr = [np.asarray(im.crop((i * S, 0, (i + 1) * S, S))).astype(float) for i in range(n)]
score = []
for i in range(n):
    a, b = fr[i], fr[(i + 1) % n]
    solid = (a[..., 3] > 200) | (b[..., 3] > 200)
    d = np.abs(b - a)[..., :3].sum(axis=2)
    score.append(int(((d > thr) & solid).sum()))
med = sorted(score)[n // 2]
print('median changed px', med)
for i in sorted(range(n), key=lambda i: -score[i])[:10]:
    print(f'{i}->{(i + 1) % n}: {score[i]} ({score[i] / max(med, 1):.1f}x)')

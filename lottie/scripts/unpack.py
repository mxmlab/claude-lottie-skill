"""Prepare a work dir: python unpack.py <file.tgs|file.json>... -> tgs/<name>.json (+ out/, sheets/ dirs)"""
import gzip, json, os, sys
os.makedirs('tgs', exist_ok=True); os.makedirs('out', exist_ok=True); os.makedirs('sheets', exist_ok=True); os.makedirs('iso', exist_ok=True)
for f in sys.argv[1:]:
    raw = open(f, 'rb').read()
    j = json.loads(gzip.decompress(raw) if raw[:2] == b'\x1f\x8b' else raw)
    n = os.path.splitext(os.path.basename(f))[0]
    json.dump(j, open(f'tgs/{n}.json', 'w', encoding='utf-8'), ensure_ascii=False)
    print(f"{n}: {j['w']}x{j['h']} fr{j['fr']} {j['op']-j['ip']}f layers={len(j['layers'])}")
import shutil
shutil.copy(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sheet.html'), 'sheet.html')
print('sheet.html copied; run srv.py from this dir')

"""Builds the Datalake Studio promo from the segments recorded by record.mjs.

    python3 -I promo/build.py

Works in promo/work/ (segs/ from record.mjs, plus clips/ and text/) and writes
promo/out/datalake-studio-promo-1080p.mp4. Both folders are git-ignored. See promo/README.md.

1. Renders the captions and the title/end cards to PNG with headless Chrome (cards.mjs).
2. Cuts each clip of the edit list out of its segment, sped up where it says so.
3. Concatenates the clips and overlays the captions, which fade and slide in. No audio.
"""
import json
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
T = os.path.join(HERE, 'work')
OUT = os.path.join(HERE, 'out', 'datalake-studio-promo-1080p.mp4')
FPS = 30
CARD_SECONDS = {'title': 3.8, 'end': 5.0}

TITLE = {'title': 'Datalake Studio', 'sub': 'From raw data to ready-to-use APIs',
         'kicker': 'Open source  ·  Runs on your machine  ·  Powered by DuckDB'}
END = {'title': 'Datalake Studio', 'sub': 'Load  ·  Query  ·  Visualise  ·  Publish',
       'url': 'github.com/javitorres/datalakeStudio', 'kicker': 'Open source  ·  GPLv3  ·  Vue + FastAPI + DuckDB'}

# ── Edit list ─────────────────────────────────────────────────────────────────────────────
# (segment, in, out, speed, caption). Times are segment seconds; the caption shows over that clip.
# A caption is (kicker, title, sub). 'title' and 'end' are the cards above, not segments.
CLIPS = [
    ('title', 0, 0, 1, None),
    ('overview', 0.5, 4.0, 1, ('Overview', 'One workspace for all your data', None)),
    ('load', 0.8, 12.2, 1.35, ('Load', '3M NYC taxi trips, straight from a URL',
                               'Parquet, CSV, JSON · from a URL, S3, PostgreSQL or your disk')),
    ('load', 13.8, 22.3, 1.35, ('Load', 'Shapefiles too: the taxi zone map',
                                'Upload a zipped shapefile and query its geometry')),
    ('sql', 1.0, 13.2, 2.4, ('SQL', 'Join every trip with its pickup zone',
                             'Full DuckDB SQL, spatial functions included')),
    ('sql', 13.2, 19.6, 1, ('Fast', 'Millions of rows, answers in seconds',
                            'DuckDB runs inside the app: no cluster to manage')),
    ('sql', 19.6, 27.3, 1.4, ('SQL', 'Save any result as a new table', None)),
    ('explore', 1.0, 12.6, 1.25, ('Explore', 'Sample rows and profile every column', None)),
    ('charts', 2.0, 10.0, 1.5, ('Visualise', 'Instant charts for the fields you pick', None)),
    ('charts', 10.0, 21.5, 1, ('Cross-filter', 'Drag one chart, the others follow',
                               'Short trips? Almost all of them start in Manhattan')),
    ('map', 0.5, 12.5, 1.8, ('Map', 'Aggregate pickups into H3 hexagons', None)),
    ('map', 12.5, 23.3, 1, ('Map', 'Every pickup in New York, in 3D',
                            'Height and colour show the number of trips')),
    ('api', 0.8, 20.5, 1.7, ('Publish', 'Turn a saved query into a REST API',
                             '{borough} becomes a parameter of the endpoint')),
    ('api', 20.5, 24.0, 1, None),
    ('api', 24.1, 27.4, 1, ('Live', 'Any app can query it now', 'JSON straight from DuckDB')),
    ('end', 0, 0, 1, None),
]


def length(c):
    seg, tin, tout, speed, _ = c
    return CARD_SECONDS[seg] if seg in CARD_SECONDS else (tout - tin) / speed


starts = []
acc = 0.0
for c in CLIPS:
    starts.append(acc)
    acc += length(c)
TOTAL = acc


def run(cmd):
    subprocess.run(cmd, check=True)


# ── 1. Captions and cards ─────────────────────────────────────────────────────────────────
os.makedirs(f'{T}/text', exist_ok=True)
os.makedirs(f'{T}/clips', exist_ok=True)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
cards = [{'name': 'title', 'kind': 'title', **TITLE}, {'name': 'end', 'kind': 'end', **END}]
for i, c in enumerate(CLIPS):
    if c[4]:
        kicker, title, sub = c[4]
        cards.append({'name': f'cap{i:02d}', 'kind': 'caption', 'kicker': kicker, 'title': title, 'sub': sub})
with open(f'{T}/text/cards.json', 'w') as f:
    json.dump(cards, f, indent=1)
run(['node', os.path.join(HERE, 'cards.mjs'), f'{T}/text/cards.json', f'{T}/text'])

# ── 2. Clips ──────────────────────────────────────────────────────────────────────────────
ENC = ['-c:v', 'libx264', '-preset', 'medium', '-crf', '14', '-pix_fmt', 'yuv420p', '-r', str(FPS)]
for i, c in enumerate(CLIPS):
    seg, tin, tout, speed, _ = c
    out = f'{T}/clips/{i:02d}.mp4'
    if seg in CARD_SECONDS:
        run(['ffmpeg', '-loglevel', 'error', '-y', '-loop', '1', '-framerate', str(FPS), '-i', f'{T}/text/{seg}.png',
             '-t', f'{length(c):.4f}', '-vf', 'format=yuv420p,setsar=1', *ENC, out])
    else:
        # -t before -i: it limits the input, so a sped-up clip lasts (out - in) / speed
        run(['ffmpeg', '-loglevel', 'error', '-y', '-ss', f'{tin:.4f}', '-t', f'{tout - tin:.4f}',
             '-i', f'{T}/segs/{seg}.mp4', '-an',
             '-vf', f'setpts=(PTS-STARTPTS)/{speed},fps={FPS},scale=1920:1080:flags=lanczos,setsar=1', *ENC, out])
with open(f'{T}/clips/list.txt', 'w') as f:
    for i in range(len(CLIPS)):
        f.write(f"file '{T}/clips/{i:02d}.mp4'\n")

# ── 3. Captions over the edit, final encode ───────────────────────────────────────────────
inputs = []
graph = []
last = '0:v'
for ci, c in enumerate(CLIPS):
    if not c[4]:
        continue
    a = starts[ci] + 0.35
    b = starts[ci] + min(length(c) - 0.3, 5.5)
    n = inputs.count('-i') + 1   # input 0 is the edit
    inputs += ['-loop', '1', '-framerate', str(FPS), '-t', f'{TOTAL:.3f}', '-i', f'{T}/text/cap{ci:02d}.png']
    graph.append(f'[{n}:v]format=rgba,fade=t=in:st={a:.3f}:d=0.35:alpha=1,'
                 f'fade=t=out:st={b - 0.35:.3f}:d=0.35:alpha=1[c{ci}]')
    # Slides up 26 px while it fades in
    y = f"if(lt(t,{a:.3f}),26,if(lt(t,{a + 0.45:.3f}),26*pow(1-(t-{a:.3f})/0.45,2),0))"
    graph.append(f"[{last}][c{ci}]overlay=x=0:y='{y}':eval=frame:enable='between(t,{a:.3f},{b:.3f})'[v{ci}]")
    last = f'v{ci}'
graph.append(f'[{last}]fade=t=in:st=0:d=0.6,fade=t=out:st={TOTAL - 0.9:.3f}:d=0.9[vout]')
with open(f'{T}/text/graph.txt', 'w') as f:
    f.write(';\n'.join(graph))
run(['ffmpeg', '-loglevel', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', f'{T}/clips/list.txt', *inputs,
     '-filter_complex_script', f'{T}/text/graph.txt', '-map', '[vout]',
     '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', '-profile:v', 'high', '-pix_fmt', 'yuv420p',
     '-r', str(FPS), '-movflags', '+faststart', OUT])
print(f'total {TOTAL:.2f} s -> {OUT}')

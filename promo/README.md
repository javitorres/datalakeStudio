# Promo video

A ~1:45 product tour with English captions and no audio, recorded from the real app using
NYC yellow taxi trips (January 2024, ~3M rows) and the TLC taxi zone shapefile.

Requirements: Node 22+, Python 3, `google-chrome` and `ffmpeg`.

1. Start the backend on `:8000` with a **throwaway data folder**: the segments drop and
   create tables, endpoints and saved queries. Maps need a Mapbox token in `secrets.yml`.
2. Start the frontend on `:8080` (`cd client && npm run dev -- --port 8080`).
3. Record the segments. Run them all, or only the ones listed:

   ```bash
   node promo/record.mjs                 # overview load sql explore charts map api
   node promo/record.mjs map api
   ```

   Each segment is written to `promo/work/segs/<name>.mp4`. Headless Chrome is driven over
   CDP (`cdp.mjs`), with a scripted cursor, at 1280×720 CSS pixels and scale 1.5 (1080p).
   `promo/sheet.sh <segment> [step]` makes a contact sheet to choose the cut points.
4. Build the video:

   ```bash
   python3 -I promo/build.py
   ```

   The edit list (`CLIPS` in `build.py`) sets each clip's in and out points, its speed and its
   caption. `cards.mjs` renders the captions and the title and end cards with Chrome.
   The output is `promo/out/datalake-studio-promo-1080p.mp4`.

`promo/work/` and `promo/out/` are git-ignored.

"""Chapter cards: a regional route map per day, drawn in an engraved-map style.

Every ornament is tied to real data rather than invented geography:

  - stop symbols come from the reverse-geocode classification, so Srebrna Góra
    gets a bastion, the -Zdrój towns get a spa fountain, Ostrów Tumski gets
    cathedral spires and Karłów gets a flat-topped table mountain, which is the
    actual signature of the Góry Stołowe
  - the hill hachures sit at photo positions above 600 m, so the relief shown is
    relief that was actually walked
  - the route is the photo sequence

Only the compass, frame and cartouche rules are purely decorative. Two maps as
before: the main one scaled to the day, an inset for the whole trip.

Usage: chapter_cards.py <outdir> [--day N] [--summary]
"""
import argparse
import json
import math
import os
from collections import defaultdict

from PIL import Image, ImageDraw, ImageFont

BG = (16, 18, 14)
DIM = (58, 63, 51)
ACCENT = (214, 202, 160)
TEXT = (236, 232, 218)
MUTED = (126, 130, 112)
FAINT = (30, 33, 26)
RULE = (74, 79, 64)

FONT = '/System/Library/Fonts/Supplemental/Futura.ttc'
DAY_OF = {'2026-08-02': 1, '2026-08-03': 2, '2026-08-04': 3,
          '2026-08-05': 4, '2026-08-06': 5}

STR = {
    'en': {
        'day': 'DAY', 'trip': 'THE TRIP', 'span': '2 – 6 AUGUST 2026',
        'sub': 'five days, eleven stops', 'whole': 'the whole trip',
        'photos': 'photos', 'ph_loc': 'photos with a location',
        'p2p': 'km*  photo to photo', 'alt': 'm  altitude',
        'arc': 'Wrocław to the Table Mountains',
        'foot': '* straight line photo to photo, not road distance           '
                'place names © OpenStreetMap contributors',
        'dates': {1: '2 August', 2: '3 August', 3: '4 August',
                  4: '5 August', 5: '6 August'},
        'quip': {1: 'where it starts',
                 2: 'six photos, sixty-six kilometres',
                 3: 'three towns before dark',
                 4: 'up at 07:44, four stops',
                 5: 'a photo every 82 metres'},
    },
    'pl': {
        'day': 'DZIEŃ', 'trip': 'WYPRAWA', 'span': '2 – 6 SIERPNIA 2026',
        'sub': 'pięć dni, jedenaście przystanków', 'whole': 'cała trasa',
        'photos': 'zdjęć', 'ph_loc': 'zdjęć z lokalizacją',
        'p2p': 'km*  od zdjęcia do zdjęcia', 'alt': 'm  wysokości',
        'arc': 'z Wrocławia w Góry Stołowe',
        'foot': '* linia prosta od zdjęcia do zdjęcia, nie odległość drogowa           '
                'nazwy miejsc © OpenStreetMap contributors',
        'dates': {1: '2 sierpnia', 2: '3 sierpnia', 3: '4 sierpnia',
                  4: '5 sierpnia', 5: '6 sierpnia'},
        'quip': {1: 'tu się zaczyna',
                 2: 'sześć zdjęć, sześćdziesiąt sześć kilometrów',
                 3: 'trzy miasta przed zmrokiem',
                 4: 'pobudka 7:44, cztery przystanki',
                 5: 'zdjęcie co 82 metry'},
    },
}

# One line per place, only where there is something genuinely worth reading.
# Supplied from general knowledge, not from the geocoder - check before delivery.
NOTES = {
    'Wrocław': {'en': 'Ostrów Tumski, the oldest part of the city',
                'pl': 'Ostrów Tumski, najstarsza część miasta'},
    'Srebrna Góra': {'en': 'one of the largest mountain fortresses in Europe',
                     'pl': 'jedna z największych twierdz górskich w Europie'},
    'Kłodzko': {'en': 'the fortress above the town',
                'pl': 'twierdza nad miastem'},
    'Bystrzyca Kłodzka': {'en': 'home of the matchbox museum',
                          'pl': 'muzeum filumenistyczne'},
    'Duszniki-Zdrój': {'en': 'Chopin played here in 1826',
                       'pl': 'Chopin grał tu w 1826'},
    'Kudowa-Zdrój': {'en': 'the Skull Chapel at Czermna',
                     'pl': 'Kaplica Czaszek w Czermnej'},
    'Karłów': {'en': 'the way up Szczeliniec Wielki, 919 m',
               'pl': 'brama na Szczeliniec Wielki, 919 m'},
}
FORTRESS = {'Srebrna Góra', 'Nowy Świat', 'Kłodzko'}
CATHEDRAL = {'Ostrów Tumski'}
TABLE_MTN = {'Karłów'}
MIN_SPAN_KM = 2.5
HILL_ABOVE = 600.0


def font(px, idx=0):
    try:
        return ImageFont.truetype(FONT, px, index=idx)
    except Exception:
        return ImageFont.load_default()


def hav(a, b):
    R = 6371.0
    p1, p2 = math.radians(a['lat']), math.radians(b['lat'])
    dp = p2 - p1
    dl = math.radians(b['lon'] - a['lon'])
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


# --- symbols, each drawn centred on (x, y) within a box of side s -----------

def sym_table_mountain(dr, x, y, s, c):
    h = s * 0.62
    dr.polygon([(x - s * 0.72, y + h * 0.5), (x - s * 0.42, y - h * 0.5),
                (x + s * 0.42, y - h * 0.5), (x + s * 0.72, y + h * 0.5)],
               outline=c, width=3)
    for f in (0.05, 0.28):                          # strata: the Góry Stołowe giveaway
        yy = y - h * 0.5 + h * (0.35 + f)
        dr.line([(x - s * (0.5 + f), yy), (x + s * (0.5 + f), yy)], fill=c, width=2)


def sym_fortress(dr, x, y, s, c):
    pts = []
    for i in range(10):
        ang = math.radians(-90 + i * 36)
        r = s * (0.72 if i % 2 == 0 else 0.34)
        pts.append((x + r * math.cos(ang), y + r * math.sin(ang)))
    dr.polygon(pts, outline=c, width=3)


def sym_spa(dr, x, y, s, c):
    dr.arc([x - s * 0.6, y + s * 0.05, x + s * 0.6, y + s * 0.8], 0, 180, fill=c, width=3)
    dr.line([(x, y + s * 0.1), (x, y - s * 0.3)], fill=c, width=3)
    dr.arc([x - s * 0.55, y - s * 0.6, x + s * 0.05, y + s * 0.1], 250, 350, fill=c, width=2)
    dr.arc([x - s * 0.05, y - s * 0.6, x + s * 0.55, y + s * 0.1], 190, 290, fill=c, width=2)


def sym_cathedral(dr, x, y, s, c):
    for d in (-1, 1):
        bx = x + d * s * 0.34
        dr.polygon([(bx - s * 0.17, y + s * 0.6), (bx - s * 0.17, y - s * 0.22),
                    (bx, y - s * 0.6), (bx + s * 0.17, y - s * 0.22),
                    (bx + s * 0.17, y + s * 0.6)], outline=c, width=3)
        dr.line([(bx, y - s * 0.6), (bx, y - s * 0.84)], fill=c, width=2)
        dr.line([(bx - s * 0.1, y - s * 0.75), (bx + s * 0.1, y - s * 0.75)], fill=c, width=2)


def sym_city(dr, x, y, s, c):
    for d, h in ((-0.56, 0.45), (0.0, 0.78), (0.56, 0.55)):
        dr.rectangle([x + d * s - s * 0.2, y + s * 0.6 - s * h,
                      x + d * s + s * 0.2, y + s * 0.6], outline=c, width=3)


def sym_town(dr, x, y, s, c):
    dr.rectangle([x - s * 0.42, y - s * 0.05, x + s * 0.42, y + s * 0.6], outline=c, width=3)
    dr.polygon([(x - s * 0.56, y - s * 0.05), (x, y - s * 0.6), (x + s * 0.56, y - s * 0.05)],
               outline=c, width=3)


def sym_village(dr, x, y, s, c):
    dr.rectangle([x - s * 0.56, y + s * 0.12, x - s * 0.06, y + s * 0.6], outline=c, width=3)
    dr.polygon([(x - s * 0.68, y + s * 0.12), (x - s * 0.31, y - s * 0.3),
                (x + s * 0.06, y + s * 0.12)], outline=c, width=3)
    dr.line([(x + s * 0.42, y + s * 0.6), (x + s * 0.42, y + s * 0.12)], fill=c, width=3)
    dr.polygon([(x + s * 0.18, y + s * 0.16), (x + s * 0.42, y - s * 0.4),
                (x + s * 0.66, y + s * 0.16)], outline=c, width=3)


def symbol_for(name, detail, alt):
    if name in TABLE_MTN or alt >= 900:
        return sym_table_mountain
    if name in CATHEDRAL or detail in CATHEDRAL:
        return sym_cathedral
    if name in FORTRESS:
        return sym_fortress
    if 'Zdrój' in name or detail == 'Zieleniec' or 'Zdrój' in (detail or ''):
        return sym_spa
    if name.startswith('Wroc') or detail in ('Nadodrze', 'Stare Miasto'):
        return sym_city
    return sym_town


def hachure(dr, x, y, s, c):
    dr.line([(x - s, y + s * 0.5), (x, y - s * 0.5), (x + s, y + s * 0.5)], fill=c, width=2)
    for d in (-0.4, 0.0, 0.4):
        dr.line([(x + d * s, y - s * 0.5 + abs(d) * s), (x + d * s, y + s * 0.4)],
                fill=c, width=1)


def compass(dr, x, y, r, c, lab):
    for i in range(8):
        ang = math.radians(-90 + i * 45)
        rr = r if i % 2 == 0 else r * 0.45
        a1, a2 = ang - math.radians(22), ang + math.radians(22)
        dr.polygon([(x, y),
                    (x + rr * 0.42 * math.cos(a1), y + rr * 0.42 * math.sin(a1)),
                    (x + rr * math.cos(ang), y + rr * math.sin(ang)),
                    (x + rr * 0.42 * math.cos(a2), y + rr * 0.42 * math.sin(a2))],
                   outline=c, width=2)
    dr.ellipse([x - r * 0.1, y - r * 0.1, x + r * 0.1, y + r * 0.1], outline=c, width=2)
    dr.text((x - 11, y - r - 48), 'N', font=lab, fill=c)


def frame(dr, W, H):
    for inset, w in ((34, 3), (48, 1)):
        dr.rectangle([inset, inset, W - inset, H - inset], outline=RULE, width=w)
    for cx, cy in ((48, 48), (W - 48, 48), (48, H - 48), (W - 48, H - 48)):
        dr.polygon([(cx, cy - 13), (cx + 13, cy), (cx, cy + 13), (cx - 13, cy)],
                   outline=RULE, width=2)


def scale_bar(dr, x, y, px, km, lab, c):
    seg = px / 4
    for i in range(4):
        dr.rectangle([x + i * seg, y - 8, x + (i + 1) * seg, y + 8],
                     outline=c, width=2, fill=c if i % 2 else None)
    dr.text((x + px + 18, y - 18), f'{km} km', font=lab, fill=c)


def projector(pts, box, k, pad=0.86, min_span_deg=0.0):
    x0, y0, x1, y1 = box
    xs = [p['lon'] * k for p in pts]
    ys = [-p['lat'] for p in pts]
    spx = max(max(xs) - min(xs), min_span_deg * k)
    spy = max(max(ys) - min(ys), min_span_deg)
    s = min((x1 - x0) / max(spx, 1e-9), (y1 - y0) / max(spy, 1e-9)) * pad
    cx, cy = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
    return (lambda p: ((x0 + x1) / 2 + (p['lon'] * k - cx) * s,
                       (y0 + y1) / 2 + (-p['lat'] - cy) * s)), s


def nice_km(span):
    for v in (1, 2, 5, 10, 20, 50, 100):
        if v >= span / 4:
            return v
    return 100


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('outdir')
    ap.add_argument('--day', type=int, default=0)
    ap.add_argument('--summary', action='store_true')
    ap.add_argument('--lang', choices=('en', 'pl'), default='en')
    ap.add_argument('--width', type=int, default=3840)
    ap.add_argument('--height', type=int, default=1600)
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    T = STR[a.lang]

    pts = json.load(open('tmp/photo_gps.json'))
    stops = {DAY_OF[k]: v for k, v in json.load(open('tmp/trip_stops.json')).items()
             if k in DAY_OF}
    byday = defaultdict(list)
    for p in pts:
        d = DAY_OF.get(p['dt'][:10].replace(':', '-'))
        if d:
            byday[d].append(p)
    for d in byday:
        byday[d].sort(key=lambda x: x['dt'])
    allpts = [p for v in byday.values() for p in v]
    k = math.cos(math.radians(sum(p['lat'] for p in allpts) / len(allpts)))

    W, H = a.width, a.height
    main_box = (int(W * 0.40), int(H * 0.11), W - 170, H - 200)
    ins_box = (int(W * 0.055), int(H * 0.625), int(W * 0.055) + 290, int(H * 0.625) + 390)

    jobs = ['S'] if a.summary else ([a.day] if a.day else sorted(byday))
    for d in jobs:
        summary = d == 'S'
        day = allpts if summary else byday[d]
        im = Image.new('RGB', (W, H), BG)
        dr = ImageDraw.Draw(im)
        frame(dr, W, H)

        for gy in range(main_box[1], main_box[3], 96):
            dr.line([(main_box[0], gy), (main_box[2], gy)], fill=FAINT, width=1)
        for gx in range(main_box[0], main_box[2], 96):
            dr.line([(gx, main_box[1]), (gx, main_box[3])], fill=FAINT, width=1)

        proj, s = projector(day, main_box, k, min_span_deg=MIN_SPAN_KM / 111.0)

        for p in day:                                # relief that was actually walked
            if p['alt'] >= HILL_ABOVE:
                hx, hy = proj(p)
                hachure(dr, hx, hy + 30, 13, (50, 55, 44))

        if summary:
            for od in sorted(byday):
                pl = [proj(p) for p in byday[od]]
                if len(pl) > 1:
                    dr.line(pl, fill=ACCENT, width=4)
                for x, y in pl:
                    dr.ellipse([x - 5, y - 5, x + 5, y + 5], fill=ACCENT)
        else:
            route = [proj(p) for p in day]
            if len(route) > 1:
                dr.line(route, fill=ACCENT, width=5)
            for x, y in route:
                dr.ellipse([x - 7, y - 7, x + 7, y + 7], fill=ACCENT)

        span_km = (main_box[2] - main_box[0]) * 111.0 / s
        bar = nice_km(span_km)
        bar_px = bar / 111.0 * s
        bar_xy = (main_box[0] + 24, main_box[3] - 30)

        # the compass and scale bar are furniture: reserve them before any label
        placed = [(bar_xy[0] - 10, bar_xy[1] - 26, bar_xy[0] + bar_px + 170, bar_xy[1] + 26),
                  (main_box[2] - 190, main_box[1] + 40, main_box[2] - 10, main_box[1] + 210)]
        stoplist = ([st for v in stops.values() for st in v] if summary else stops.get(d, []))
        if summary:                                  # one label per place, not per visit
            seen, uniq = set(), []
            for st in stoplist:
                if st['name'] not in seen:
                    seen.add(st['name'])
                    uniq.append(st)
            # place the notable stops first so a crowded cluster keeps the ones
            # worth reading - the destination should not lose to a waypoint
            rank = {sym_table_mountain: 0, sym_fortress: 1, sym_cathedral: 2,
                    sym_city: 3, sym_spa: 4, sym_town: 5, sym_village: 6}
            stoplist = sorted(uniq, key=lambda st: rank.get(
                symbol_for(st['name'], st['detail'], st['alt']), 9))
        for st in stoplist:
            x, y = proj(st)
            symbol_for(st['name'], st['detail'], st['alt'])(dr, x, y - 40, 34, TEXT)
            dr.ellipse([x - 5, y - 5, x + 5, y + 5], fill=TEXT)
            sub = st['detail'] or f"{st['alt']:.0f} m"
            note = (NOTES.get(st['name']) or {}).get(a.lang, '')
            lines = [st['name']] + ([f"{st['time']}   {sub}"] if not summary else [])
            if note:
                lines.append(note)
            w = max(len(t) for t in lines) * 20
            h = 44 + 42 * (len(lines) - 1)
            spot = None
            for ox, oy in ((30, 4), (30, -h - 20), (-w - 30, 4), (-w - 30, -h - 20),
                           (30, 76), (-w - 30, 76)):
                box = (x + ox, y + oy, x + ox + w, y + oy + h)
                inside = (box[0] > main_box[0] + 8 and box[2] < main_box[2] - 8
                          and box[1] > main_box[1] + 8 and box[3] < main_box[3] - 8)
                if inside and not any(box[0] < q[2] and q[0] < box[2]
                                      and box[1] < q[3] and q[1] < box[3] for q in placed):
                    spot = box
                    break
            if spot is None:                          # a crowded cluster: symbol only
                continue
            placed.append(spot)
            dr.text((spot[0], spot[1]), st['name'], font=font(44), fill=TEXT)
            yy = spot[1] + 46
            if not summary:
                dr.text((spot[0], yy), f"{st['time']}   {sub}", font=font(30), fill=MUTED)
                yy += 42
            if note:
                dr.text((spot[0], yy), note, font=font(29, 1), fill=ACCENT)

        compass(dr, main_box[2] - 100, main_box[1] + 128, 58, RULE, font(30))

        if not summary:
            iproj, _ = projector(allpts, ins_box, k, pad=0.92)
            dr.rectangle(ins_box, outline=(38, 42, 33), width=2)
            for od in sorted(byday):
                pl = [iproj(p) for p in byday[od]]
                col = ACCENT if od == d else DIM
                if len(pl) > 1:
                    dr.line(pl, fill=col, width=4 if od == d else 2)
                for x, y in pl:
                    r = 4 if od == d else 2
                    dr.ellipse([x - r, y - r, x + r, y + r], fill=col)
            dr.text((ins_box[0], ins_box[3] + 12), T['whole'], font=font(28), fill=MUTED)

        tx = int(W * 0.055)
        alts = [p['alt'] for p in day if p['alt']]
        if summary:
            km = sum(sum(hav(v[i], v[i + 1]) for i in range(len(v) - 1))
                     for v in byday.values())
            dr.text((tx, int(H * 0.125)), T['trip'], font=font(168), fill=TEXT)
            dr.text((tx + 8, int(H * 0.335)), T['span'], font=font(56), fill=ACCENT)
            dr.text((tx + 8, int(H * 0.425)), T['sub'], font=font(46, 1), fill=MUTED)
            for i, row in enumerate([f"{km:.0f} {T['p2p']}",
                                     f"{min(alts):.0f} – {max(alts):.0f} {T['alt']}",
                                     f"{len(allpts)} {T['ph_loc']}",
                                     T['arc']]):
                dr.text((tx + 8, int(H * 0.525) + i * 60), row, font=font(40),
                        fill=TEXT if i == 0 else MUTED)
        else:
            km = sum(hav(day[i], day[i + 1]) for i in range(len(day) - 1))
            dr.text((tx, int(H * 0.125)), f"{T['day']} {d}", font=font(200), fill=TEXT)
            dr.text((tx + 8, int(H * 0.35)), T['dates'][d].upper(), font=font(58), fill=ACCENT)
            dr.text((tx + 8, int(H * 0.437)), T['quip'][d], font=font(46, 1), fill=MUTED)
            dr.text((tx + 8, int(H * 0.522)),
                    f"{len(day)} {T['photos']}    {km:.0f} km    "
                    f"{min(alts):.0f}–{max(alts):.0f} m",
                    font=font(40), fill=TEXT)
            dr.text((tx + 8, int(H * 0.572)),
                    f"{day[0]['dt'][11:16]} – {day[-1]['dt'][11:16]}",
                    font=font(36), fill=MUTED)

        scale_bar(dr, bar_xy[0], bar_xy[1], bar_px, bar, font(30), MUTED)
        dr.text((int(W * 0.40), H - 96), T['foot'], font=font(26), fill=(64, 68, 57))

        out = os.path.join(a.outdir, f'CHAPTER_{"SUMMARY" if summary else "D" + str(d)}.png')
        im.save(out)
        print(f'  {"summary" if summary else "day " + str(d):<9} {len(day):>3} photos  '
              f'{len(stoplist)} symbols  scale {bar} km -> {out}')


if __name__ == '__main__':
    main()

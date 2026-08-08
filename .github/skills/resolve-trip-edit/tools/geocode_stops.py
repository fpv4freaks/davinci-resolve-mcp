"""Reverse-geocode the trip's distinct stops into place names.

Stops are clustered from the photo GPS first so this makes ~11 requests rather
than 87. Nominatim's usage policy requires an identifying User-Agent and at most
one request per second, both of which are honoured here, and the result is
cached to disk so a rerun costs nothing.
"""
import json
import math
import os
import time
import urllib.parse
import urllib.request
from collections import defaultdict

PTS = 'tmp/photo_gps.json'
OUT = 'tmp/trip_places.json'
MIN_KM = 1.5
UA = 'wro-trip-film/1.0 (personal travel film; contact: local user)'


def hav(a, b):
    R = 6371.0
    p1, p2 = math.radians(a['lat']), math.radians(b['lat'])
    dp = p2 - p1
    dl = math.radians(b['lon'] - a['lon'])
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


def lookup(lat, lon):
    q = urllib.parse.urlencode({'lat': f'{lat:.5f}', 'lon': f'{lon:.5f}',
                                'format': 'jsonv2', 'zoom': '14',
                                'accept-language': 'pl,en'})
    req = urllib.request.Request(f'https://nominatim.openstreetmap.org/reverse?{q}',
                                 headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode())


def main():
    pts = json.load(open(PTS))
    byday = defaultdict(list)
    for p in pts:
        byday[p['dt'][:10].replace(':', '-')].append(p)

    cache = json.load(open(OUT)) if os.path.exists(OUT) else {}
    result = {}
    for d in sorted(byday):
        v = sorted(byday[d], key=lambda x: x['dt'])
        stops = [v[0]]
        for p in v[1:]:
            if all(hav(p, s) > MIN_KM for s in stops):
                stops.append(p)
        named = []
        for s in stops:
            key = f"{s['lat']:.4f},{s['lon']:.4f}"
            if key not in cache:
                try:
                    cache[key] = lookup(s['lat'], s['lon'])
                except Exception as e:
                    print(f'  {key}: lookup failed {e}')
                    cache[key] = {}
                time.sleep(1.1)                      # Nominatim: 1 request/second
            a = (cache[key].get('address') or {})
            name = (a.get('village') or a.get('town') or a.get('city')
                    or a.get('municipality') or a.get('county') or '?')
            detail = (a.get('tourism') or a.get('natural') or a.get('peak')
                      or a.get('protected_area') or a.get('suburb') or '')
            named.append({'lat': s['lat'], 'lon': s['lon'], 'time': s['dt'][11:16],
                          'alt': s['alt'], 'name': name, 'detail': detail,
                          'county': a.get('county', ''), 'state': a.get('state', '')})
            print(f"  {d}  {s['lat']:.4f},{s['lon']:.4f}  {s['dt'][11:16]}  "
                  f"{name}{' / ' + detail if detail else ''}")
        result[d] = named

    json.dump(cache, open(OUT, 'w'), indent=1, ensure_ascii=False)
    json.dump(result, open('tmp/trip_stops.json', 'w'), indent=1, ensure_ascii=False)
    print(f'\n{sum(len(v) for v in result.values())} stops named -> tmp/trip_stops.json')
    print('place names (c) OpenStreetMap contributors, ODbL')


if __name__ == '__main__':
    main()

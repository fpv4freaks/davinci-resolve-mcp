"""Extract per-photo GPS from EXIF, and report whether video telemetry is usable.

Photo EXIF is the dependable source. GoPro files carry a `gpmd` GPMF stream that
looks like a continuous track until it is read - on this shoot every sample had
`GPSF` (fix quality) 0 and coordinates of exactly 0,0, meaning the camera never
acquired a lock. Pass video files as well and this says so before anything is
designed around a track that does not exist.

Note `-map 0:d:0` selects the 4-byte `tmcd` timecode track, not the telemetry, so
the gpmd stream is located by codec tag and mapped by absolute index.

Usage: photo_gps.py <out.json> <photo_dir> [video ...]
"""
import glob
import json
import os
import struct
import subprocess
import sys

from PIL import Image, ExifTags

TAG = {v: k for k, v in ExifTags.TAGS.items()}


def dms(v, ref):
    d, m, s = (float(x) for x in v)
    x = d + m / 60 + s / 3600
    return -x if ref in ('S', 'W') else x


def photo_points(folder):
    out = []
    for f in sorted(glob.glob(os.path.join(folder, '*'))):
        if os.path.basename(f).startswith('.') or not f.lower().endswith(
                ('.jpg', '.jpeg', '.png', '.heic', '.tif', '.tiff')):
            continue
        ex = Image.open(f).getexif()
        g = ex.get_ifd(TAG['GPSInfo'])
        if not g or 2 not in g or 4 not in g:
            continue
        dt = str(ex.get(TAG['DateTimeOriginal']) or ex.get(TAG['DateTime']) or '')[:19]
        out.append({'name': os.path.basename(f),
                    'lat': round(dms(g[2], g.get(1, 'N')), 6),
                    'lon': round(dms(g[4], g.get(3, 'E')), 6),
                    'alt': round(float(g.get(6, 0)), 0), 'dt': dt})
    return out


def gpmf_fixes(path):
    probe = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'stream=index,codec_tag_string',
         '-of', 'csv=p=0', path], capture_output=True, text=True).stdout
    idx = [ln.split(',')[0] for ln in probe.splitlines() if 'gpmd' in ln]
    if not idx:
        return None
    buf = subprocess.run(
        ['ffmpeg', '-v', 'error', '-i', path, '-map', f'0:{idx[0]}', '-codec', 'copy',
         '-f', 'rawvideo', '-'], capture_output=True).stdout
    good = total = 0

    def walk(b, fix=None):
        nonlocal good, total
        i = 0
        while i + 8 <= len(b):
            key, typ, size = b[i:i + 4], b[i + 4:i + 5], b[i + 5]
            cnt = struct.unpack('>H', b[i + 6:i + 8])[0]
            n = size * cnt
            body = b[i + 8:i + 8 + n]
            i += 8 + n + ((-n) % 4)
            if typ == b'\x00':
                fix = walk(body, fix)
            elif key == b'GPSF' and len(body) >= 4:
                fix = struct.unpack('>L', body[:4])[0]
            elif key == b'GPS5' and size >= 20:
                for kk in range(cnt):
                    if (kk + 1) * size > len(body):
                        break
                    v = struct.unpack_from('>5l', body, kk * size)
                    total += 1
                    if (fix or 0) >= 2 and (v[0] or v[1]):
                        good += 1
        return fix

    walk(buf)
    return good, total


def main():
    out_path, folder = sys.argv[1], sys.argv[2]
    pts = photo_points(folder)
    json.dump(pts, open(out_path, 'w'), indent=1)
    days = sorted({p['dt'][:10] for p in pts})
    print(f'photos with GPS: {len(pts)}   dates: {", ".join(days)}')
    if pts:
        print(f"  lat {min(p['lat'] for p in pts):.4f}..{max(p['lat'] for p in pts):.4f}"
              f"   lon {min(p['lon'] for p in pts):.4f}..{max(p['lon'] for p in pts):.4f}")
    print('wrote', out_path)

    for v in sys.argv[3:]:
        r = gpmf_fixes(v)
        name = os.path.basename(v)
        if r is None:
            print(f'  {name}: no gpmd telemetry stream')
        elif r[0] == 0:
            print(f'  {name}: gpmd present but 0 of {r[1]} samples have a fix - '
                  f'unusable, the camera never locked')
        else:
            print(f'  {name}: {r[0]} of {r[1]} samples with a fix')


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""生成 FastRead 应用图标 (res/icon.png / icon.ico / icon.icns), 仅用标准库。"""
import os
import struct
import zlib

RES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'res')


def _png(w, h, pixels):
    def chunk(tag, data):
        c = tag + data
        return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c))
    ihdr = struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)
    raw = b''.join(b'\x00' + bytes(v for px in row for v in px) for row in pixels)
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', ihdr)
            + chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b''))


def draw(size):
    r = 0.17
    cx = cy = 0.5
    hx = hy = 0.5
    blue = (13, 110, 253)
    white = (255, 255, 255)
    book = (0.24, 0.26, 0.76, 0.76)
    spine = (0.475, 0.525)
    lines = (0.36, 0.47, 0.58, 0.69)
    px = []
    for y in range(size):
        row = []
        ny = (y + 0.5) / size
        for x in range(size):
            nx = (x + 0.5) / size
            dx = max(abs(nx - cx) - (hx - r), 0)
            dy = max(abs(ny - cy) - (hy - r), 0)
            if dx * dx + dy * dy > r * r:
                row.append((0, 0, 0, 0))
                continue
            color = blue
            b0, t0, b1, t1 = book
            s0, s1 = spine
            if b0 < nx < b1 and t0 < ny < t1 and not (s0 < nx < s1):
                color = white
            page = False
            if s1 < nx < b1 or b0 < nx < s0:
                for ly in lines:
                    if abs(ny - ly) < 0.012:
                        page = True
            if page:
                color = blue
            row.append(color + (255,))
        px.append(row)
    return px


def write_ico(path, sizes):
    images = []
    offset = 6 + 16 * len(sizes)
    for i, s in enumerate(sizes):
        png = _png(s, s, draw(s))
        images.append((s, png))
        offset += 16
    header = struct.pack('<HHH', 0, 1, len(sizes))
    entries = b''
    data = b''
    for i, (s, png) in enumerate(images):
        entries += struct.pack('<BBBBHHII', s if s < 256 else 0, s if s < 256 else 0, 0, 0, 1, 32,
                               len(png), offset)
        data += png
        offset += len(png)
    with open(path, 'wb') as f:
        f.write(header + entries + data)


def write_icns(path, sizes):
    chunks = {16: 'icp4', 32: 'icp5', 64: 'icp6', 128: 'ic07', 256: 'ic08', 512: 'ic09', 1024: 'ic10'}
    body = b''
    for s, tag in sizes:
        png = _png(s, s, draw(s))
        body += tag.encode() + struct.pack('>I', len(png) + 8) + png
    with open(path, 'wb') as f:
        f.write(b'icns' + struct.pack('>I', len(body) + 8) + body)


def main():
    os.makedirs(RES_DIR, exist_ok=True)
    with open(os.path.join(RES_DIR, 'icon.png'), 'wb') as f:
        f.write(_png(256, 256, draw(256)))
    write_ico(os.path.join(RES_DIR, 'icon.ico'), [16, 32, 48, 256])
    write_icns(os.path.join(RES_DIR, 'icon.icns'), [(256, 'ic08'), (512, 'ic09'), (1024, 'ic10')])
    print("已生成 res/icon.png, res/icon.ico, res/icon.icns")


if __name__ == "__main__":
    main()

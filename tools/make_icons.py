#!/usr/bin/env python3
"""
生成应用图标：从 res/icon.png 生成圆角版 res/icon.png、res/icon.ico 与 res/icon.icns。
源图自动居中裁成正方形并加圆角（alpha 抗锯齿），缩放用 macOS 自带 sips / iconutil（无第三方库）。
"""

import os
import shutil
import struct
import subprocess
import sys
import tempfile
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "res")
SRC = os.path.join(RES, "icon.png")

ICO_SIZES = [16, 24, 32, 48, 64, 128, 256]
ICONSET = {  # (size, name)
    16: "icon_16x16.png",
    32: "icon_16x16@2x.png",
    32: "icon_32x32.png",
    64: "icon_32x32@2x.png",
    128: "icon_128x128.png",
    256: "icon_128x128@2x.png",
    256: "icon_256x256.png",
    512: "icon_256x256@2x.png",
    512: "icon_512x512.png",
    1024: "icon_512x512@2x.png",
}
ROUND_RATIO = 0.23  # 圆角半径 = 边长 * 0.23，接近 macOS 图标风格


def run(*cmd):
    subprocess.run(cmd, check=True)


def read_png_rgb(path):
    d = open(path, "rb").read()
    assert d[:8] == b"\x89PNG\r\n\x1a\n", "不是合法 PNG"
    pos = 8
    width = height = None
    idat = b""
    while pos < len(d):
        ln, typ = struct.unpack(">I4s", d[pos:pos + 8])
        data = d[pos + 8:pos + 8 + ln]
        if typ == b"IHDR":
            width, height, bit, ct, comp, flt, inter = struct.unpack(">IIBBBBB", data)
            assert (bit, ct, comp, flt, inter) == (8, 2, 0, 0, 0), "仅支持 8bit RGB 非交错 PNG"
        elif typ == b"IDAT":
            idat += data
        pos += 12 + ln
    raw = zlib.decompress(idat)
    return width, height, unfilter(raw, width, height, 3)


def unfilter(raw, w, h, bpp):
    out = bytearray()
    stride = w * bpp
    prev = bytearray(stride)
    pos = 0
    for _ in range(h):
        f = raw[pos]
        pos += 1
        row = bytearray(raw[pos:pos + stride])
        pos += stride
        if f == 1:
            for i in range(bpp, stride):
                row[i] = (row[i] + row[i - bpp]) & 0xFF
        elif f == 2:
            for i in range(stride):
                row[i] = (row[i] + prev[i]) & 0xFF
        elif f == 3:
            for i in range(stride):
                a = row[i - bpp] if i >= bpp else 0
                row[i] = (row[i] + ((a + prev[i]) >> 1)) & 0xFF
        elif f == 4:
            for i in range(stride):
                a = row[i - bpp] if i >= bpp else 0
                c = prev[i - bpp] if i >= bpp else 0
                row[i] = (row[i] + paeth(a, prev[i], c)) & 0xFF
        out += row
        prev = row
    return bytes(out)


def paeth(a, b, c):
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


def round_mask(w, h, radius):
    def coverage(x, y):
        dx = min(x, w - 1 - x)
        dy = min(y, h - 1 - y)
        if dx >= radius or dy >= radius:
            return 1.0
        inside = 0
        for sx in range(4):
            for sy in range(4):
                lx = min(x + (sx + 0.5) / 4, w - 1 - (x + (sx + 0.5) / 4))
                ly = min(y + (sy + 0.5) / 4, h - 1 - (y + (sy + 0.5) / 4))
                if (lx - radius) ** 2 + (ly - radius) ** 2 <= radius ** 2:
                    inside += 1
        return inside / 16.0

    mask = bytearray(w * h)
    for y in range(h):
        for x in range(w):
            mask[y * w + x] = int(coverage(x, y) * 255)
    return bytes(mask)


def write_png_rgba(path, w, h, rgb, mask):
    raw = bytearray()
    for y in range(h):
        raw += b"\x00"
        for x in range(w):
            i = (y * w + x) * 3
            raw += bytes(rgb[i:i + 3]) + bytes([mask[y * w + x]])
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)
    idat = zlib.compress(bytes(raw), 9)
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        for typ, data in ((b"IHDR", ihdr), (b"IDAT", idat), (b"IEND", b"")):
            f.write(struct.pack(">I", len(data)) + typ + data + struct.pack(">I", zlib.crc32(typ + data)))


def square_and_round():
    tmp = tempfile.mkdtemp(prefix="fastread_icon_")
    try:
        square = os.path.join(tmp, "square.png")
        run("sips", "--cropToHeightWidth", "1024", "1024", SRC, "--out", square)
        w, h, rgb = read_png_rgb(square)
        write_png_rgba(os.path.join(RES, "icon.png"), w, h, rgb, round_mask(w, h, int(w * ROUND_RATIO)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("已生成圆角 res/icon.png")


def gen_pngs(src, tmp):
    pngs = {}
    for size in set(list(ICO_SIZES) + list(ICONSET)):
        out = os.path.join(tmp, f"{size}.png")
        run("sips", "-z", str(size), str(size), src, "--out", out)
        with open(out, "rb") as f:
            pngs[size] = f.read()
    return pngs


def write_ico(path, pngs):
    with open(path, "wb") as f:
        f.write(struct.pack("<HHH", 0, 1, len(pngs)))
        offset = 6 + 16 * len(pngs)
        for size, data in pngs:
            f.write(struct.pack(
                "<BBBBHHII", size if size < 256 else 0, size if size < 256 else 0,
                0, 0, 1, 32, len(data), offset))
            offset += len(data)
        for _, data in pngs:
            f.write(data)


def write_icns(pngs):
    iconset = os.path.join(tempfile.mkdtemp(prefix="fastread_iconset_"), "icon.iconset")
    os.makedirs(iconset)
    for size, name in ICONSET.items():
        with open(os.path.join(iconset, name), "wb") as f:
            f.write(pngs[size])
    run("iconutil", "-c", "icns", iconset, "-o", os.path.join(RES, "icon.icns"))


def main():
    if not os.path.isfile(SRC):
        print(f"缺少源图: {SRC}")
        sys.exit(1)
    if not shutil.which("sips") or not shutil.which("iconutil"):
        print("需要 macOS 自带的 sips 和 iconutil")
        sys.exit(1)

    square_and_round()
    tmp = tempfile.mkdtemp(prefix="fastread_icon_")
    try:
        pngs = gen_pngs(SRC, tmp)
        write_ico(os.path.join(RES, "icon.ico"), [(s, pngs[s]) for s in ICO_SIZES])
        write_icns(pngs)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("已生成 res/icon.ico 与 res/icon.icns")


if __name__ == "__main__":
    main()

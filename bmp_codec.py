#!/usr/bin/env python3
"""BMP image encoder/decoder — read and write 24-bit BMP files.

Usage:
    python bmp_codec.py --test
"""
import struct, sys

def encode_bmp(width, height, pixels) -> bytes:
    """Encode RGB pixels to BMP. pixels: list of (r,g,b) row-major, top-to-bottom."""
    row_size = (width * 3 + 3) & ~3  # pad to 4-byte boundary
    img_size = row_size * height
    file_size = 54 + img_size
    header = struct.pack('<2sIHHI', b'BM', file_size, 0, 0, 54)
    dib = struct.pack('<IIIHHIIIIII', 40, width, height, 1, 24, 0, img_size, 2835, 2835, 0, 0)
    data = bytearray()
    for y in range(height - 1, -1, -1):  # BMP is bottom-up
        for x in range(width):
            r, g, b = pixels[y * width + x]
            data.extend([b, g, r])  # BGR
        data.extend(b'\x00' * (row_size - width * 3))
    return header + dib + bytes(data)

def decode_bmp(data: bytes) -> dict:
    """Decode BMP to pixel data."""
    assert data[:2] == b'BM', "Not a BMP"
    offset = struct.unpack_from('<I', data, 10)[0]
    w, h = struct.unpack_from('<ii', data, 18)
    bpp = struct.unpack_from('<H', data, 28)[0]
    assert bpp == 24, f"Only 24-bit supported, got {bpp}"
    row_size = (w * 3 + 3) & ~3
    pixels = []
    for y in range(abs(h) - 1, -1, -1) if h > 0 else range(abs(h)):
        row_off = offset + y * row_size
        for x in range(w):
            b, g, r = data[row_off + x*3], data[row_off + x*3 + 1], data[row_off + x*3 + 2]
            pixels.append((r, g, b))
    return {'width': w, 'height': abs(h), 'pixels': pixels}

def test():
    print("=== BMP Codec Tests ===\n")
    # Gradient image
    w, h = 8, 6
    pixels = [(x*32&255, y*40&255, (x+y)*20&255) for y in range(h) for x in range(w)]
    bmp = encode_bmp(w, h, pixels)
    assert bmp[:2] == b'BM'
    print(f"✓ Encoded: {w}×{h} → {len(bmp)} bytes")

    img = decode_bmp(bmp)
    assert img['width'] == w and img['height'] == h
    assert img['pixels'] == pixels
    print(f"✓ Decoded: {img['width']}×{img['height']}, {len(img['pixels'])} pixels")
    print("✓ Roundtrip pixel-perfect")

    # 1x1
    bmp1 = encode_bmp(1, 1, [(255, 0, 0)])
    img1 = decode_bmp(bmp1)
    assert img1['pixels'] == [(255, 0, 0)]
    print("✓ 1×1 red pixel")

    # Large
    bmp_big = encode_bmp(100, 100, [(i%256, 0, 0) for i in range(10000)])
    assert len(decode_bmp(bmp_big)['pixels']) == 10000
    print("✓ 100×100 image")

    # Row padding (width=3 needs 1 byte pad per row)
    bmp3 = encode_bmp(3, 2, [(255,0,0),(0,255,0),(0,0,255),(1,2,3),(4,5,6),(7,8,9)])
    img3 = decode_bmp(bmp3)
    assert img3['pixels'][0] == (255, 0, 0) and img3['pixels'][5] == (7, 8, 9)
    print("✓ Row padding handled")

    print("\nAll tests passed! ✓")

if __name__ == "__main__":
    test() if not sys.argv[1:] or sys.argv[1] == "--test" else None

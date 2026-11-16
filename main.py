#!/usr/bin/env python3
"""Entry program for the make.fun ai-excited-01 image competition.

The entry image lives next to this script as ``entry.png`` (JPEG bytes are
fine too, despite the name). Running this script checks the image against
the competition's limits and copies it into ``/output/entry.png`` so the
judge can pick it up.

Checks performed, using only the standard library:
  * the file exists and is readable
  * its first bytes match the PNG or JPEG signature
  * its size is at most 1 MiB
  * its pixel dimensions are at most 1024 x 1024 (read from the PNG IHDR
    chunk or the first JPEG start-of-frame segment)

Any failed check prints an error and exits non-zero. On success the script
prints a short summary of what it verified and where the copy went.
"""

import os
import shutil
import struct
import sys

SOURCE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entry.png")
DEST = "/output/entry.png"

MAX_BYTES = 1_048_576
MAX_WIDTH = 1024
MAX_HEIGHT = 1024

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
JPEG_MAGIC = b"\xff\xd8\xff"


def die(message):
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)


def png_dimensions(data):
    """Return (width, height) from the IHDR chunk of a PNG byte string."""
    if len(data) < 33 or data[12:16] != b"IHDR":
        die("PNG file has no IHDR chunk where one was expected")
    width, height = struct.unpack(">II", data[16:24])
    return width, height


def jpeg_dimensions(data):
    """Return (width, height) from the first SOF marker of a JPEG."""
    pos = 2  # skip the SOI marker
    while pos + 9 < len(data):
        if data[pos] != 0xFF:
            die("JPEG stream is malformed (expected a marker)")
        marker = data[pos + 1]
        if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
            pos += 2
            continue
        if pos + 4 > len(data):
            die("JPEG stream ends inside a segment header")
        length = struct.unpack(">H", data[pos + 2:pos + 4])[0]
        if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
            # Start-of-frame: precision byte, then height, then width.
            height, width = struct.unpack(">HH", data[pos + 5:pos + 9])
            return width, height
        pos += 2 + length
    die("no start-of-frame segment found in JPEG")


def main():
    if not os.path.isfile(SOURCE):
        die(f"entry image not found: {SOURCE}")

    with open(SOURCE, "rb") as handle:
        data = handle.read()

    if data.startswith(PNG_MAGIC):
        kind = "PNG"
        width, height = png_dimensions(data)
    elif data.startswith(JPEG_MAGIC):
        kind = "JPEG"
        width, height = jpeg_dimensions(data)
    else:
        die("entry image is neither PNG nor JPEG (bad magic bytes)")

    size = len(data)
    if size > MAX_BYTES:
        die(f"entry image is {size} bytes, over the {MAX_BYTES} byte limit")
    if width > MAX_WIDTH or height > MAX_HEIGHT:
        die(f"entry image is {width}x{height}px, over the "
            f"{MAX_WIDTH}x{MAX_HEIGHT}px limit")

    os.makedirs(os.path.dirname(DEST), exist_ok=True)
    shutil.copyfile(SOURCE, DEST)

    print("Entry image OK")
    print(f"  format:     {kind}")
    print(f"  dimensions: {width}x{height} px")
    print(f"  size:       {size} bytes")
    print(f"  copied to:  {DEST}")


if __name__ == "__main__":
    main()

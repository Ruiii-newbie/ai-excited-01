"""ai-excited-01 entry: validate and copy the entry image.

The entry image lives in this repository as ``entry.png`` (JPEG bytes under
that name, matching the competition's file rules). This program checks the
image before copying it, so a broken or oversized file can never be
submitted by accident:

* the file must exist next to this script;
* its first bytes must be a PNG signature or a JPEG SOI marker;
* it must be at most 1 MiB (1048576 bytes);
* its pixel dimensions must be at most 1024 x 1024.

Dimensions are read straight from the file headers (PNG IHDR, JPEG SOF)
with no third-party libraries. The copy is deterministic: the same input
always produces the same output bytes. The destination is ``/output`` by
default, or ``$MAKEFUN_OUTPUT_DIR`` when that is set.
"""

import os
import shutil
import struct
import sys
from pathlib import Path

MAX_BYTES = 1_048_576
MAX_SIDE = 1024

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
JPEG_MAGIC = b"\xff\xd8\xff"


def png_dimensions(data: bytes) -> tuple[int, int]:
    """Width and height from a PNG IHDR chunk (bytes 16..24, big-endian)."""
    if len(data) < 24 or data[12:16] != b"IHDR":
        raise ValueError("not a well-formed PNG (missing IHDR)")
    width, height = struct.unpack(">II", data[16:24])
    return width, height


def jpeg_dimensions(data: bytes) -> tuple[int, int]:
    """Width and height from the first JPEG start-of-frame segment."""
    pos = 2  # past the SOI marker
    while pos + 4 <= len(data):
        if data[pos] != 0xFF:
            raise ValueError("corrupt JPEG marker stream")
        marker = data[pos + 1]
        if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
            # Markers with no length field: standalone, single byte long.
            pos += 2
            continue
        seg_len = struct.unpack(">H", data[pos + 2 : pos + 4])[0]
        if seg_len < 2 or pos + 2 + seg_len > len(data):
            raise ValueError("corrupt JPEG segment length")
        if marker in (0xC0, 0xC1, 0xC2):  # baseline / extended / progressive
            height, width = struct.unpack(">HH", data[pos + 5 : pos + 9])
            return width, height
        pos += 2 + seg_len
    raise ValueError("no JPEG start-of-frame segment found")


def inspect(data: bytes) -> tuple[str, tuple[int, int]]:
    """Return (format, (width, height)) for PNG or JPEG bytes, else fail."""
    if data.startswith(PNG_MAGIC):
        return "PNG", png_dimensions(data)
    if data.startswith(JPEG_MAGIC):
        return "JPEG", jpeg_dimensions(data)
    raise ValueError("unknown image format (need PNG or JPEG magic bytes)")


def main() -> int:
    source = Path(__file__).resolve().parent / "entry.png"
    if not source.is_file():
        print(f"error: entry image not found: {source}", file=sys.stderr)
        return 1

    data = source.read_bytes()
    try:
        fmt, (width, height) = inspect(data)
    except ValueError as exc:
        print(f"error: {source}: {exc}", file=sys.stderr)
        return 1

    problems = []
    if len(data) > MAX_BYTES:
        problems.append(f"size {len(data)} bytes exceeds {MAX_BYTES} byte limit")
    if width > MAX_SIDE or height > MAX_SIDE:
        problems.append(f"dimensions {width}x{height} exceed {MAX_SIDE}x{MAX_SIDE}")
    if problems:
        for problem in problems:
            print(f"error: {source}: {problem}", file=sys.stderr)
        return 1

    output_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_dir / "entry.png"
    shutil.copyfile(source, destination)

    print(f"entry image : {source}")
    print(f"format      : {fmt}")
    print(f"dimensions  : {width}x{height}")
    print(f"size        : {len(data)} bytes (limit {MAX_BYTES})")
    print(f"copied to   : {destination}")
    print("validation  : OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())

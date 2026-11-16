"""ai-excited-01 entry: copy the entry image to /output/entry.png.

No network, no randomness: the output is a byte-for-byte copy of the
entry image shipped in this repository, so repeated runs are identical.
"""

import os
import shutil
import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parent
    source = repo_root / "entry.png"
    if not source.is_file():
        print(f"error: {source} not found", file=sys.stderr)
        return 1
    output_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_dir / "entry.png"
    shutil.copyfile(source, destination)
    print(f"wrote {destination} ({destination.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

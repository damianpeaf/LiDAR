"""Convert JSON point cloud datasets to PLY format for CloudCompare."""

import json
import struct
import sys
from pathlib import Path


def write_ply(points, output_path):
    n = len(points)
    header = (
        "ply\n"
        "format binary_little_endian 1.0\n"
        f"element vertex {n}\n"
        "property float x\n"
        "property float y\n"
        "property float z\n"
        "property uchar red\n"
        "property uchar green\n"
        "property uchar blue\n"
        "end_header\n"
    )
    with open(output_path, "wb") as f:
        f.write(header.encode("ascii"))
        for p in points:
            intensity = int(p["intensity"]) & 0xFF
            f.write(struct.pack("<fffBBB", p["x"], p["y"], p["z"], intensity, intensity, intensity))


def convert(json_path):
    print(f"Reading {json_path.name} ...")
    with open(json_path, "r", encoding="utf-8") as f:
        points = json.load(f)
    print(f"  {len(points):,} points")
    out = json_path.with_suffix(".ply")
    write_ply(points, out)
    print(f"  -> {out.name}")


def main():
    folder = Path(__file__).parent
    targets = [Path(a) for a in sys.argv[1:]] if sys.argv[1:] else sorted(folder.glob("*.json"))
    for p in targets:
        if p.name == Path(__file__).name:
            continue
        convert(p)
    print("Done.")


if __name__ == "__main__":
    main()

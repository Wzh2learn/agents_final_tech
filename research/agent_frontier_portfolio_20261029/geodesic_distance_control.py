#!/usr/bin/env python3
"""Bound point-to-AF-boundary WGS84 distance by sampling geodesic segments.

For a polyline whose adjacent vertices are joined by shortest WGS84 geodesics,
all endpoints and regularly spaced intermediate samples are evaluated. Every
point on a segment is within half the maximum sample spacing of a sample;
the triangle inequality yields a lower and an upper bound on the true minimum.
This is a post-hoc sensitivity check, not an upstream benchmark reference.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from pyproj import Geod, __version__ as pyproj_version


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def distance_bounds(segments, point_lon, point_lat, spacing_m):
    if spacing_m <= 0:
        raise ValueError("spacing must be positive")
    geod = Geod(ellps="WGS84")
    samples = []
    max_gap = 0.0
    segment_count = 0
    for coords in segments:
        for first, last in zip(coords, coords[1:]):
            lon1, lat1 = map(float, first[:2])
            lon2, lat2 = map(float, last[:2])
            _, _, length = geod.inv(lon1, lat1, lon2, lat2)
            if not math.isfinite(length):
                raise ValueError("invalid segment coordinates")
            n = max(1, math.ceil(length / spacing_m))
            samples.append((lon1, lat1))
            if n > 1:
                samples.extend(geod.npts(lon1, lat1, lon2, lat2, n - 1))
            samples.append((lon2, lat2))
            max_gap = max(max_gap, length / n)
            segment_count += 1
    if not samples:
        raise ValueError("no boundary segments")
    points = np.asarray(samples, dtype=float)
    _, _, distances = geod.inv(np.full(len(points), point_lon), np.full(len(points), point_lat),
                                points[:, 0], points[:, 1])
    upper = float(np.min(distances))
    # Allow 10 micrometres for floating-point and geodesic-library roundoff.
    # This is a numerical guard, not a formal error certificate for pyproj.
    numerical_pad_m = 1e-5
    return {"lower_km": max(0.0, upper - max_gap / 2 - numerical_pad_m) / 1000,
            "upper_km": (upper + numerical_pad_m) / 1000,
            "numerical_pad_m": numerical_pad_m, "max_gap_m": max_gap,
            "sample_count": len(points), "segment_count": segment_count}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("boundaries", type=Path)
    parser.add_argument("answer", type=Path)
    parser.add_argument("--spacing-m", type=float, default=1000)
    args = parser.parse_args()
    features = json.loads(args.boundaries.read_text(encoding="utf-8"))["features"]
    answer = json.loads(args.answer.read_text(encoding="utf-8"))
    matching = [x for x in features if "AF" in (x["properties"].get("PlateA"), x["properties"].get("PlateB"))]
    segments = []
    for feature in matching:
        geometry = feature["geometry"]
        if geometry["type"] == "LineString":
            segments.append(geometry["coordinates"])
        elif geometry["type"] == "MultiLineString":
            segments.extend(geometry["coordinates"])
        else:
            raise ValueError("unexpected boundary geometry")
    bounds = distance_bounds(segments, float(answer["longitude"]), float(answer["latitude"]), args.spacing_m)
    print(json.dumps({"status": "POST_HOC_GEODESIC_SAMPLING_BOUND",
                      "interpretation": "WGS84 shortest geodesic segments between listed vertices; not a benchmark gold label",
                      "boundaries_sha256": sha(args.boundaries), "agent_answer_sha256": sha(args.answer),
                      "plate": "AF", "boundary_features": len(matching),
                      "event_id": answer.get("id"), "agent_distance_km": answer.get("distance_km"),
                      "spacing_m": args.spacing_m, "bounds": bounds,
                      "numpy": np.__version__, "pyproj": pyproj_version}, indent=2))


if __name__ == "__main__":
    main()

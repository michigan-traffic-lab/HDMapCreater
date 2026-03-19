#!/usr/bin/env python3
"""Prune dense intermediate geometry nodes from OSM ways."""

from __future__ import annotations

import argparse
import math
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


EARTH_RADIUS_METERS = 6_371_000.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Remove intermediate way nodes that are closer than the requested "
            "minimum spacing while always preserving each way's end nodes."
        )
    )
    parser.add_argument(
        "input",
        nargs="?",
        default="lanelet2.osm",
        help="Input OSM file. Defaults to lanelet2.osm.",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="lanelet2_pruned.osm",
        help="Output OSM file. Defaults to lanelet2_pruned.osm.",
    )
    parser.add_argument(
        "--min-distance",
        type=float,
        default=2.0,
        help="Minimum spacing in meters between kept nodes. Defaults to 2.0.",
    )
    return parser.parse_args()


def haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(d_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2.0) ** 2
    )
    return 2.0 * EARTH_RADIUS_METERS * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))


def simplify_way(node_refs: list[str], node_coords: dict[str, tuple[float, float]], min_distance: float) -> list[str]:
    if len(node_refs) <= 2:
        return node_refs[:]

    kept_refs = [node_refs[0]]
    last_kept = node_refs[0]

    for node_ref in node_refs[1:-1]:
        last_lat, last_lon = node_coords[last_kept]
        lat, lon = node_coords[node_ref]
        if haversine_meters(last_lat, last_lon, lat, lon) >= min_distance:
            kept_refs.append(node_ref)
            last_kept = node_ref

    kept_refs.append(node_refs[-1])
    return kept_refs


def prune_geometry_nodes(input_path: Path, output_path: Path, min_distance: float) -> None:
    tree = ET.parse(input_path)
    root = tree.getroot()

    node_elements = {node.attrib["id"]: node for node in root.findall("node")}
    node_coords = {
        node_id: (float(node.attrib["lat"]), float(node.attrib["lon"]))
        for node_id, node in node_elements.items()
    }

    original_way_refs: set[str] = set()
    kept_way_refs: set[str] = set()
    changed_ways = 0
    removed_way_refs = 0

    for way in root.findall("way"):
        nd_elements = way.findall("nd")
        if len(nd_elements) <= 2:
            kept_way_refs.update(nd.attrib["ref"] for nd in nd_elements)
            original_way_refs.update(nd.attrib["ref"] for nd in nd_elements)
            continue

        original_refs = [nd.attrib["ref"] for nd in nd_elements]
        original_way_refs.update(original_refs)

        missing_refs = [node_ref for node_ref in original_refs if node_ref not in node_coords]
        if missing_refs:
            raise ValueError(
                f"Way {way.attrib.get('id', '<unknown>')} references missing nodes: "
                + ", ".join(missing_refs[:5])
            )

        simplified_refs = simplify_way(original_refs, node_coords, min_distance)
        kept_way_refs.update(simplified_refs)

        if simplified_refs == original_refs:
            continue

        changed_ways += 1
        removed_way_refs += len(original_refs) - len(simplified_refs)

        for nd_element, node_ref in zip(nd_elements, simplified_refs):
            nd_element.set("ref", node_ref)

        for nd_element in nd_elements[len(simplified_refs) :]:
            way.remove(nd_element)

    removed_node_elements = 0
    for node_id, node in list(node_elements.items()):
        if node_id in kept_way_refs:
            continue
        if node_id not in original_way_refs:
            continue
        if len(node):
            continue
        root.remove(node)
        removed_node_elements += 1

    try:
        ET.indent(tree, space="  ")
    except AttributeError:
        pass

    output_path.parent.mkdir(parents=True, exist_ok=True)
    tree.write(output_path, encoding="UTF-8", xml_declaration=True)

    print(f"Input: {input_path}")
    print(f"Output: {output_path}")
    print(f"Minimum spacing: {min_distance:.3f} m")
    print(f"Ways updated: {changed_ways}")
    print(f"Way node references removed: {removed_way_refs}")
    print(f"Orphan node elements removed: {removed_node_elements}")


def main() -> int:
    args = parse_args()
    if args.min_distance <= 0:
        print("--min-distance must be greater than 0.", file=sys.stderr)
        return 2

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.is_file():
        print(f"Input file not found: {input_path}", file=sys.stderr)
        return 2

    prune_geometry_nodes(input_path, output_path, args.min_distance)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

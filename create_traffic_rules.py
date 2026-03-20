#!/usr/bin/env python3
"""Create traffic-light regulatory relations and attach them to road lanelets."""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create missing traffic-light regulatory_element relations from "
            "traffic-light/stop-line lanelet coverage, then add matching "
            "regulatory_element relation members to lanelet relations."
        )
    )
    parser.add_argument("-i", "--input", help="Input OSM file.")
    parser.add_argument("-o", "--output", help="Output OSM file.")
    return parser.parse_args()


def has_tag(element: ET.Element, key: str, value: str) -> bool:
    return any(
        tag.attrib.get("k") == key and tag.attrib.get("v") == value
        for tag in element.findall("tag")
    )


def is_deleted(element: ET.Element) -> bool:
    return element.attrib.get("action") == "delete"


def numeric_sort_key(value: str) -> tuple[int, int | str]:
    try:
        return (0, int(value))
    except ValueError:
        return (1, value)


def collect_way_nodes(
    root: ET.Element, type_value: str | None = None
) -> dict[str, list[str]]:
    way_nodes: dict[str, list[str]] = {}

    for way in root.findall("way"):
        if is_deleted(way):
            continue
        if type_value is not None and not has_tag(way, "type", type_value):
            continue

        way_id = way.attrib.get("id")
        if not way_id:
            continue

        node_refs = [nd.attrib["ref"] for nd in way.findall("nd") if "ref" in nd.attrib]
        if node_refs:
            way_nodes[way_id] = node_refs

    return way_nodes


def collect_way_elements(
    root: ET.Element, type_value: str | None = None
) -> dict[str, ET.Element]:
    ways: dict[str, ET.Element] = {}

    for way in root.findall("way"):
        if is_deleted(way):
            continue
        if type_value is not None and not has_tag(way, "type", type_value):
            continue

        way_id = way.attrib.get("id")
        if not way_id:
            continue

        ways[way_id] = way

    return ways


def collect_relation_ids(root: ET.Element) -> set[int]:
    relation_ids: set[int] = set()

    for relation in root.findall("relation"):
        relation_id = relation.attrib.get("id")
        if relation_id is None:
            continue
        try:
            relation_ids.add(int(relation_id))
        except ValueError:
            continue

    return relation_ids


def choose_start_relation_id(
    existing_ids: set[int], requested_id: int | None, direction: str
) -> int:
    if requested_id is not None:
        if requested_id in existing_ids:
            raise ValueError(f"Requested relation ID already exists: {requested_id}")
        return requested_id

    if direction == "negative":
        return min(existing_ids, default=0) - 1

    return max(existing_ids, default=0) + 1


def next_relation_id(current_id: int, direction: str) -> int:
    if direction == "negative":
        return current_id - 1
    return current_id + 1


def allocate_relation_ids(
    existing_ids: set[int],
    count: int,
    requested_start_id: int | None = None,
    direction: str = "negative",
) -> list[int]:
    if count <= 0:
        return []

    relation_ids: list[int] = []
    used_ids = set(existing_ids)
    current_id = choose_start_relation_id(used_ids, requested_start_id, direction)

    while len(relation_ids) < count:
        if current_id not in used_ids:
            relation_ids.append(current_id)
            used_ids.add(current_id)
        current_id = next_relation_id(current_id, direction)

    return relation_ids


def collect_existing_traffic_light_relations(
    root: ET.Element,
) -> tuple[set[tuple[str, str]], dict[str, str]]:
    pairs: set[tuple[str, str]] = set()
    relation_id_by_traffic_light: dict[str, str] = {}

    for relation in root.findall("relation"):
        if is_deleted(relation):
            continue
        if not (
            has_tag(relation, "type", "regulatory_element")
            and has_tag(relation, "subtype", "traffic_light")
        ):
            continue

        relation_id = relation.attrib.get("id")
        if not relation_id:
            continue

        refers = [
            member.attrib["ref"]
            for member in relation.findall("member")
            if member.attrib.get("type") == "way"
            and member.attrib.get("role") == "refers"
            and "ref" in member.attrib
        ]
        ref_lines = [
            member.attrib["ref"]
            for member in relation.findall("member")
            if member.attrib.get("type") == "way"
            and member.attrib.get("role") == "ref_line"
            and "ref" in member.attrib
        ]

        for traffic_light_id in refers:
            existing_relation_id = relation_id_by_traffic_light.get(traffic_light_id)
            if existing_relation_id is not None and existing_relation_id != relation_id:
                raise ValueError(
                    "Traffic light "
                    f"{traffic_light_id} belongs to multiple traffic-light "
                    f"regulatory relations: {existing_relation_id}, {relation_id}"
                )
            relation_id_by_traffic_light[traffic_light_id] = relation_id

        for stop_line_id in ref_lines:
            for traffic_light_id in refers:
                pairs.add((stop_line_id, traffic_light_id))

    return pairs, relation_id_by_traffic_light


def get_way_end_nodes(
    way: ET.Element, way_nodes: dict[str, list[str]]
) -> tuple[str, str]:
    way_id = way.attrib.get("id")
    if not way_id:
        raise ValueError("Encountered a way without an id.")

    node_refs = way_nodes.get(way_id)
    if node_refs is None:
        raise ValueError(f"Way {way_id} is missing or deleted.")
    if len(node_refs) < 2:
        raise ValueError(f"Way {way_id} must contain at least two nodes.")

    return node_refs[0], node_refs[-1]


BoundaryNodeKey = tuple[str, ...]


@dataclass
class RoadLaneletIndex:
    relation_by_id: dict[str, ET.Element]
    left_boundary_nodes_by_lanelet_id: dict[str, BoundaryNodeKey]
    right_boundary_nodes_by_lanelet_id: dict[str, BoundaryNodeKey]
    lanelet_ids_by_left_boundary_node: dict[str, list[str]]
    lanelet_ids_by_left_boundary_key: dict[BoundaryNodeKey, list[str]]
    lanelet_ids_by_boundary_key: dict[BoundaryNodeKey, list[str]]


def sort_unique_ids(values: list[str]) -> list[str]:
    return sorted(set(values), key=numeric_sort_key)


def get_unique_way_member_ref(relation: ET.Element, role: str) -> str:
    refs = [
        member.attrib["ref"]
        for member in relation.findall("member")
        if member.attrib.get("type") == "way"
        and member.attrib.get("role") == role
        and "ref" in member.attrib
    ]
    relation_id = relation.attrib.get("id", "<unknown>")
    if len(refs) != 1:
        raise ValueError(
            f"Road lanelet relation {relation_id} must contain exactly one {role!r} way member."
        )
    return refs[0]


def build_road_lanelet_index(
    root: ET.Element, way_nodes: dict[str, list[str]]
) -> RoadLaneletIndex:
    relation_by_id: dict[str, ET.Element] = {}
    left_boundary_nodes_by_lanelet_id: dict[str, BoundaryNodeKey] = {}
    right_boundary_nodes_by_lanelet_id: dict[str, BoundaryNodeKey] = {}
    lanelet_ids_by_left_boundary_node: dict[str, list[str]] = {}
    lanelet_ids_by_left_boundary_key: dict[BoundaryNodeKey, list[str]] = {}
    lanelet_ids_by_boundary_key: dict[BoundaryNodeKey, list[str]] = {}

    for relation in root.findall("relation"):
        if is_deleted(relation):
            continue
        if not (has_tag(relation, "type", "lanelet") and has_tag(relation, "subtype", "road")):
            continue

        lanelet_id = relation.attrib.get("id")
        if not lanelet_id:
            raise ValueError("Encountered a road lanelet relation without an id.")

        left_way_id = get_unique_way_member_ref(relation, "left")
        right_way_id = get_unique_way_member_ref(relation, "right")

        if left_way_id not in way_nodes:
            raise ValueError(
                f"Road lanelet relation {lanelet_id} references missing left boundary way {left_way_id}."
            )
        if right_way_id not in way_nodes:
            raise ValueError(
                f"Road lanelet relation {lanelet_id} references missing right boundary way {right_way_id}."
            )

        left_nodes = tuple(way_nodes[left_way_id])
        right_nodes = tuple(way_nodes[right_way_id])

        relation_by_id[lanelet_id] = relation
        left_boundary_nodes_by_lanelet_id[lanelet_id] = left_nodes
        right_boundary_nodes_by_lanelet_id[lanelet_id] = right_nodes

        for node_ref in left_nodes:
            lanelet_ids_by_left_boundary_node.setdefault(node_ref, []).append(lanelet_id)

        lanelet_ids_by_left_boundary_key.setdefault(left_nodes, []).append(lanelet_id)
        lanelet_ids_by_boundary_key.setdefault(left_nodes, []).append(lanelet_id)
        lanelet_ids_by_boundary_key.setdefault(right_nodes, []).append(lanelet_id)

    for lanelet_ids in lanelet_ids_by_left_boundary_node.values():
        lanelet_ids[:] = sort_unique_ids(lanelet_ids)
    for lanelet_ids in lanelet_ids_by_left_boundary_key.values():
        lanelet_ids[:] = sort_unique_ids(lanelet_ids)
    for lanelet_ids in lanelet_ids_by_boundary_key.values():
        lanelet_ids[:] = sort_unique_ids(lanelet_ids)

    return RoadLaneletIndex(
        relation_by_id=relation_by_id,
        left_boundary_nodes_by_lanelet_id=left_boundary_nodes_by_lanelet_id,
        right_boundary_nodes_by_lanelet_id=right_boundary_nodes_by_lanelet_id,
        lanelet_ids_by_left_boundary_node=lanelet_ids_by_left_boundary_node,
        lanelet_ids_by_left_boundary_key=lanelet_ids_by_left_boundary_key,
        lanelet_ids_by_boundary_key=lanelet_ids_by_boundary_key,
    )


def get_lanelet_boundary_nodes(
    road_lanelet_index: RoadLaneletIndex, lanelet_id: str, boundary_side: str
) -> BoundaryNodeKey:
    if boundary_side == "left":
        return road_lanelet_index.left_boundary_nodes_by_lanelet_id[lanelet_id]
    if boundary_side == "right":
        return road_lanelet_index.right_boundary_nodes_by_lanelet_id[lanelet_id]
    raise ValueError(f"Unsupported boundary side: {boundary_side}")


def other_boundary_side(boundary_side: str) -> str:
    if boundary_side == "left":
        return "right"
    if boundary_side == "right":
        return "left"
    raise ValueError(f"Unsupported boundary side: {boundary_side}")


def find_unique_next_lanelet_id(
    current_lanelet_id: str,
    right_boundary_nodes: BoundaryNodeKey,
    road_lanelet_index: RoadLaneletIndex,
    way_id: str,
) -> str:
    next_lanelet_ids = [
        lanelet_id
        for lanelet_id in road_lanelet_index.lanelet_ids_by_left_boundary_key.get(
            right_boundary_nodes, []
        )
        if lanelet_id != current_lanelet_id
    ]
    if len(next_lanelet_ids) != 1:
        raise ValueError(
            f"Way {way_id} expected exactly one next road lanelet for boundary "
            f"{list(right_boundary_nodes)}, found {next_lanelet_ids or 'none'}."
        )
    return next_lanelet_ids[0]


def build_lanelet_chain_from_left_boundary(
    way_id: str,
    start_node_ref: str,
    end_node_ref: str,
    road_lanelet_index: RoadLaneletIndex,
) -> list[str]:
    first_lanelet_ids = road_lanelet_index.lanelet_ids_by_left_boundary_node.get(
        start_node_ref, []
    )
    if len(first_lanelet_ids) != 1:
        raise ValueError(
            f"Way {way_id} expected exactly one first road lanelet whose left boundary "
            f"contains node {start_node_ref}, found {first_lanelet_ids or 'none'}."
        )

    lanelet_ids: list[str] = []
    visited_lanelet_ids: set[str] = set()
    current_lanelet_id = first_lanelet_ids[0]

    while True:
        if current_lanelet_id in visited_lanelet_ids:
            raise ValueError(f"Way {way_id} produced a loop while walking road lanelets.")

        visited_lanelet_ids.add(current_lanelet_id)
        lanelet_ids.append(current_lanelet_id)

        right_boundary_nodes = road_lanelet_index.right_boundary_nodes_by_lanelet_id[
            current_lanelet_id
        ]
        if end_node_ref in right_boundary_nodes:
            return lanelet_ids

        current_lanelet_id = find_unique_next_lanelet_id(
            current_lanelet_id=current_lanelet_id,
            right_boundary_nodes=right_boundary_nodes,
            road_lanelet_index=road_lanelet_index,
            way_id=way_id,
        )


def try_build_lanelet_chain_from_boundary(
    first_lanelet_id: str,
    start_boundary_side: str,
    end_node_ref: str,
    road_lanelet_index: RoadLaneletIndex,
) -> list[str] | None:
    lanelet_ids: list[str] = []
    visited_lanelet_ids: set[str] = set()
    current_lanelet_id = first_lanelet_id
    current_start_boundary_side = start_boundary_side

    while True:
        if current_lanelet_id in visited_lanelet_ids:
            return None

        visited_lanelet_ids.add(current_lanelet_id)
        lanelet_ids.append(current_lanelet_id)

        next_boundary_side = other_boundary_side(current_start_boundary_side)
        next_boundary_nodes = get_lanelet_boundary_nodes(
            road_lanelet_index, current_lanelet_id, next_boundary_side
        )
        if end_node_ref in next_boundary_nodes:
            return lanelet_ids

        next_lanelet_ids = [
            lanelet_id
            for lanelet_id in road_lanelet_index.lanelet_ids_by_boundary_key.get(
                next_boundary_nodes, []
            )
            if lanelet_id != current_lanelet_id
        ]
        if len(next_lanelet_ids) != 1:
            return None

        next_lanelet_id = next_lanelet_ids[0]
        matching_boundary_sides = [
            boundary_side
            for boundary_side in ("left", "right")
            if get_lanelet_boundary_nodes(
                road_lanelet_index, next_lanelet_id, boundary_side
            )
            == next_boundary_nodes
        ]
        if len(matching_boundary_sides) != 1:
            return None

        current_lanelet_id = next_lanelet_id
        current_start_boundary_side = matching_boundary_sides[0]


def build_lanelet_chain_from_boundary_sharing(
    way_id: str,
    start_node_ref: str,
    end_node_ref: str,
    road_lanelet_index: RoadLaneletIndex,
) -> list[str]:
    first_lanelet_ids = sorted(
        {
            lanelet_id
            for lanelet_id in road_lanelet_index.relation_by_id
            if start_node_ref in road_lanelet_index.left_boundary_nodes_by_lanelet_id[lanelet_id]
            or start_node_ref
            in road_lanelet_index.right_boundary_nodes_by_lanelet_id[lanelet_id]
        },
        key=numeric_sort_key,
    )

    matched_chains: list[tuple[str, ...]] = []
    seen_chains: set[tuple[str, ...]] = set()
    for first_lanelet_id in first_lanelet_ids:
        for boundary_side in ("left", "right"):
            if start_node_ref not in get_lanelet_boundary_nodes(
                road_lanelet_index, first_lanelet_id, boundary_side
            ):
                continue
            lanelet_ids = try_build_lanelet_chain_from_boundary(
                first_lanelet_id=first_lanelet_id,
                start_boundary_side=boundary_side,
                end_node_ref=end_node_ref,
                road_lanelet_index=road_lanelet_index,
            )
            if lanelet_ids is None:
                continue

            lanelet_chain = tuple(lanelet_ids)
            if lanelet_chain in seen_chains:
                continue
            seen_chains.add(lanelet_chain)
            matched_chains.append(lanelet_chain)

    if len(matched_chains) != 1:
        raise ValueError(
            f"Way {way_id} expected exactly one road lanelet chain from node "
            f"{start_node_ref} to node {end_node_ref}, found "
            f"{[list(chain) for chain in matched_chains] or 'none'}."
        )

    return list(matched_chains[0])


def find_covered_lanelet_ids_for_way(
    way: ET.Element,
    way_nodes: dict[str, list[str]],
    road_lanelet_index: RoadLaneletIndex,
) -> list[str]:
    way_id = way.attrib.get("id")
    if not way_id:
        raise ValueError("Encountered a way without an id.")

    start_node_ref, end_node_ref = get_way_end_nodes(way, way_nodes)

    try:
        return build_lanelet_chain_from_left_boundary(
            way_id=way_id,
            start_node_ref=start_node_ref,
            end_node_ref=end_node_ref,
            road_lanelet_index=road_lanelet_index,
        )
    except ValueError:
        return build_lanelet_chain_from_boundary_sharing(
            way_id=way_id,
            start_node_ref=start_node_ref,
            end_node_ref=end_node_ref,
            road_lanelet_index=road_lanelet_index,
        )


def build_lanelet_coverage_by_way_type(
    root: ET.Element,
    type_value: str,
    way_nodes: dict[str, list[str]],
    road_lanelet_index: RoadLaneletIndex,
) -> dict[str, list[str]]:
    lanelet_list_by_way_id: dict[str, list[str]] = {}
    ways = collect_way_elements(root, type_value)

    for way_id in sorted(ways, key=numeric_sort_key):
        lanelet_list_by_way_id[way_id] = find_covered_lanelet_ids_for_way(
            way=ways[way_id],
            way_nodes=way_nodes,
            road_lanelet_index=road_lanelet_index,
        )

    return lanelet_list_by_way_id


def make_regulatory_relation(
    relation_id: int, stop_line_id: str, traffic_light_id: str
) -> ET.Element:
    relation = ET.Element(
        "relation",
        {
            "id": str(relation_id),
            "action": "modify",
            "visible": "true",
            "version": "1",
        },
    )
    ET.SubElement(
        relation,
        "member",
        {"type": "way", "ref": stop_line_id, "role": "ref_line"},
    )
    ET.SubElement(
        relation,
        "member",
        {"type": "way", "ref": traffic_light_id, "role": "refers"},
    )
    ET.SubElement(relation, "tag", {"k": "subtype", "v": "traffic_light"})
    ET.SubElement(relation, "tag", {"k": "type", "v": "regulatory_element"})
    return relation


def insert_member_before_tags(relation: ET.Element, member: ET.Element) -> None:
    insert_index = len(relation)
    for index, child in enumerate(relation):
        if child.tag == "tag":
            insert_index = index
            break
    relation.insert(insert_index, member)


def create_missing_traffic_light_relations(
    root: ET.Element,
) -> tuple[dict[str, list[str]], dict[str, str], RoadLaneletIndex]:
    way_nodes = collect_way_nodes(root)
    road_lanelet_index = build_road_lanelet_index(root, way_nodes)
    traffic_light_lanelets_by_way_id = build_lanelet_coverage_by_way_type(
        root=root,
        type_value="traffic_light",
        way_nodes=way_nodes,
        road_lanelet_index=road_lanelet_index,
    )
    stop_line_lanelets_by_way_id = build_lanelet_coverage_by_way_type(
        root=root,
        type_value="stop_line",
        way_nodes=way_nodes,
        road_lanelet_index=road_lanelet_index,
    )
    existing_pairs, relation_id_by_traffic_light = collect_existing_traffic_light_relations(
        root
    )

    existing_stop_line_ids_by_traffic_light: dict[str, set[str]] = {}
    for stop_line_id, traffic_light_id in existing_pairs:
        existing_stop_line_ids_by_traffic_light.setdefault(traffic_light_id, set()).add(
            stop_line_id
        )

    new_pairs: list[tuple[str, str]] = []
    for traffic_light_id in sorted(traffic_light_lanelets_by_way_id, key=numeric_sort_key):
        existing_stop_line_ids = sorted(
            existing_stop_line_ids_by_traffic_light.get(traffic_light_id, set()),
            key=numeric_sort_key,
        )
        if len(existing_stop_line_ids) > 1:
            raise ValueError(
                f"Traffic light {traffic_light_id} already belongs to multiple stop lines: "
                f"{existing_stop_line_ids}."
            )

        if traffic_light_id in relation_id_by_traffic_light:
            continue

        traffic_light_lanelet_ids = set(traffic_light_lanelets_by_way_id[traffic_light_id])
        matched_stop_line_ids = sorted(
            [
                stop_line_id
                for stop_line_id, stop_line_lanelet_ids in stop_line_lanelets_by_way_id.items()
                if traffic_light_lanelet_ids.intersection(stop_line_lanelet_ids)
            ],
            key=numeric_sort_key,
        )
        if len(matched_stop_line_ids) != 1:
            raise ValueError(
                f"Traffic light {traffic_light_id} expected exactly one stop line with common "
                f"road lanelets, found {matched_stop_line_ids or 'none'}."
            )

        new_pairs.append((matched_stop_line_ids[0], traffic_light_id))

    new_relation_ids = allocate_relation_ids(
        collect_relation_ids(root),
        len(new_pairs),
    )

    print(f"Road lanelet relations indexed: {len(road_lanelet_index.relation_by_id)}")
    print(f"Traffic-light ways: {len(traffic_light_lanelets_by_way_id)}")
    print(f"Stop-line ways: {len(stop_line_lanelets_by_way_id)}")
    print(f"Existing traffic-light relations: {len(relation_id_by_traffic_light)}")
    print(f"New traffic-light relations to create: {len(new_pairs)}")

    for relation_id, (stop_line_id, traffic_light_id) in zip(new_relation_ids, new_pairs):
        relation = make_regulatory_relation(relation_id, stop_line_id, traffic_light_id)
        root.append(relation)
        relation_id_by_traffic_light[traffic_light_id] = str(relation_id)

    return (
        traffic_light_lanelets_by_way_id,
        relation_id_by_traffic_light,
        road_lanelet_index,
    )


def add_regulatory_members_to_lanelets(
    traffic_light_lanelets_by_way_id: dict[str, list[str]],
    relation_id_by_traffic_light: dict[str, str],
    road_lanelet_index: RoadLaneletIndex,
) -> list[tuple[str, str]]:
    links_added: list[tuple[str, str]] = []

    for traffic_light_id in sorted(traffic_light_lanelets_by_way_id, key=numeric_sort_key):
        regulatory_relation_id = relation_id_by_traffic_light.get(traffic_light_id)
        if regulatory_relation_id is None:
            raise ValueError(
                f"Traffic light {traffic_light_id} does not have a regulatory relation id."
            )

        for lanelet_id in traffic_light_lanelets_by_way_id[traffic_light_id]:
            relation = road_lanelet_index.relation_by_id.get(lanelet_id)
            if relation is None:
                raise ValueError(f"Road lanelet relation {lanelet_id} is missing from the index.")

            existing_relation_refs = {
                member.attrib["ref"]
                for member in relation.findall("member")
                if member.attrib.get("type") == "relation" and "ref" in member.attrib
            }
            if regulatory_relation_id in existing_relation_refs:
                continue

            insert_member_before_tags(
                relation,
                ET.Element(
                    "member",
                    {
                        "type": "relation",
                        "ref": regulatory_relation_id,
                        "role": "regulatory_element",
                    },
                ),
            )
            links_added.append((lanelet_id, regulatory_relation_id))

    print(f"Traffic-light lanelet coverages processed: {len(traffic_light_lanelets_by_way_id)}")
    print(f"Lanelet regulatory_element members to add: {len(links_added)}")

    return links_added


def process_osm(
    input_path: Path,
    output_path: Path,
) -> None:
    tree = ET.parse(input_path)
    root = tree.getroot()

    print(f"Input: {input_path}")
    print()
    (
        traffic_light_lanelets_by_way_id,
        relation_id_by_traffic_light,
        road_lanelet_index,
    ) = create_missing_traffic_light_relations(root=root)
    print()
    add_regulatory_members_to_lanelets(
        traffic_light_lanelets_by_way_id=traffic_light_lanelets_by_way_id,
        relation_id_by_traffic_light=relation_id_by_traffic_light,
        road_lanelet_index=road_lanelet_index,
    )

    try:
        ET.indent(tree, space="  ")
    except AttributeError:
        pass

    output_path.parent.mkdir(parents=True, exist_ok=True)
    tree.write(output_path, encoding="UTF-8", xml_declaration=True)

    print(f"Output: {output_path}")


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)
    assert (
        input_path != output_path
    ), "Input and output paths must be different to avoid accidentally overwrite."

    if not input_path.is_file():
        print(f"Input file not found: {input_path}", file=sys.stderr)
        return 2

    try:
        process_osm(
            input_path=input_path,
            output_path=output_path,
        )
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

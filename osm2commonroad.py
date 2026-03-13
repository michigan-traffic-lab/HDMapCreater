#!/usr/bin/env python3
"""
Convert OSM to Lanelet2 via CommonRoad
For Michigan Stadium area
"""

import argparse

from crdesigner.map_conversion.map_conversion_interface import osm_to_commonroad
from commonroad.common.file_writer import CommonRoadFileWriter, OverwriteExistingFile
from commonroad.planning.planning_problem import PlanningProblemSet
from commonroad.scenario.scenario import Tag

parser = argparse.ArgumentParser()
parser.add_argument("--osm-file", type=str, default="example/map.osm", help="Path to the input OSM file")
parser.add_argument("--cr-file", type=str, default="example/map_cr.xml", help="Path to the output CommonRoad XML file")
args = parser.parse_args()

# Step 1: Convert OSM to CommonRoad
print("="*70)
print("[1/2] Converting OSM to CommonRoad...")
print("="*70)

scenario = osm_to_commonroad(args.osm_file)

print(f"\n✓ Conversion successful!")
print(f"  Lanelets: {len(scenario.lanelet_network.lanelets)}")
print(f"  Intersections: {len(scenario.lanelet_network.intersections)}")
print(f"  Traffic signs: {len(scenario.lanelet_network.traffic_signs)}")
print(f"  Traffic lights: {len(scenario.lanelet_network.traffic_lights)}")

# Step 2: Write CommonRoad XML file
print(f"\n[2/2] Saving intermediate CommonRoad XML...")

writer = CommonRoadFileWriter(
    scenario=scenario,
    planning_problem_set=PlanningProblemSet(),
    affiliation="University of Michigan",
    author="creator",
    tags={Tag.URBAN},
    source="CommonRoad Scenario Designer"
)
writer.write_to_file(args.cr_file, OverwriteExistingFile.ALWAYS)
print(f"  → Saved: {args.cr_file}")

#!/usr/bin/env python3
"""
Convert OSM to Lanelet2 via CommonRoad
For Michigan Stadium area
"""

import argparse
from pathlib import Path

from commonroad.common.file_reader import CommonRoadFileReader
from crdesigner.map_conversion.lanelet2.cr2lanelet import CR2LaneletConverter
from crdesigner.common.config.lanelet2_config import Lanelet2Config
import xml.etree.ElementTree as ET

parser = argparse.ArgumentParser()
parser.add_argument("--cr-file", type=str, default="example/map_cr.xml", help="Path to the input CommonRoad XML file")
parser.add_argument("--lanelet2-file", type=str, default="example/map_lanelet2.osm", help="Path to the output Lanelet2 OSM file")
args = parser.parse_args()

output_path = Path(args.lanelet2_file)
if not output_path.parent.exists():
    output_path.parent.mkdir(parents=True, exist_ok=True)

# Step 3: Convert CommonRoad to Lanelet2
print(f"Converting to Lanelet2 format...")

# Reload the scenario
scenario_reloaded, _ = CommonRoadFileReader(args.cr_file).open()

# Configure Lanelet2 conversion
l2_config = Lanelet2Config()
l2_config.use_local_coordinates = False  # Use global UTM coordinates
l2_config.left_driving = False  # Right-hand traffic (US)
l2_config.translate = False  # Don't translate coordinates

print(f"  → Configuration:")
print(f"     - Use local coordinates: {l2_config.use_local_coordinates}")
print(f"     - Left driving: {l2_config.left_driving}")
print(f"     - Translate: {l2_config.translate}")

# Create converter with proper config
converter = CR2LaneletConverter(config=l2_config)

# Convert - returns an OSM XML element
lanelet2_osm = converter(scenario_reloaded)

# Write the OSM XML to file
tree = ET.ElementTree(lanelet2_osm)
ET.indent(tree, space="  ")  # Pretty print
tree.write(args.lanelet2_file, encoding="utf-8", xml_declaration=True)

print(f"\n{'='*70}")
print(f"✓ SUCCESS!")
print(f"{'='*70}")
print(f"Lanelet2 map saved to: {args.lanelet2_file}")

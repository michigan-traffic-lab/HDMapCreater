import json
import os
import math
from enum import Enum
import requests
from PIL import Image
from io import BytesIO
from collections import defaultdict
from typing import Dict, List
import numpy as np

from lanelet2.core import LaneletMap
from lanelet2.io import Origin, load
from lanelet2.projection import UtmProjector
from lanelet2.core import BasicPoint2d, TrafficLight

from map.lanelet_naming import name_all_lanelets


class LaneShape(Enum):
    """
    Enum for different types of lane shape.
    """
    STRAIGHT = 'straight'
    LEFT_TURN = 'left-turn'
    RIGHT_TURN = 'right-turn'
    U_TURN = 'u-turn'


class LaneletRelationships:
    """Stores prebuilt relationships for a single lanelet."""

    def __init__(self, lanelet_id: int):
        self.lanelet_id = lanelet_id
        self.left_neighbors: List[int] = []
        self.right_neighbors: List[int] = []
        self.successors: List[int] = []
        self.predecessors: List[int] = []

    def __repr__(self):
        return (f"LaneletRelationships(id={self.lanelet_id}, "
                f"left={self.left_neighbors}, right={self.right_neighbors}, "
                f"succ={self.successors}, pred={self.predecessors})")


class Map():
    def __init__(self, base_map: LaneletMap = None, map_configs = None, background_img=None, origin_projector=None):
        super().__init__()
        self._base_map = base_map
        self.name = map_configs.get("name", "default_map") if map_configs else "default_map"
        self.origin_projector = origin_projector
        self.approaches = map_configs.get("approaches", {}) if map_configs else {}
        self.corner_coords = map_configs.get("corner_coords", {}) if map_configs else {}
        self.traffic_light_info = {}
        self.background_img = background_img

        # Lanelet shape/maneuver information (will be populated later)
        self.lanelet_shapes = {}  # lanelet_id -> LaneShape

        # Prebuilt lane relationships for efficient access
        self.relationships: Dict[int, LaneletRelationships] = {}
        self.lanelet_names: Dict[int, str] = {}  # lanelet_id -> name (to be populated later)
        self.left_turn_routes, self.right_turn_routes = [], []
        self.intersection_range = {}

    def get_left_neighbors(self, lanelet_id: int) -> List[int]:
        """Get lanelet IDs to the left of the given lanelet."""
        if lanelet_id not in self.relationships:
            return []
        return self.relationships[lanelet_id].left_neighbors

    def get_right_neighbors(self, lanelet_id: int) -> List[int]:
        """Get lanelet IDs to the right of the given lanelet."""
        if lanelet_id not in self.relationships:
            return []
        return self.relationships[lanelet_id].right_neighbors

    def get_successors(self, lanelet_id: int) -> List[int]:
        """Get lanelet IDs that follow the given lanelet."""
        if lanelet_id not in self.relationships:
            return []
        return self.relationships[lanelet_id].successors

    def get_predecessors(self, lanelet_id: int) -> List[int]:
        """Get lanelet IDs that precede the given lanelet."""
        if lanelet_id not in self.relationships:
            return []
        return self.relationships[lanelet_id].predecessors

    # optionally forward attribute access to the base map
    def __getattr__(self, name):
        return getattr(self._base_map, name) if self._base_map else None

    def base_map(self):
        return self._base_map


def load_map(path, google_maps_api_key='', zoom=19):
    config_file = f'{path}/configs.json'
    background_file = f'{path}/background.png'
    lanelet2_file = f'{path}/lanelet2.osm'

    if not os.path.exists(config_file):
        origin = Origin(lat=42.279913, lon=-83.732777)
        origin_projector = UtmProjector(origin)  # uses correct UTM zone for origin
        map_obj = Map(origin_projector=origin_projector)
        return map_obj

    with open(config_file, "r") as f:
        map_configs = json.load(f)

    if map_configs['origin']['lat'] == 0 and map_configs['origin']['lon'] == 0:
        print(f"Map center coordinates not set. Please update the 'origin' field in {path}/configs.json with valid latitude and longitude values.")
        return None

    if os.path.exists(background_file):
        background_img = Image.open(background_file)
    else:
        if google_maps_api_key:
            background_img, corner_coords = get_background_figure_from_google_maps(map_configs['origin']['lat'], map_configs['origin']['lon'], zoom, (640, 640), 'satellite', google_maps_api_key, path)
        else:
            background_img, corner_coords = None, {}

        map_configs.update({"corner_coords": corner_coords})
        with open(f"{path}/configs.json", "w") as f:
            json.dump(map_configs, f, indent=4)

    origin = Origin(lat=map_configs['origin']['lat'], lon=map_configs['origin']['lon'])
    origin_projector = UtmProjector(origin)  # uses correct UTM zone for origin
    if os.path.exists(lanelet2_file):
        map_obj = load(lanelet2_file, origin_projector)
    else:
        map_obj = Map(None, map_configs, background_img, origin_projector)
        return map_obj

    map_obj = Map(map_obj, map_configs, background_img, origin_projector)

    map_obj = adjust_map(map_obj, map_configs['origin'].get('rotation', 0), map_configs['origin'].get('x_offset', 0), map_configs['origin'].get('y_offset', 0))
    map_obj = build_relationships(map_obj)
    map_obj = load_lanelet_shapes(map_obj)
    map_obj = name_all_lanelets(map_obj, num_directions=4)
    map_obj = load_traffic_light_info(map_obj)

    return map_obj


def get_background_figure_from_google_maps(
        center_lat,
        center_lng,
        zoom,  # Zoom level (0-21+)
        img_size,  # Width x Height in pixels
        maptype,  # roadmap, satellite, hybrid, terrain
        api_key='',
        path='.'):
    """
    Fetches a static map image from Google Maps API based on predefined parameters.
    Returns the image object.
    """
    # Fetch the static map
    url = f"https://maps.googleapis.com/maps/api/staticmap?center={center_lat},{center_lng}&zoom={zoom}&size={img_size[0]}x{img_size[1]}&maptype={maptype}&key={api_key}"
    response = requests.get(url)
    img = Image.open(BytesIO(response.content))
    img.save(f"{path}/background.png")

    # Earth constants
    TILE_SIZE = 256

    def latlng_to_pixel(lat, lng, zoom):
        scale = 2 ** zoom
        siny = math.sin(math.radians(lat))
        siny = min(max(siny, -0.9999), 0.9999)
        x = TILE_SIZE * (0.5 + lng / 360.0) * scale
        y = TILE_SIZE * (0.5 - math.log((1 + siny) / (1 - siny)) / (4 * math.pi)) * scale
        return x, y

    def pixel_to_latlng(x, y, zoom):
        scale = 2 ** zoom
        lng = (x / (TILE_SIZE * scale) - 0.5) * 360.0
        lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * y / (TILE_SIZE * scale))))
        lat = math.degrees(lat_rad)
        return lat, lng

    # Center in pixels
    center_px, center_py = latlng_to_pixel(center_lat, center_lng, zoom)

    # Image pixel bounds
    w, h = img_size
    half_w, half_h = w / 2, h / 2

    # Corners in pixels
    corners_px = {
        'top_left':     (center_px - half_w, center_py - half_h),
        'top_right':    (center_px + half_w, center_py - half_h),
        'bottom_left':  (center_px - half_w, center_py + half_h),
        'bottom_right': (center_px + half_w, center_py + half_h),
    }

    # Convert pixel coords back to lat/lng
    corner_coords = {key: pixel_to_latlng(x, y, zoom) for key, (x, y) in corners_px.items()}

    return img, corner_coords


def adjust_map(map_obj, angle_degrees, x_offset=0, y_offset=0):
    angle_radians = math.radians(angle_degrees)
    cos_angle = math.cos(angle_radians)
    sin_angle = math.sin(angle_radians)

    def rotate_point(point):
        # Rotate a point around the origin (0,0) clockwise
        x_new = point.x * cos_angle - point.y * sin_angle
        y_new = point.x * sin_angle + point.y * cos_angle
        return BasicPoint2d(x_new, y_new)

    for point in map_obj.pointLayer:
        rotated_point = rotate_point(point)
        point.x = rotated_point.x + x_offset
        point.y = rotated_point.y + y_offset
    return map_obj


def build_relationships(map_obj):
    """Prebuild all lane relationships based on shared bounds and points."""

    # Step 1: Build point-to-linestring index for efficient lookups
    linestring_index = defaultdict(list)
    endpoint_index = defaultdict(list)

    for ll in map_obj.laneletLayer:
        ll_id = ll.id

        # Initialize relationship object
        map_obj.relationships[ll_id] = LaneletRelationships(ll_id)

        # Index left bound
        left_ids = tuple(pt.id for pt in ll.leftBound)
        if left_ids:
            linestring_index[left_ids].append((ll_id, 'left'))
            endpoint_index[(left_ids[0], left_ids[-1])].append((ll_id, 'left'))

        # Index right bound
        right_ids = tuple(pt.id for pt in ll.rightBound)
        if right_ids:
            linestring_index[right_ids].append((ll_id, 'right'))
            endpoint_index[(right_ids[0], right_ids[-1])].append((ll_id, 'right'))

    # Step 2: Find left/right neighbors based on shared boundaries
    for point_tuple, lanelets in linestring_index.items():
        if len(lanelets) < 2:
            continue

        for i, (ll_id_1, side_1) in enumerate(lanelets):
            for ll_id_2, side_2 in lanelets[i+1:]:
                if side_1 == 'right' and side_2 == 'left':
                    map_obj.relationships[ll_id_1].right_neighbors.append(ll_id_2)
                    map_obj.relationships[ll_id_2].left_neighbors.append(ll_id_1)
                elif side_1 == 'left' and side_2 == 'right':
                    map_obj.relationships[ll_id_1].left_neighbors.append(ll_id_2)
                    map_obj.relationships[ll_id_2].right_neighbors.append(ll_id_1)

    # Step 3: Find successors/predecessors based on connected endpoints
    for ll in map_obj._base_map.laneletLayer:
        ll_id = ll.id

        if not ll.leftBound or not ll.rightBound:
            continue

        left_end = ll.leftBound[-1].id
        right_end = ll.rightBound[-1].id

        for other_ll in map_obj._base_map.laneletLayer:
            if other_ll.id == ll_id:
                continue

            if not other_ll.leftBound or not other_ll.rightBound:
                continue

            other_left_start = other_ll.leftBound[0].id
            other_right_start = other_ll.rightBound[0].id

            if (left_end == other_left_start and right_end == other_right_start):
                map_obj.relationships[ll_id].successors.append(other_ll.id)
                map_obj.relationships[other_ll.id].predecessors.append(ll_id)
    return map_obj


def load_lanelet_shapes(map_obj):
    """
    Load lane shapes from the lanelet2 map by reading 'turn_direction' attributes.
    Populates map_obj.lanelet_shapes dictionary.

    Args:
        map_obj: Map object with laneletLayer

    Returns:
        map_obj with populated lanelet_shapes
    """
    # Iterate through all lanelets in the map
    for lanelet in map_obj.laneletLayer:
        # Check if this lanelet has a 'turn_direction' attribute
        if lanelet.attributes['subtype'] in ['intersection', 'roundabout', 'enter', 'exit'] and 'turn_direction' in lanelet.attributes:
            turn_direction = lanelet.attributes['turn_direction'].lower()
            if turn_direction != 'straight':
                turn_direction += '-turn'
            map_obj.lanelet_shapes[lanelet.id] = LaneShape(turn_direction)
        else:
            map_obj.lanelet_shapes[lanelet.id] = LaneShape.STRAIGHT

    return map_obj


def load_traffic_light_info(map_obj):
    """Build a dictionary mapping point IDs to lanelets"""
    traffic_light_info = {}
    lanelet_controlled_by_regelem_dict = defaultdict(list)
    for lanelet in map_obj.laneletLayer:
        if not lanelet.regulatoryElements:
            continue
        for regelem in lanelet.regulatoryElements:
            if not isinstance(regelem, TrafficLight):
                continue
            lanelet_controlled_by_regelem_dict[regelem.id].append(lanelet)
    for regelem in map_obj.regulatoryElementLayer:
        if regelem.id not in lanelet_controlled_by_regelem_dict:
            continue
        controlled_lanelet_names = [map_obj.lanelet_names[lanelet.id] for lanelet in lanelet_controlled_by_regelem_dict[regelem.id] if lanelet.id in map_obj.lanelet_names]
        if not controlled_lanelet_names:
            continue
        heading = controlled_lanelet_names[0].split('-')[0]
        movements = set(name.split('-')[1].split('_')[0] for name in controlled_lanelet_names)
        if len(movements) == 1:
            movement = movements.pop()
        else:
            # if multiple lanelets with different movements are controlled by the same traffic light, we prioritize straight > left > right for naming
            if 'Straight' in movements:
                movement = 'Straight'
            elif 'Left' in movements:
                movement = 'Left'
            elif 'Right' in movements:
                movement = 'Right'
            else:
                movement = controlled_lanelet_names[0].split('-')[1].split('_')[0]
        if heading + movement in traffic_light_info:
            continue
        linestring = regelem.trafficLights[0]
        traffic_light_info[heading + movement] = {
            "left_bottom_corner": [linestring[0].x, linestring[0].y],
            "length": math.sqrt((linestring[1].x - linestring[0].x)**2 + (linestring[1].y - linestring[0].y)**2),
            "height": 1,
            "rotation": np.degrees(math.atan2(linestring[1].y - linestring[0].y, linestring[1].x - linestring[0].x))
        }

    map_obj.traffic_light_info = traffic_light_info
    return map_obj

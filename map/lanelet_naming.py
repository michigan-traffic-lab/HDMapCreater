from enum import Enum
import numpy as np
from lanelet2 import geometry
from typing import Dict, List, Tuple
from collections import defaultdict


class LaneShape(Enum):
    """
    Enum for different types of lane shape.
    """
    STRAIGHT = 'straight'
    LEFT_TURN = 'left-turn'
    RIGHT_TURN = 'right-turn'
    U_TURN = 'u-turn'


def get_lanelet_heading(lanelet) -> float:
    """
    Get the heading of a lanelet at its midpoint.
    
    Args:
        lanelet: Lanelet object
        
    Returns:
        heading in radians (-π to π)
    """
    try:
        p1 = lanelet.centerline[0]
        p2 = lanelet.centerline[1]
        
        heading = np.arctan2(p2.y - p1.y, p2.x - p1.x)
        return heading
        
    except Exception as e:
        print(f"Warning: Failed to get heading for lanelet {lanelet.id}: {e}")
        # Fallback: use first two points
        if len(lanelet.centerline) >= 2:
            p1 = lanelet.centerline[0]
            p2 = lanelet.centerline[1]
            return np.arctan2(p2.y - p1.y, p2.x - p1.x)
        return 0.0


def heading_to_direction(heading_rad: float, num_directions: int = 8) -> str:
    """
    Convert heading in radians to cardinal/intercardinal direction.
    
    Args:
        heading_rad: heading in radians (-π to π)
        num_directions: Number of directions to use (4, 8, or 16)
                       4: N, E, S, W
                       8: N, NE, E, SE, S, SW, W, NW
                       16: N, NNE, NE, ENE, E, ESE, SE, SSE, S, SSW, SW, WSW, W, WNW, NW, NNW
        
    Returns:
        Direction string with 'bound' suffix (e.g., 'Northbound', 'Northeastbound')
    """
    # Convert to degrees [0, 360)
    heading_deg = np.degrees(heading_rad) % 360
    
    if num_directions == 4:
        # 4 directions: N, E, S, W (90° each)
        directions = ['Eastbound', 'Northbound', 'Westbound', 'Southbound']
        sector_size = 90.0
        idx = int((heading_deg + sector_size / 2) / sector_size) % 4
        return directions[idx]
    
    elif num_directions == 8:
        # 8 directions: N, NE, E, SE, S, SW, W, NW (45° each)
        directions = [
            'Eastbound',       # 0°
            'Northeastbound',  # 45°
            'Northbound',      # 90°
            'Northwestbound',  # 135°
            'Westbound',       # 180°
            'Southwestbound',  # 225°
            'Southbound',      # 270°
            'Southeastbound',  # 315°
        ]
        sector_size = 45.0
        idx = int((heading_deg + sector_size / 2) / sector_size) % 8
        return directions[idx]
    
    elif num_directions == 16:
        # 16 directions (22.5° each)
        directions = [
            'Eastbound',           # 0°
            'Eastnortheastbound',  # 22.5°
            'Northeastbound',      # 45°
            'Northnortheastbound', # 67.5°
            'Northbound',          # 90°
            'Northnorthwestbound', # 112.5°
            'Northwestbound',      # 135°
            'Westnorthwestbound',  # 157.5°
            'Westbound',           # 180°
            'Westsouthwestbound',  # 202.5°
            'Southwestbound',      # 225°
            'Southsouthwestbound', # 247.5°
            'Southbound',          # 270°
            'Southsoutheastbound', # 292.5°
            'Southeastbound',      # 315°
            'Eastsoutheastbound',  # 337.5°
        ]
        sector_size = 22.5
        idx = int((heading_deg + sector_size / 2) / sector_size) % 16
        return directions[idx]
    
    else:
        raise ValueError(f"num_directions must be 4, 8, or 16, got {num_directions}")


def format_lane_shape(lane_shape: LaneShape) -> str:
    """
    Format LaneShape enum value for use in lanelet names.
    Converts 'left-turn' -> 'Left_Turn', 'straight' -> 'Straight', etc.
    """
    # Get the enum value (e.g., 'left-turn', 'straight')
    value = lane_shape.value
    # Replace hyphens with underscores and title case each word
    return '_'.join(word.capitalize() for word in value.split('-'))


def propagate_turn_types(map_obj) -> Dict[int, LaneShape]:
    """
    Propagate turn types from successors to predecessors using existing relationships.
    
    Rules:
    - If a STRAIGHT lanelet's successors only contain LEFT_TURN, mark it as LEFT_TURN
    - If a STRAIGHT lanelet's successors only contain RIGHT_TURN, mark it as RIGHT_TURN
    - If a STRAIGHT lanelet has both STRAIGHT and turn successors, keep it STRAIGHT
    
    Args:
        map_obj: Map object with lanelet_shapes and relationships already built
        
    Returns:
        Updated dictionary of lanelet_id -> LaneShape
    """
    # Start with existing shapes from the map
    lane_shapes = dict(map_obj.lanelet_shapes)
    
    # Add STRAIGHT as default for lanelets without explicit shape
    for lanelet in map_obj.laneletLayer:
        if lanelet.id not in lane_shapes:
            lane_shapes[lanelet.id] = LaneShape.STRAIGHT
    
    # Iteratively propagate turn types backwards
    changed = True
    max_iterations = 10  # Prevent infinite loops
    iteration = 0
    
    while changed and iteration < max_iterations:
        changed = False
        iteration += 1
        
        for lanelet_id, shape in list(lane_shapes.items()):
            # Only propagate for currently STRAIGHT lanelets
            if shape != LaneShape.STRAIGHT:
                continue
            
            # Get successors using existing relationships
            successor_ids = map_obj.get_successors(lanelet_id)
            if not successor_ids:
                continue
            
            # Get shapes of successors
            successor_shapes = [lane_shapes.get(sid, LaneShape.STRAIGHT) 
                              for sid in successor_ids]
            
            # Check if all successors are the same turn type
            unique_shapes = set(successor_shapes)
            
            # If all successors are LEFT_TURN (and no STRAIGHT)
            if unique_shapes == {LaneShape.LEFT_TURN}:
                lane_shapes[lanelet_id] = LaneShape.LEFT_TURN
                changed = True
            
            # If all successors are RIGHT_TURN (and no STRAIGHT)
            elif unique_shapes == {LaneShape.RIGHT_TURN}:
                lane_shapes[lanelet_id] = LaneShape.RIGHT_TURN
                changed = True
            
            # If all successors are U_TURN (and no STRAIGHT)
            elif unique_shapes == {LaneShape.U_TURN}:
                lane_shapes[lanelet_id] = LaneShape.U_TURN
                changed = True
    
    return lane_shapes


def get_rightmost_point(lanelet) -> float:
    """
    Get a metric for the rightmost position of a lanelet.
    This uses the right bound's average position.
    
    Args:
        lanelet: Lanelet object
        
    Returns:
        A position metric (for sorting)
    """
    # Get the midpoint of the right bound
    if len(lanelet.rightBound) == 0:
        return 0.0
    
    mid_idx = len(lanelet.rightBound) // 2
    mid_point = lanelet.rightBound[mid_idx]
    
    # Return x, y as tuple for potential 2D sorting
    return (mid_point.x, mid_point.y)


def sort_lanes_right_to_left(lanelet_ids: List[int], map_obj, direction: str) -> List[int]:
    """
    Sort lanelets from right to left based on their direction of travel.
    
    Args:
        lanelet_ids: List of lanelet IDs to sort
        map_obj: Map object
        direction: Direction string (e.g., 'Northbound', 'Northeastbound', 'Northnortheastbound')
        
    Returns:
        Sorted list of lanelet IDs (rightmost first)
    """
    # Get lanelets
    lanelets = []
    for ll_id in lanelet_ids:
        for ll in map_obj.laneletLayer:
            if ll.id == ll_id:
                lanelets.append(ll)
                break
    
    if not lanelets:
        return lanelet_ids
    
    # Extract primary and secondary directions from the direction string
    # Examples: 'Northbound' -> primary='North', secondary=None
    #           'Northeastbound' -> primary='North', secondary='East'
    #           'Northnortheastbound' -> primary='North', secondary='East' (more north than east)
    direction_lower = direction.lower().replace('bound', '')
    
    # Determine the dominant direction(s)
    has_north = 'north' in direction_lower
    has_south = 'south' in direction_lower
    has_east = 'east' in direction_lower
    has_west = 'west' in direction_lower
    
    def get_sort_key(lanelet):
        # Use the midpoint of the lanelet's right bound
        if len(lanelet.rightBound) > 0:
            mid_idx = len(lanelet.rightBound) // 2
            point = lanelet.rightBound[mid_idx]
        else:
            # Fallback to centerline
            mid_idx = len(lanelet.centerline) // 2
            point = lanelet.centerline[mid_idx]
        
        # Determine sort order based on primary direction
        # Pure cardinal directions
        if has_north and not has_south and not has_east and not has_west:
            # Pure Northbound: right = smaller x
            return point.x
        elif has_south and not has_north and not has_east and not has_west:
            # Pure Southbound: right = larger x
            return -point.x
        elif has_east and not has_north and not has_south and not has_west:
            # Pure Eastbound: right = smaller y
            return point.y
        elif has_west and not has_north and not has_south and not has_east:
            # Pure Westbound: right = larger y
            return -point.y
        
        # Diagonal directions (intercardinal and secondary intercardinal)
        elif has_north and has_east:
            # Northeast quadrant: right = smaller (x - y)
            # More north -> more weight on x, more east -> more weight on -y
            return point.x - point.y
        elif has_north and has_west:
            # Northwest quadrant: right = smaller (x + y)
            return point.x + point.y
        elif has_south and has_east:
            # Southeast quadrant: right = larger (x + y)
            return -(point.x + point.y)
        elif has_south and has_west:
            # Southwest quadrant: right = larger (x - y)
            return -(point.x - point.y)
        else:
            # Fallback
            return point.x
    
    # Sort lanelets
    sorted_lanelets = sorted(lanelets, key=get_sort_key)
    
    # Return sorted IDs
    return [ll.id for ll in sorted_lanelets]


def name_all_lanelets(map_obj, num_directions: int = 4) -> Dict[int, str]:
    """
    Generate names for all lanelets in the format: Direction-TurnType-Number
    Example: 'Northbound-Left_Turn-1', 'Southbound-Straight-2'
    
    Args:
        map_obj: Map object with lanelet_shapes and relationships already built
        num_directions: Number of directions to use (4, 8, or 16)
                       4: N, E, S, W
                       8: N, NE, E, SE, S, SW, W, NW (default)
                       16: N, NNE, NE, ENE, E, ESE, SE, SSE, S, SSW, SW, WSW, W, WNW, NW, NNW
        
    Returns:
        Dictionary mapping lanelet_id -> name string
    """
    # Step 1: Propagate turn types based on successors
    lane_shapes = propagate_turn_types(map_obj)
    
    # Step 2: Calculate heading for each lanelet
    lanelet_headings = {}
    for lanelet in map_obj.laneletLayer:
        heading = get_lanelet_heading(lanelet)
        lanelet_headings[lanelet.id] = heading
    
    # Step 3: Group lanelets by direction and turn type
    lanelet_info = {}  # lanelet_id -> (direction, turn_type)
    
    for lanelet in map_obj.laneletLayer:
        ll_id = lanelet.id
        heading = lanelet_headings[ll_id]
        direction = heading_to_direction(heading, num_directions)
        if lanelet.attributes['subtype'] == 'intersection':
            turn_type = lane_shapes.get(ll_id, LaneShape.STRAIGHT)
        else:
            successors = map_obj.get_successors(ll_id)
            successors_shapes = set([lane_shapes.get(sid, LaneShape.STRAIGHT) for sid in successors])
            if LaneShape.STRAIGHT in successors_shapes:
                turn_type = LaneShape.STRAIGHT
            elif len(successors_shapes) > 1:
                turn_type = LaneShape.STRAIGHT
            elif len(successors_shapes) == 0:
                turn_type = lane_shapes.get(ll_id, LaneShape.STRAIGHT)
            else:
                turn_type = list(successors_shapes)[0]
        turn_type_str = format_lane_shape(turn_type)
        
        lanelet_info[ll_id] = (direction, turn_type_str)
    
    # Step 4: For each group, sort from right to left and assign numbers
    lanelet_names = {}
    approach_groups = defaultdict(set)  # direction -> set of lanelet_ids leading to intersections
    departure_groups = defaultdict(set)  # direction -> set of lanelet_ids leading away from intersections

    def _get_successive_lanelets(lanelet_id):
        successors = map_obj.get_successors(lanelet_id)
        all_successors = set(successors)
        for succ_id in successors:
            all_successors.update(_get_successive_lanelets(succ_id))
        return all_successors
    
    for ll_id, (direction, turn_type) in lanelet_info.items():
        # Count how many right neighbors have the same direction and movement
        # Number = count of right neighbors + 1 (this lanelet itself)
        count = 0
        current_id = ll_id
        
        # Keep checking right neighbors
        while True:
            right_neighbors = map_obj.get_right_neighbors(current_id)
            
            # Find right neighbor with same direction and movement
            found_right = False
            for right_id in right_neighbors:
                if right_id in lanelet_info:
                    right_dir, right_turn = lanelet_info[right_id]
                    if right_dir == direction and right_turn == turn_type:
                        count += 1
                        current_id = right_id
                        found_right = True
                        break
            
            if not found_right:
                break
        
        # Number is: count of right neighbors + 1
        number = count + 1
        name = f"{direction}-{turn_type}-{number}"
        lanelet_names[ll_id] = name

        if map_obj.laneletLayer.get(ll_id).attributes['subtype'] not in ['intersection', 'crosswalk']:
            # Get successive lanelets list recursively
            approach = False
            for succ_id in _get_successive_lanelets(ll_id):
                if map_obj.laneletLayer.get(succ_id).attributes['subtype'] == 'intersection':
                    approach = True
            if approach:
                approach_groups[direction].add(ll_id)
            else:
                departure_groups[direction].add(ll_id)
    map_obj.lanelet_names = lanelet_names
    map_obj.approach_groups = approach_groups
    map_obj.departure_groups = departure_groups

    return map_obj

import argparse
import matplotlib.pyplot as plt
from typing import Tuple, List
from lanelet2.core import GPSPoint

from map.map import load_map
from visualization.config import render_config
from visualization.config.style_config import StyleConfig
from visualization.plotting import plot_map, plot_traffic_lights


def determine_xy_lim(map_obj) -> Tuple[List[float], List[float]]:
    """
    Determine x and y axis limits from map object.
    
    Args:
        map_obj: Map object with background_img and corner_coords
        
    Returns:
        (xlim, ylim) where xlim = [xmin, xmax], ylim = [ymin, ymax]
        Returns ([], []) if no background image available
    """
    if map_obj.background_img is not None and map_obj.corner_coords:
        try:
            top_left = map_obj.origin_projector.forward(
                GPSPoint(
                    map_obj.corner_coords['top_left'][0],
                    map_obj.corner_coords['top_left'][1]
                )
            )
            top_right = map_obj.origin_projector.forward(
                GPSPoint(
                    map_obj.corner_coords['top_right'][0],
                    map_obj.corner_coords['top_right'][1]
                )
            )
            bottom_right = map_obj.origin_projector.forward(
                GPSPoint(
                    map_obj.corner_coords['bottom_right'][0],
                    map_obj.corner_coords['bottom_right'][1]
                )
            )
            bottom_left = map_obj.origin_projector.forward(
                GPSPoint(
                    map_obj.corner_coords['bottom_left'][0],
                    map_obj.corner_coords['bottom_left'][1]
                )
            )
            xlim = [max(top_left.x, bottom_left.x), min(top_right.x, bottom_right.x)]
            ylim = [max(bottom_left.y, bottom_right.y), min(top_left.y, top_right.y)]
            
            return xlim, ylim, {
                'top_left': (top_left.x, top_left.y),
                'top_right': (top_right.x, top_right.y),
                'bottom_right': (bottom_right.x, bottom_right.y),
                'bottom_left': (bottom_left.x, bottom_left.y)
            }
        except Exception as e:
            print(f"Warning: Failed to calculate xy limits from map: {e}")
            return [], [], {}
    
    return [], [], {}


parser = argparse.ArgumentParser()
parser.add_argument("--map-path", type=str, default="example/fuller_huronPkwy", help="Path to the lanelet2 file")
parser.add_argument("--google-maps-api-key", type=str, default="", help="Google Maps API key for fetching satellite imagery")
parser.add_argument("--output-file", type=str, default="example/fuller_huronPkwy.png", help="Path to save the plotted map image")
args = parser.parse_args()

# Load the lanelet2 map
map_obj = load_map(args.map_path, google_maps_api_key=args.google_maps_api_key)

style = StyleConfig(
    map_alpha=0.8,
    lanelet_intersection_color=(0.5, 0.5, 1.0),   # light blue
    lanelet_left_turn_color=(1.0, 0.5, 0.0),       # orange
    lanelet_right_turn_color=(0.0, 0.8, 0.4),      # green
    lanelet_crosswalk_color=(0.8, 0.8, 0.0),       # yellow
)

fig, ax = plt.subplots(figsize=(6, 6))
xlim, ylim, background_corners = determine_xy_lim(map_obj)
plot_map(ax, map_obj, extent=xlim + ylim, background_corners=background_corners, style=style)
plot_traffic_lights(ax, map_obj, style=style)
plt.xlim(xlim)
plt.ylim(ylim)
plt.tight_layout()
plt.savefig(args.output_file)

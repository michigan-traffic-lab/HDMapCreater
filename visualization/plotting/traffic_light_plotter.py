"""
Traffic element plotting (traffic lights, signs, etc).
"""
from matplotlib.patches import Rectangle
from typing import Dict, Optional

from ..config import StyleConfig


def plot_traffic_lights(
    ax,
    map_obj,
    trajectory_manager=None,
    frame_step: int = 0,
    style: Optional[StyleConfig] = None
):
    """
    Plot traffic light indicators.
    
    Args:
        ax: Matplotlib axis
        map_obj: Map object with traffic_light_info attribute
        trajectory_manager: TrajectoryManager
        frame_step: Frame index
        style: StyleConfig for default colors
    """
    if style is None:
        style = StyleConfig()
    
    # Check if map has traffic light info
    if not hasattr(map_obj, 'traffic_light_info'):
        return
    
    if trajectory_manager is None or not hasattr(trajectory_manager.step_to_frame_map[frame_step], 'spat'):
        traffic_light_phase = {}
    else:
        traffic_light_phase = trajectory_manager.step_to_frame_map[frame_step].spat
    
    # Plot each traffic light
    for traffic_light_name, traffic_light_geometry in map_obj.traffic_light_info.items():
        # Determine color and alpha
        if traffic_light_name in traffic_light_phase:
            color = traffic_light_phase[traffic_light_name] if traffic_light_phase[traffic_light_name] != 'flashing y' else 'y'
            alpha = 1.0
        else:
            color = style.traffic_light_default_color
            alpha = style.traffic_light_default_alpha
        
        # Create rectangle patch
        rect = Rectangle(
            traffic_light_geometry['left_bottom_corner'],
            traffic_light_geometry['length'],
            traffic_light_geometry['height'],
            angle=traffic_light_geometry['rotation'],
            facecolor=color,
            edgecolor='none',
            linewidth=0,
            alpha=alpha
        )
        
        ax.add_patch(rect)

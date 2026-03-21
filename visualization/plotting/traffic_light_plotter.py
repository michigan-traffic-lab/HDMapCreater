"""
Traffic element plotting (traffic lights, signs, etc).
"""
from matplotlib.patches import Rectangle
from typing import Dict, Optional

from ..config import StyleConfig, RenderConfig

# Map spat phase strings to StyleConfig color attribute names
_PHASE_COLOR_MAP = {
    'r': 'traffic_light_red_color',
    'g': 'traffic_light_green_color',
    'y': 'traffic_light_yellow_color',
}


def plot_traffic_lights(
    ax,
    map_obj,
    trajectory_manager=None,
    frame_step: int = 0,
    style: Optional[StyleConfig] = None,
    render_config: Optional[RenderConfig] = None,
    is_video: bool = False,
    flashing_yellow_start: Optional[Dict[str, int]] = None
):
    """
    Plot traffic light indicators.

    Args:
        ax: Matplotlib axis
        map_obj: Map object with traffic_light_info attribute
        trajectory_manager: TrajectoryManager
        frame_step: Frame index
        style: StyleConfig for default colors
        render_config: RenderConfig for flashing yellow frequency
        is_video: Whether this is being rendered as part of a video
        flashing_yellow_start: Dict tracking the start frame of each
            traffic light's current flashing yellow run. Mutated in place.
    """
    if style is None:
        style = StyleConfig()
    if render_config is None:
        render_config = RenderConfig()

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
            phase = traffic_light_phase[traffic_light_name]
            if phase == 'flashing y':
                if is_video and flashing_yellow_start is not None:
                    # Record the start frame of this flashing yellow run
                    if traffic_light_name not in flashing_yellow_start:
                        flashing_yellow_start[traffic_light_name] = frame_step

                    # Alternate relative to the start of this run
                    elapsed = frame_step - flashing_yellow_start[traffic_light_name]
                    freq = render_config.flashing_yellow_frequency
                    if (elapsed // freq) % 2 == 0:
                        color = style.traffic_light_yellow_color
                        alpha = 1.0
                    else:
                        color = style.traffic_light_flashing_yellow_off_color
                        alpha = 1.0
                else:
                    # Single frame: show as static yellow
                    color = style.traffic_light_yellow_color
                    alpha = 1.0
            else:
                color = getattr(style, _PHASE_COLOR_MAP.get(phase, ''), phase)
                alpha = 1.0
                # Phase is no longer flashing yellow, clear the start tracker
                if flashing_yellow_start is not None and traffic_light_name in flashing_yellow_start:
                    del flashing_yellow_start[traffic_light_name]
        else:
            color = style.traffic_light_default_color
            alpha = style.traffic_light_default_alpha
            # Not active, clear the start tracker
            if flashing_yellow_start is not None and traffic_light_name in flashing_yellow_start:
                del flashing_yellow_start[traffic_light_name]
        
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

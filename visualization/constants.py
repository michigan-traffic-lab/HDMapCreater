"""
Constants and default values for visualization.
"""
from typing import Tuple

# ============================================================================
# Colors (RGB tuples, values 0-1)
# ============================================================================
MAP_COLOR: Tuple[float, float, float] = (0, 0, 0)  # Black
LANELET_INTERSECTION_COLOR: Tuple[float, float, float] = (0.1, 0.3, 1.0)   # Blue
LANELET_LEFT_TURN_COLOR: Tuple[float, float, float] = (1.0, 0.45, 0.0)    # Orange
LANELET_RIGHT_TURN_COLOR: Tuple[float, float, float] = (0.0, 0.75, 0.2)   # Green
LANELET_CROSSWALK_COLOR: Tuple[float, float, float] = (1.0, 0.85, 0.0)    # Yellow
ROADUSER_COLOR: Tuple[float, float, float] = (0, 1, 0)  # Green
HIGHLIGHT_COLOR: Tuple[float, float, float] = (1, 0, 0)  # Red
HIST_TRAJ_COLOR: Tuple[float, float, float] = (0, 0, 0)  # Black
FUTURE_TRAJ_COLOR: Tuple[float, float, float] = (0, 0, 1)  # Blue
PRED_TRAJ_COLOR: Tuple[float, float, float] = (0, 1, 0)  # Green
ARROW_COLOR: Tuple[float, float, float] = (0, 0, 0)  # Black
TRAFFIC_LIGHT_RED_COLOR: Tuple[float, float, float] = (1, 0, 0)  # Red
TRAFFIC_LIGHT_YELLOW_COLOR: Tuple[float, float, float] = (1.0, 0.843, 0.0)  # Gold
TRAFFIC_LIGHT_GREEN_COLOR: Tuple[float, float, float] = (0, 1, 0)  # Green
TRAFFIC_LIGHT_FLASHING_YELLOW_OFF_COLOR: Tuple[float, float, float] = (0.4, 0.337, 0.0)  # Dimmed gold
TRAFFIC_LIGHT_DEFAULT_COLOR: Tuple[float, float, float] = (1, 1, 1)  # White
INTERSECTION_AREA_COLOR: Tuple[float, float, float] = (1, 0, 0)  # Red

# ============================================================================
# Alpha values (transparency, 0-1)
# ============================================================================
MAP_ALPHA: float = 0.3
FUTURE_TRAJ_ALPHA: float = 0.5
TRAFFIC_LIGHT_DEFAULT_ALPHA: float = 0.5
INTERSECTION_AREA_ALPHA: float = 0.7

# ============================================================================
# Sizes and dimensions
# ============================================================================
ARROW_WIDTH: float = 0.8
ARROW_LENGTH: float = 1.0
HEADING_ARROW_LENGTH: float = 1.0
MARKER_SIZE: float = 1.0
LINE_WIDTH: float = 1.0
TEXT_FONTSIZE: int = 8

# ============================================================================
# Figure defaults
# ============================================================================
DEFAULT_FIGSIZE: Tuple[float, float] = (6.4, 6.4)
DEFAULT_DPI: int = 100
DEFAULT_FPS: int = 10
DEFAULT_FONTSIZE: int = 12

# ============================================================================
# Font settings
# ============================================================================
FONT_FAMILY: str = "serif"
FONT_SERIF: Tuple[str, ...] = ("Times", "DejaVu Serif", "Georgia")

# ============================================================================
# Trajectory defaults
# ============================================================================
DEFAULT_HIST_TRAJ_LEN: int = 20
DEFAULT_FUTURE_TRAJ_LEN: int = 50
DEFAULT_PRED_TRAJ_LEN: int = 50

# ============================================================================
# Video encoding defaults
# ============================================================================
DEFAULT_VIDEO_CODEC: str = "libx264"
DEFAULT_VIDEO_FORMAT: str = "mp4"
DEFAULT_VIDEO_PARAMS: list[str] = ["-pix_fmt", "yuv420p"]

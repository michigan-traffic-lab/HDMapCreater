"""
Constants and default values for visualization.
"""
from typing import Tuple

# ============================================================================
# Colors (RGB tuples, values 0-1)
# ============================================================================
MAP_COLOR: Tuple[float, float, float] = (0, 0, 0)  # Black
ROADUSER_COLOR: Tuple[float, float, float] = (0, 1, 0)  # Green
HIGHLIGHT_COLOR: Tuple[float, float, float] = (1, 0, 0)  # Red
HIST_TRAJ_COLOR: Tuple[float, float, float] = (0, 0, 0)  # Black
FUTURE_TRAJ_COLOR: Tuple[float, float, float] = (0, 0, 1)  # Blue
PRED_TRAJ_COLOR: Tuple[float, float, float] = (0, 1, 0)  # Green
ARROW_COLOR: Tuple[float, float, float] = (0, 0, 0)  # Black
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

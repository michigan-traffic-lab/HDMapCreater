"""
Configuration for visual styling.
"""
from dataclasses import dataclass, field, asdict
from typing import Tuple, List, Dict, Any
import json

from ..constants import *


@dataclass
class StyleConfig:
    """
    Visual styling configuration for colors, sizes, and appearance.
    """
    # ========================================================================
    # Figure settings
    # ========================================================================
    figsize: Tuple[float, float] = DEFAULT_FIGSIZE
    dpi: int = DEFAULT_DPI
    show_legend: bool = False
    tight_layout: bool = True
    constrained_layout: bool = False
    file_format: str = "png"  # Options: 'png', 'jpg', 'pdf', etc.
    
    # ========================================================================
    # Colors (RGB tuples, 0-1)
    # ========================================================================
    colorful: bool = False
    map_color: Tuple[float, float, float] = MAP_COLOR
    roaduser_color: Tuple[float, float, float] = ROADUSER_COLOR
    highlight_color: Tuple[float, float, float] = HIGHLIGHT_COLOR
    hist_traj_color: Tuple[float, float, float] = HIST_TRAJ_COLOR
    future_traj_color: Tuple[float, float, float] = FUTURE_TRAJ_COLOR
    pred_traj_color: Tuple[float, float, float] = PRED_TRAJ_COLOR
    arrow_color: Tuple[float, float, float] = ARROW_COLOR
    traffic_light_red_color: Tuple[float, float, float] = TRAFFIC_LIGHT_RED_COLOR
    traffic_light_yellow_color: Tuple[float, float, float] = TRAFFIC_LIGHT_YELLOW_COLOR
    traffic_light_green_color: Tuple[float, float, float] = TRAFFIC_LIGHT_GREEN_COLOR
    traffic_light_flashing_yellow_off_color: Tuple[float, float, float] = TRAFFIC_LIGHT_FLASHING_YELLOW_OFF_COLOR
    traffic_light_default_color: Tuple[float, float, float] = TRAFFIC_LIGHT_DEFAULT_COLOR
    intersection_area_color: Tuple[float, float, float] = INTERSECTION_AREA_COLOR
    # Lanelet type colors (subtype/turn_direction based)
    lanelet_intersection_color: Tuple[float, float, float] = LANELET_INTERSECTION_COLOR
    lanelet_left_turn_color: Tuple[float, float, float] = LANELET_LEFT_TURN_COLOR
    lanelet_right_turn_color: Tuple[float, float, float] = LANELET_RIGHT_TURN_COLOR
    lanelet_crosswalk_color: Tuple[float, float, float] = LANELET_CROSSWALK_COLOR
    # set color for each roaduser
    roaduser_colors: Dict[Any, Tuple[float, float, float]] = field(default_factory=dict)
    
    # ========================================================================
    # Alpha values (transparency, 0-1)
    # ========================================================================
    map_alpha: float = MAP_ALPHA
    future_traj_alpha: float = FUTURE_TRAJ_ALPHA
    traffic_light_default_alpha: float = TRAFFIC_LIGHT_DEFAULT_ALPHA
    intersection_area_alpha: float = INTERSECTION_AREA_ALPHA
    
    # ========================================================================
    # Sizes and dimensions
    # ========================================================================
    arrow_width: float = ARROW_WIDTH
    arrow_length: float = ARROW_LENGTH
    heading_arrow_length: float = HEADING_ARROW_LENGTH
    marker_size: float = MARKER_SIZE
    line_width: float = LINE_WIDTH
    text_fontsize: int = TEXT_FONTSIZE
    
    # ========================================================================
    # Fonts
    # ========================================================================
    font_family: str = FONT_FAMILY
    font_serif: List[str] = field(default_factory=lambda: list(FONT_SERIF))
    fontsize: int = DEFAULT_FONTSIZE
    
    def __post_init__(self):
        """Validate configuration."""
        if self.dpi < 50 or self.dpi > 500:
            raise ValueError(f"DPI must be between 50 and 500, got {self.dpi}")
        
        if self.fontsize < 6 or self.fontsize > 72:
            raise ValueError(f"Fontsize must be between 6 and 72, got {self.fontsize}")

        # Validate alpha values
        for attr in ['map_alpha', 'future_traj_alpha', 'traffic_light_default_alpha']:
            value = getattr(self, attr)
            if not 0 <= value <= 1:
                raise ValueError(f"{attr} must be between 0 and 1, got {value}")
        
        # Validate colors are RGB tuples with values 0-1
        color_attrs = [
            'map_color', 'roaduser_color', 'highlight_color',
            'hist_traj_color', 'future_traj_color', 'pred_traj_color',
            'arrow_color',
            'traffic_light_red_color', 'traffic_light_yellow_color',
            'traffic_light_green_color', 'traffic_light_flashing_yellow_off_color',
            'traffic_light_default_color'
        ]
        for attr in color_attrs:
            color = getattr(self, attr)
            if not isinstance(color, tuple) or len(color) != 3:
                raise ValueError(f"{attr} must be a 3-tuple, got {color}")
            if not all(0 <= c <= 1 for c in color):
                raise ValueError(f"{attr} values must be between 0 and 1, got {color}")
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'StyleConfig':
        """
        Create StyleConfig from a dictionary.
        
        Args:
            config_dict: Dictionary with configuration values
            
        Returns:
            StyleConfig instance
            
        Example:
            >>> config_dict = {
            ...     'roaduser_color': (0, 0.8, 0),
            ...     'map_alpha': 0.5
            ... }
            >>> config = StyleConfig.from_dict(config_dict)
        """
        # Convert color lists back to tuples if needed
        color_attrs = [
            'map_color', 'roaduser_color', 'highlight_color',
            'hist_traj_color', 'future_traj_color', 'pred_traj_color',
            'arrow_color',
            'traffic_light_red_color', 'traffic_light_yellow_color',
            'traffic_light_green_color', 'traffic_light_flashing_yellow_off_color',
            'traffic_light_default_color'
        ]
        for attr in color_attrs:
            if attr in config_dict and isinstance(config_dict[attr], list):
                config_dict[attr] = tuple(config_dict[attr])
        
        return cls(**config_dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert StyleConfig to a dictionary.
        
        Returns:
            Dictionary representation of the configuration
            
        Example:
            >>> config = StyleConfig(map_alpha=0.5)
            >>> config_dict = config.to_dict()
        """
        return asdict(self)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'StyleConfig':
        """
        Create StyleConfig from a JSON string.
        
        Args:
            json_str: JSON string with configuration values
            
        Returns:
            StyleConfig instance
            
        Example:
            >>> json_str = '{"map_alpha": 0.5, "roaduser_color": [0, 0.8, 0]}'
            >>> config = StyleConfig.from_json(json_str)
        """
        config_dict = json.loads(json_str)
        return cls.from_dict(config_dict)
    
    def to_json(self, indent: int = 2) -> str:
        """
        Convert StyleConfig to a JSON string.
        
        Args:
            indent: Number of spaces for indentation (None for compact)
            
        Returns:
            JSON string representation
            
        Example:
            >>> config = StyleConfig(map_alpha=0.5)
            >>> json_str = config.to_json()
        """
        return json.dumps(self.to_dict(), indent=indent)
    
    @classmethod
    def from_file(cls, filepath: str) -> 'StyleConfig':
        """
        Load StyleConfig from a JSON file.
        
        Args:
            filepath: Path to JSON file
            
        Returns:
            StyleConfig instance
            
        Example:
            >>> config = StyleConfig.from_file('style_config.json')
        """
        with open(filepath, 'r') as f:
            config_dict = json.load(f)
        return cls.from_dict(config_dict)
    
    def to_file(self, filepath: str, indent: int = 2):
        """
        Save StyleConfig to a JSON file.
        
        Args:
            filepath: Path to save JSON file
            indent: Number of spaces for indentation
            
        Example:
            >>> config = StyleConfig(map_alpha=0.5)
            >>> config.to_file('style_config.json')
        """
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=indent)

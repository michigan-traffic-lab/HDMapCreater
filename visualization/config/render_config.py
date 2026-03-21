"""
Configuration for rendering frames.
"""
from dataclasses import dataclass, field, asdict
from typing import Tuple, List, Optional, Dict, Any
import json

from ..constants import (
    DEFAULT_FIGSIZE, DEFAULT_DPI, DEFAULT_FONTSIZE,
    DEFAULT_HIST_TRAJ_LEN, DEFAULT_FUTURE_TRAJ_LEN, DEFAULT_PRED_TRAJ_LEN
)


@dataclass
class RenderConfig:
    """
    Configuration for rendering a single frame.
    
    This replaces the 25+ parameters that were previously passed to plot_frame.
    """
    title: str = ""

    # ========================================================================
    # Map settings
    # ========================================================================
    show_map: bool = True
    show_lane_ids: bool = False
    show_arrows: bool = False
    plot_lane_ids: List[int] = field(default_factory=list)
    not_plot_lane_ids: List[int] = field(default_factory=list)
    highlight_lane_ids: List[int] = field(default_factory=list)
    draw_left: bool = True
    draw_right: bool = True
    draw_center: bool = False

    # ========================================================================
    # Road user settings
    # ========================================================================
    show_roadusers: bool = True
    # None = plot all, [] = plot none, [ids] = plot specific
    roaduser_ids: Optional[List[Any]] = None
    highlight_roaduser_ids: List[Any] = field(default_factory=list)
    show_roaduser_id_labels: bool = False
    roaduser_id_labels_to_show: List[Any] = field(default_factory=list)
    distinguish_by_source: bool = True

    # ========================================================================
    # Trajectory settings
    # ========================================================================
    show_hist_traj: bool = False
    hist_traj_length: int = DEFAULT_HIST_TRAJ_LEN

    show_future_traj: bool = False
    future_traj_length: int = DEFAULT_FUTURE_TRAJ_LEN

    show_pred_traj: bool = False
    pred_traj_length: int = DEFAULT_PRED_TRAJ_LEN
    pred_traj_highlight_ids: List[Any] = field(default_factory=list)

    # ========================================================================
    # Traffic elements
    # ========================================================================
    show_traffic_lights: bool = True
    flashing_yellow_frequency: int = 10  # frames per flash

    # ========================================================================
    # Traffic elements
    # ========================================================================
    x_units: str = "ft"
    y_units: str = "ft"
    x_conversion_factor: float = 3.28084
    y_conversion_factor: float = 3.28084

    # ========================================================================
    # Overlays
    # ========================================================================
    show_timestamp: bool = False
    timestamp_position: str = "top-right"
    show_scale_bar: bool = False

    # ========================================================================
    # Advanced options
    # ========================================================================
    intersection_polygons: Optional[List] = None
    custom_xlim: Optional[Tuple[float, float]] = None
    custom_ylim: Optional[Tuple[float, float]] = None

    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.hist_traj_length < 0:
            raise ValueError(f"hist_traj_length must be >= 0, got {self.hist_traj_length}")
        
        if self.future_traj_length < 0:
            raise ValueError(f"future_traj_length must be >= 0, got {self.future_traj_length}")
        
        if self.pred_traj_length < 0:
            raise ValueError(f"pred_traj_length must be >= 0, got {self.pred_traj_length}")
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'RenderConfig':
        """
        Create RenderConfig from a dictionary.
        
        Args:
            config_dict: Dictionary with configuration values
            
        Returns:
            RenderConfig instance
            
        Example:
            >>> config_dict = {
            ...     'figsize': (16, 12),
            ...     'dpi': 150,
            ...     'show_hist_traj': True,
            ...     'colorful': True
            ... }
            >>> config = RenderConfig.from_dict(config_dict)
        """
        # Convert tuple strings back to tuples if needed
        if 'figsize' in config_dict and isinstance(config_dict['figsize'], list):
            config_dict['figsize'] = tuple(config_dict['figsize'])
        
        return cls(**config_dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert RenderConfig to a dictionary.
        
        Returns:
            Dictionary representation of the configuration
            
        Example:
            >>> config = RenderConfig(dpi=150, colorful=True)
            >>> config_dict = config.to_dict()
        """
        return asdict(self)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'RenderConfig':
        """
        Create RenderConfig from a JSON string.
        
        Args:
            json_str: JSON string with configuration values
            
        Returns:
            RenderConfig instance
            
        Example:
            >>> json_str = '{"dpi": 150, "colorful": true}'
            >>> config = RenderConfig.from_json(json_str)
        """
        config_dict = json.loads(json_str)
        return cls.from_dict(config_dict)
    
    def to_json(self, indent: int = 2) -> str:
        """
        Convert RenderConfig to a JSON string.
        
        Args:
            indent: Number of spaces for indentation (None for compact)
            
        Returns:
            JSON string representation
            
        Example:
            >>> config = RenderConfig(dpi=150)
            >>> json_str = config.to_json()
        """
        return json.dumps(self.to_dict(), indent=indent)
    
    @classmethod
    def from_file(cls, filepath: str) -> 'RenderConfig':
        """
        Load RenderConfig from a JSON file.
        
        Args:
            filepath: Path to JSON file
            
        Returns:
            RenderConfig instance
            
        Example:
            >>> config = RenderConfig.from_file('config.json')
        """
        with open(filepath, 'r') as f:
            config_dict = json.load(f)
        return cls.from_dict(config_dict)
    
    def to_file(self, filepath: str, indent: int = 2):
        """
        Save RenderConfig to a JSON file.
        
        Args:
            filepath: Path to save JSON file
            indent: Number of spaces for indentation
            
        Example:
            >>> config = RenderConfig(dpi=150)
            >>> config.to_file('config.json')
        """
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=indent)

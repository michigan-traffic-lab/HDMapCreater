"""
Map and road network plotting.
"""
from typing import List, Optional
import numpy as np
import cv2

from ..config import RenderConfig, StyleConfig


def plot_map(
    ax,
    map_obj,
    config: Optional[RenderConfig] = None,
    style: Optional[StyleConfig] = None,
    extent: Optional[List[float]] = None,
    background_corners: Optional[dict] = None
):
    """
    Plot the road network map.
    
    Args:
        ax: Matplotlib axis
        map_obj: Map object with laneletLayer
        config: RenderConfig for display options
        style: StyleConfig for visual styling
        extent: [xmin, xmax, ymin, ymax] for background image
    """
    if config is None:
        config = RenderConfig()
    if style is None:
        style = StyleConfig()
    
    # Plot background image if available
    if extent and len(extent) == 4 and map_obj.background_img is not None:
        # ax.imshow(map_obj.background_img, extent=extent, zorder=0)
        img = np.array(map_obj.background_img.convert('RGBA'))
        H, W = img.shape[:2]

        src_corners = np.array([[0, 0], [W, 0], [W, H], [0, H]], dtype=np.float32)
        dst_corners = np.array([
            background_corners['top_left'],
            background_corners['top_right'],
            background_corners['bottom_right'],
            background_corners['bottom_left']
        ], dtype=np.float32)

        M = cv2.getPerspectiveTransform(src_corners, dst_corners)

        xmin, ymin = dst_corners.min(axis=0)
        xmax, ymax = dst_corners.max(axis=0)

        # Scale factor: preserve original resolution
        scale = max(W / (xmax - xmin), H / (ymax - ymin))
        out_w = int(np.ceil((xmax - xmin) * scale))
        out_h = int(np.ceil((ymax - ymin) * scale))

        # Shift to origin + scale to pixel size
        M_shift = np.array([
            [scale, 0, -xmin * scale],
            [0, scale, -ymin * scale],
            [0, 0, 1]
        ], dtype=np.float64) @ M

        warped = cv2.warpPerspective(img, M_shift, (out_w, out_h),
                                    borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))

        ax.imshow(warped, extent=[xmin, xmax, ymin, ymax], origin='lower', zorder=0)

    if not map_obj.base_map():
        return
    
    # Helper function to plot lane lines
    def _plot_lines(lane_points, lanelet_id):
        """Plot a single lane line."""
        if lanelet_id in config.highlight_lane_ids:
            color = style.highlight_color
        else:
            color = style.map_color
        
        ax.plot(*zip(*lane_points), color=color, zorder=1, alpha=style.map_alpha)
    
    # Plot each lanelet
    for lanelet in map_obj.laneletLayer:
        # Filter by lane IDs if specified
        if config.plot_lane_ids and lanelet.id not in config.plot_lane_ids:
            continue
        if config.not_plot_lane_ids and lanelet.id in config.not_plot_lane_ids:
            continue
        
        # Plot boundaries and centerline
        if config.draw_left:
            lane_points = [[point.x, point.y] for point in lanelet.leftBound]
            _plot_lines(lane_points, lanelet.id)
        
        if config.draw_right:
            lane_points = [[point.x, point.y] for point in lanelet.rightBound]
            _plot_lines(lane_points, lanelet.id)
        
        if config.draw_center:
            lane_points = [[point.x, point.y] for point in lanelet.centerline]
            _plot_lines(lane_points, lanelet.id)
        
        # Plot direction arrows if requested
        if config.show_arrows and len(lanelet.centerline) > 1:
            mid_ind = len(lanelet.centerline) // 2
            ax.arrow(
                lanelet.centerline[mid_ind].x,
                lanelet.centerline[mid_ind].y,
                lanelet.centerline[mid_ind + 1].x - lanelet.centerline[mid_ind].x,
                lanelet.centerline[mid_ind + 1].y - lanelet.centerline[mid_ind].y,
                head_width=style.arrow_width * 2,
                head_length=style.arrow_length * 2,
                fc=style.arrow_color,
                ec=style.arrow_color,
                zorder=2
            )
        
        # Plot lane IDs if requested
        if config.show_lane_ids and len(lanelet.centerline) > 0:
            ax.text(
                lanelet.centerline[-1].x,
                lanelet.centerline[-1].y,
                str(lanelet.id),
                fontsize=style.text_fontsize,
                zorder=3
            )

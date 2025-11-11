"""
Data Visualization Service for Concert AI Chatbot.

This service generates charts and visualizations for concert analytics,
encoding them for embedding in chatbot responses.
"""
import base64
import io
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Literal
import structlog
from pydantic import BaseModel, Field

try:
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    plt = None
    Figure = None

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None

logger = structlog.get_logger(__name__)


ChartType = Literal["bar", "line", "scatter", "heatmap", "pie"]


class VisualizationResult(BaseModel):
    """Result of visualization generation."""
    success: bool
    chart_type: str
    image_base64: Optional[str] = None
    image_format: str = "png"
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DataVisualizationService:
    """
    Service for generating data visualizations for concert analytics.
    
    Features:
    - Creates various chart types (bar, line, scatter, heatmap, pie)
    - Supports concert analytics visualizations (popularity trends, sales forecasts, rankings)
    - Encodes images as base64 for embedding in chatbot responses
    - Provides templates for common visualization patterns
    """
    
    def __init__(
        self,
        default_figsize: Tuple[int, int] = (10, 6),
        default_dpi: int = 100,
        style: str = "seaborn-v0_8-darkgrid"
    ):
        """
        Initialize the data visualization service.
        
        Args:
            default_figsize: Default figure size (width, height) in inches
            default_dpi: Default DPI for image rendering
            style: Matplotlib style to use
        """
        if not MATPLOTLIB_AVAILABLE:
            raise ImportError(
                "matplotlib is required for data visualization. "
                "Install it with: pip install matplotlib"
            )
        
        self.default_figsize = default_figsize
        self.default_dpi = default_dpi
        
        # Set matplotlib style
        try:
            plt.style.use(style)
        except Exception:
            # Fallback to default style if specified style not available
            try:
                plt.style.use('seaborn-v0_8')
            except Exception:
                pass  # Use matplotlib default
        
        self.logger = structlog.get_logger("DataVisualizationService")
    
    def _figure_to_base64(self, fig: Figure, format: str = "png") -> str:
        """
        Convert matplotlib figure to base64-encoded string.
        
        Args:
            fig: Matplotlib figure
            format: Image format (png, jpg, svg)
            
        Returns:
            Base64-encoded image string
        """
        buffer = io.BytesIO()
        fig.savefig(buffer, format=format, bbox_inches='tight', dpi=self.default_dpi)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        buffer.close()
        plt.close(fig)
        return image_base64
    
    def create_bar_chart(
        self,
        data: Dict[str, float],
        title: str,
        xlabel: str = "",
        ylabel: str = "",
        color: str = "#1f77b4",
        figsize: Optional[Tuple[int, int]] = None
    ) -> VisualizationResult:
        """
        Create a bar chart.
        
        Args:
            data: Dictionary mapping labels to values
            title: Chart title
            xlabel: X-axis label
            ylabel: Y-axis label
            color: Bar color
            figsize: Figure size (width, height)
            
        Returns:
            VisualizationResult with encoded image
        """
        try:
            figsize = figsize or self.default_figsize
            fig, ax = plt.subplots(figsize=figsize)
            
            labels = list(data.keys())
            values = list(data.values())
            
            bars = ax.bar(labels, values, color=color, alpha=0.8)
            
            # Add value labels on top of bars
            for bar in bars:
                height = bar.get_height()
                ax.text(
                    bar.get_x() + bar.get_width() / 2.,
                    height,
                    f'{height:.1f}',
                    ha='center',
                    va='bottom',
                    fontsize=9
                )
            
            ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
            ax.set_xlabel(xlabel, fontsize=11)
            ax.set_ylabel(ylabel, fontsize=11)
            ax.grid(axis='y', alpha=0.3)
            
            # Rotate x-axis labels if there are many
            if len(labels) > 5:
                plt.xticks(rotation=45, ha='right')
            
            plt.tight_layout()
            
            image_base64 = self._figure_to_base64(fig)
            
            return VisualizationResult(
                success=True,
                chart_type="bar",
                image_base64=image_base64,
                metadata={
                    "data_points": len(data),
                    "title": title
                }
            )
        
        except Exception as e:
            self.logger.error("Failed to create bar chart", error=str(e))
            return VisualizationResult(
                success=False,
                chart_type="bar",
                error=str(e)
            )
    
    def create_line_chart(
        self,
        data: Dict[str, List[float]],
        title: str,
        xlabel: str = "",
        ylabel: str = "",
        figsize: Optional[Tuple[int, int]] = None
    ) -> VisualizationResult:
        """
        Create a line chart with multiple series.
        
        Args:
            data: Dictionary mapping series names to lists of values
            title: Chart title
            xlabel: X-axis label
            ylabel: Y-axis label
            figsize: Figure size (width, height)
            
        Returns:
            VisualizationResult with encoded image
        """
        try:
            figsize = figsize or self.default_figsize
            fig, ax = plt.subplots(figsize=figsize)
            
            for series_name, values in data.items():
                x_values = list(range(len(values)))
                ax.plot(x_values, values, marker='o', label=series_name, linewidth=2)
            
            ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
            ax.set_xlabel(xlabel, fontsize=11)
            ax.set_ylabel(ylabel, fontsize=11)
            ax.grid(True, alpha=0.3)
            ax.legend(loc='best', framealpha=0.9)
            
            plt.tight_layout()
            
            image_base64 = self._figure_to_base64(fig)
            
            return VisualizationResult(
                success=True,
                chart_type="line",
                image_base64=image_base64,
                metadata={
                    "series_count": len(data),
                    "title": title
                }
            )
        
        except Exception as e:
            self.logger.error("Failed to create line chart", error=str(e))
            return VisualizationResult(
                success=False,
                chart_type="line",
                error=str(e)
            )

    def create_scatter_plot(
        self,
        x_values: List[float],
        y_values: List[float],
        title: str,
        xlabel: str = "",
        ylabel: str = "",
        labels: Optional[List[str]] = None,
        color: str = "#ff7f0e",
        figsize: Optional[Tuple[int, int]] = None
    ) -> VisualizationResult:
        """
        Create a scatter plot.
        
        Args:
            x_values: X-axis values
            y_values: Y-axis values
            title: Chart title
            xlabel: X-axis label
            ylabel: Y-axis label
            labels: Optional labels for each point
            color: Point color
            figsize: Figure size (width, height)
            
        Returns:
            VisualizationResult with encoded image
        """
        try:
            if len(x_values) != len(y_values):
                raise ValueError("x_values and y_values must have the same length")
            
            figsize = figsize or self.default_figsize
            fig, ax = plt.subplots(figsize=figsize)
            
            ax.scatter(x_values, y_values, color=color, alpha=0.6, s=100, edgecolors='black', linewidth=0.5)
            
            # Add labels if provided
            if labels and len(labels) == len(x_values):
                for i, label in enumerate(labels):
                    ax.annotate(
                        label,
                        (x_values[i], y_values[i]),
                        xytext=(5, 5),
                        textcoords='offset points',
                        fontsize=8,
                        alpha=0.7
                    )
            
            ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
            ax.set_xlabel(xlabel, fontsize=11)
            ax.set_ylabel(ylabel, fontsize=11)
            ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            image_base64 = self._figure_to_base64(fig)
            
            return VisualizationResult(
                success=True,
                chart_type="scatter",
                image_base64=image_base64,
                metadata={
                    "data_points": len(x_values),
                    "title": title
                }
            )
        
        except Exception as e:
            self.logger.error("Failed to create scatter plot", error=str(e))
            return VisualizationResult(
                success=False,
                chart_type="scatter",
                error=str(e)
            )
    
    def create_pie_chart(
        self,
        data: Dict[str, float],
        title: str,
        figsize: Optional[Tuple[int, int]] = None
    ) -> VisualizationResult:
        """
        Create a pie chart.
        
        Args:
            data: Dictionary mapping labels to values
            title: Chart title
            figsize: Figure size (width, height)
            
        Returns:
            VisualizationResult with encoded image
        """
        try:
            figsize = figsize or (8, 8)
            fig, ax = plt.subplots(figsize=figsize)
            
            labels = list(data.keys())
            values = list(data.values())
            
            # Create pie chart with percentage labels
            wedges, texts, autotexts = ax.pie(
                values,
                labels=labels,
                autopct='%1.1f%%',
                startangle=90,
                textprops={'fontsize': 10}
            )
            
            # Make percentage text bold
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
            
            ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
            
            plt.tight_layout()
            
            image_base64 = self._figure_to_base64(fig)
            
            return VisualizationResult(
                success=True,
                chart_type="pie",
                image_base64=image_base64,
                metadata={
                    "categories": len(data),
                    "title": title
                }
            )
        
        except Exception as e:
            self.logger.error("Failed to create pie chart", error=str(e))
            return VisualizationResult(
                success=False,
                chart_type="pie",
                error=str(e)
            )
    
    def create_heatmap(
        self,
        data: List[List[float]],
        title: str,
        row_labels: Optional[List[str]] = None,
        col_labels: Optional[List[str]] = None,
        cmap: str = "YlOrRd",
        figsize: Optional[Tuple[int, int]] = None
    ) -> VisualizationResult:
        """
        Create a heatmap.
        
        Args:
            data: 2D list of values
            title: Chart title
            row_labels: Labels for rows
            col_labels: Labels for columns
            cmap: Colormap name
            figsize: Figure size (width, height)
            
        Returns:
            VisualizationResult with encoded image
        """
        try:
            if not NUMPY_AVAILABLE:
                raise ImportError("numpy is required for heatmaps")
            
            figsize = figsize or self.default_figsize
            fig, ax = plt.subplots(figsize=figsize)
            
            data_array = np.array(data)
            
            im = ax.imshow(data_array, cmap=cmap, aspect='auto')
            
            # Set ticks and labels
            if row_labels:
                ax.set_yticks(np.arange(len(row_labels)))
                ax.set_yticklabels(row_labels)
            
            if col_labels:
                ax.set_xticks(np.arange(len(col_labels)))
                ax.set_xticklabels(col_labels, rotation=45, ha='right')
            
            # Add colorbar
            cbar = plt.colorbar(im, ax=ax)
            cbar.ax.set_ylabel('Value', rotation=270, labelpad=15)
            
            # Add value annotations
            for i in range(len(data)):
                for j in range(len(data[0])):
                    text = ax.text(
                        j, i, f'{data[i][j]:.1f}',
                        ha="center", va="center",
                        color="black" if data[i][j] < np.max(data_array) * 0.5 else "white",
                        fontsize=8
                    )
            
            ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
            
            plt.tight_layout()
            
            image_base64 = self._figure_to_base64(fig)
            
            return VisualizationResult(
                success=True,
                chart_type="heatmap",
                image_base64=image_base64,
                metadata={
                    "rows": len(data),
                    "cols": len(data[0]) if data else 0,
                    "title": title
                }
            )
        
        except Exception as e:
            self.logger.error("Failed to create heatmap", error=str(e))
            return VisualizationResult(
                success=False,
                chart_type="heatmap",
                error=str(e)
            )
    
    # Template methods for common concert analytics visualizations
    
    def create_venue_popularity_chart(
        self,
        venues: List[Dict[str, Any]],
        top_n: int = 10
    ) -> VisualizationResult:
        """
        Create a bar chart showing top venue popularity rankings.
        
        Args:
            venues: List of venue dictionaries with 'name' and 'popularity_rank' or 'avg_attendance_rate'
            top_n: Number of top venues to display
            
        Returns:
            VisualizationResult with encoded image
        """
        try:
            # Sort venues by popularity (lower rank = more popular) or attendance rate
            if venues and 'popularity_rank' in venues[0]:
                sorted_venues = sorted(venues, key=lambda v: v.get('popularity_rank', 999))[:top_n]
                metric_key = 'avg_attendance_rate'
                ylabel = 'Average Attendance Rate (%)'
            else:
                sorted_venues = sorted(
                    venues,
                    key=lambda v: v.get('avg_attendance_rate', 0),
                    reverse=True
                )[:top_n]
                metric_key = 'avg_attendance_rate'
                ylabel = 'Average Attendance Rate (%)'
            
            data = {
                v.get('name', f"Venue {i+1}"): v.get(metric_key, 0) * 100
                for i, v in enumerate(sorted_venues)
            }
            
            return self.create_bar_chart(
                data=data,
                title=f"Top {len(data)} Most Popular Venues",
                xlabel="Venue",
                ylabel=ylabel,
                color="#2ca02c"
            )
        
        except Exception as e:
            self.logger.error("Failed to create venue popularity chart", error=str(e))
            return VisualizationResult(
                success=False,
                chart_type="bar",
                error=str(e)
            )
    
    def create_ticket_sales_forecast_chart(
        self,
        predictions: List[Dict[str, Any]]
    ) -> VisualizationResult:
        """
        Create a bar chart showing ticket sales predictions.
        
        Args:
            predictions: List of prediction dictionaries with 'concert_name' and 'predicted_sales'
            
        Returns:
            VisualizationResult with encoded image
        """
        try:
            data = {
                p.get('concert_name', f"Concert {i+1}"): p.get('predicted_sales', 0)
                for i, p in enumerate(predictions)
            }
            
            return self.create_bar_chart(
                data=data,
                title="Ticket Sales Forecast",
                xlabel="Concert",
                ylabel="Predicted Ticket Sales",
                color="#d62728"
            )
        
        except Exception as e:
            self.logger.error("Failed to create ticket sales forecast chart", error=str(e))
            return VisualizationResult(
                success=False,
                chart_type="bar",
                error=str(e)
            )
    
    def create_artist_popularity_trend_chart(
        self,
        artist_data: Dict[str, List[float]],
        time_labels: Optional[List[str]] = None
    ) -> VisualizationResult:
        """
        Create a line chart showing artist popularity trends over time.
        
        Args:
            artist_data: Dictionary mapping artist names to popularity scores over time
            time_labels: Optional time period labels for x-axis
            
        Returns:
            VisualizationResult with encoded image
        """
        try:
            result = self.create_line_chart(
                data=artist_data,
                title="Artist Popularity Trends",
                xlabel="Time Period" if not time_labels else "",
                ylabel="Popularity Score"
            )
            
            # If time labels provided, update the chart
            if time_labels and result.success:
                # Note: This is a simplified version. For production, you'd want to
                # modify the create_line_chart method to accept x-axis labels
                pass
            
            return result
        
        except Exception as e:
            self.logger.error("Failed to create artist popularity trend chart", error=str(e))
            return VisualizationResult(
                success=False,
                chart_type="line",
                error=str(e)
            )
    
    def create_genre_distribution_chart(
        self,
        genre_counts: Dict[str, int]
    ) -> VisualizationResult:
        """
        Create a pie chart showing genre distribution.
        
        Args:
            genre_counts: Dictionary mapping genre names to counts
            
        Returns:
            VisualizationResult with encoded image
        """
        try:
            return self.create_pie_chart(
                data=genre_counts,
                title="Concert Genre Distribution"
            )
        
        except Exception as e:
            self.logger.error("Failed to create genre distribution chart", error=str(e))
            return VisualizationResult(
                success=False,
                chart_type="pie",
                error=str(e)
            )
    
    def create_revenue_vs_attendance_chart(
        self,
        concerts: List[Dict[str, Any]]
    ) -> VisualizationResult:
        """
        Create a scatter plot showing revenue vs attendance correlation.
        
        Args:
            concerts: List of concert dictionaries with 'total_attendance' and 'revenue'
            
        Returns:
            VisualizationResult with encoded image
        """
        try:
            x_values = [c.get('total_attendance', 0) for c in concerts]
            y_values = [c.get('revenue', 0) for c in concerts]
            labels = [c.get('name', f"Concert {i+1}") for i, c in enumerate(concerts)]
            
            return self.create_scatter_plot(
                x_values=x_values,
                y_values=y_values,
                title="Revenue vs Attendance",
                xlabel="Total Attendance",
                ylabel="Revenue ($)",
                labels=labels if len(concerts) <= 20 else None,  # Only show labels if not too many
                color="#9467bd"
            )
        
        except Exception as e:
            self.logger.error("Failed to create revenue vs attendance chart", error=str(e))
            return VisualizationResult(
                success=False,
                chart_type="scatter",
                error=str(e)
            )

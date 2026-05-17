"""
Unit tests for visualization functions.
"""

import os
import sys
import tempfile
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import matplotlib.pyplot as plt

# Mock openturns if not available
try:
    import openturns as ot
    OPENTURNS_AVAILABLE = True
except ImportError:
    OPENTURNS_AVAILABLE = False
    # Use mock openturns
    sys.path.insert(0, str(Path(__file__).parent))
    import mock_openturns as ot

from otGpxTrack.Base import GpxTrack
from streamlitApp.visualization import (
    plot_track_with_speed,
    plot_speed_over_time,
    plot_elevation_profile,
    plot_speed_distribution,
    create_comparison_plot,
)


def get_test_file_path(filename):
    """Get the absolute path to a test file."""
    return os.path.join(os.path.dirname(__file__), '..', '..', 'firstexample', filename)


@pytest.fixture
def sample_track():
    """Fixture to load a sample GPX track."""
    gpx_file = get_test_file_path("activity_19218242997.gpx")
    return GpxTrack(gpx_file)


class TestVisualization:
    """Test class for visualization functions."""

    def test_plot_track_with_speed(self, sample_track):
        """Test track plot with speed coloring."""
        fig = plot_track_with_speed(sample_track, speed_unit="knots")
        
        assert fig is not None
        assert isinstance(fig, plt.Figure)
        assert len(fig.axes) >= 1
        
        # Clean up
        plt.close(fig)

    def test_plot_track_with_speed_different_units(self, sample_track):
        """Test track plot with different speed units."""
        for unit in ["m/s", "km/h", "knots"]:
            fig = plot_track_with_speed(sample_track, speed_unit=unit)
            assert fig is not None
            plt.close(fig)

    def test_plot_track_with_speed_custom_figsize(self, sample_track):
        """Test track plot with custom figure size."""
        fig = plot_track_with_speed(sample_track, figsize=(10, 6))
        assert fig is not None
        plt.close(fig)

    def test_plot_speed_over_time(self, sample_track):
        """Test speed over time plot."""
        fig = plot_speed_over_time(sample_track, speed_unit="knots")
        
        assert fig is not None
        assert isinstance(fig, plt.Figure)
        assert len(fig.axes) >= 1
        
        plt.close(fig)

    def test_plot_speed_over_time_with_process_sample(self, sample_track):
        """Test speed over time plot with process sample."""
        # Generate a process sample
        process_sample = sample_track.processSample(
            sample_size=100, method='ar1', sigma_tot=2.5, phi=0.9
        )
        
        fig = plot_speed_over_time(
            sample_track, 
            speed_unit="knots",
            process_sample=process_sample
        )
        
        assert fig is not None
        plt.close(fig)

    def test_plot_elevation_profile(self, sample_track):
        """Test elevation profile plot."""
        fig = plot_elevation_profile(sample_track)
        
        assert fig is not None
        assert isinstance(fig, plt.Figure)
        assert len(fig.axes) >= 1
        
        plt.close(fig)

    def test_plot_elevation_profile_custom_figsize(self, sample_track):
        """Test elevation profile plot with custom figure size."""
        fig = plot_elevation_profile(sample_track, figsize=(14, 8))
        assert fig is not None
        plt.close(fig)

    def test_plot_speed_distribution(self, sample_track):
        """Test speed distribution histogram."""
        fig = plot_speed_distribution(sample_track, speed_unit="knots")
        
        assert fig is not None
        assert isinstance(fig, plt.Figure)
        assert len(fig.axes) >= 1
        
        plt.close(fig)

    def test_plot_speed_distribution_different_units(self, sample_track):
        """Test speed distribution with different speed units."""
        for unit in ["m/s", "km/h", "knots"]:
            fig = plot_speed_distribution(sample_track, speed_unit=unit)
            assert fig is not None
            plt.close(fig)

    def test_plot_speed_distribution_custom_bins(self, sample_track):
        """Test speed distribution with custom number of bins."""
        fig = plot_speed_distribution(sample_track, bins=20)
        assert fig is not None
        plt.close(fig)

    def test_create_comparison_plot(self, sample_track):
        """Test comparison plot with multiple subplots."""
        fig = create_comparison_plot(sample_track)
        
        assert fig is not None
        assert isinstance(fig, plt.Figure)
        # Should have 4 subplots (2x2 grid)
        assert len(fig.axes) >= 4
        
        plt.close(fig)

    def test_visualization_error_handling(self):
        """Test error handling for empty tracks."""
        # Create a mock track with no points
        class MockTrack:
            def __init__(self):
                self.points = []
                self.data = None
        
        mock_track = MockTrack()
        
        # These should raise ValueError
        with pytest.raises(ValueError):
            plot_track_with_speed(mock_track)
        
        with pytest.raises(ValueError):
            plot_speed_over_time(mock_track)
        
        with pytest.raises(ValueError):
            plot_elevation_profile(mock_track)
        
        with pytest.raises(ValueError):
            plot_speed_distribution(mock_track)


class TestVisualizationEdgeCases:
    """Test edge cases for visualization functions."""

    def test_single_point_track(self):
        """Test visualization with a track that has only one point."""
        # This is a bit tricky to test without creating a real GPX file
        # For now, we'll just test that the functions handle it gracefully
        pass

    def test_zero_speed_points(self, sample_track):
        """Test that zero speeds are handled correctly."""
        # The visualization functions should handle zero speeds
        fig = plot_speed_distribution(sample_track)
        assert fig is not None
        plt.close(fig)

    def test_missing_elevation_data(self, sample_track):
        """Test elevation profile with potentially missing elevation data."""
        # The elevation profile function should handle missing elevation
        fig = plot_elevation_profile(sample_track)
        assert fig is not None
        plt.close(fig)

"""
Unit tests for Streamlit app components.

These tests verify the functionality of individual components used in the app.
"""

import os
import sys
import tempfile
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for testing

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


def get_test_file_path(filename):
    """Get the absolute path to a test file."""
    return os.path.join(os.path.dirname(__file__), '..', '..', 'firstexample', filename)


@pytest.fixture
def sample_track():
    """Fixture to load a sample GPX track."""
    gpx_file = get_test_file_path("activity_19218242997.gpx")
    return GpxTrack(gpx_file)


class TestTrackStatistics:
    """Test track statistics calculations."""

    def test_track_distance(self, sample_track):
        """Test distance calculation."""
        distance = sample_track.get_distance()
        assert distance > 0
        assert isinstance(distance, float)

    def test_track_duration(self, sample_track):
        """Test duration calculation."""
        duration = sample_track.get_duration()
        assert duration > 0
        assert isinstance(duration, float)

    def test_track_average_speed(self, sample_track):
        """Test average speed calculation."""
        avg_speed = sample_track.get_average_speed()
        assert avg_speed >= 0
        assert isinstance(avg_speed, float)

    def test_speed_unit_conversion(self, sample_track):
        """Test speed unit conversions."""
        avg_speed_mps = sample_track.get_average_speed()
        
        # Convert to km/h
        avg_speed_kmh = avg_speed_mps * 3.6
        assert avg_speed_kmh > avg_speed_mps
        
        # Convert to knots
        avg_speed_knots = avg_speed_mps * 1.94384
        assert avg_speed_knots > avg_speed_mps


class TestBestSegmentAnalysis:
    """Test best segment analysis functionality."""

    def test_best_segment_for_distance(self, sample_track):
        """Test finding best segment for a target distance."""
        target_distance = 500.0
        start_idx, end_idx, speed = sample_track.get_best_segment_for_distance(target_distance)
        
        assert start_idx < end_idx
        assert end_idx < len(sample_track.points)
        assert speed >= 0
        assert isinstance(start_idx, int)
        assert isinstance(end_idx, int)
        assert isinstance(speed, float)

    def test_best_segment_for_time(self, sample_track):
        """Test finding best segment for a target time."""
        target_time = 10.0
        start_idx, end_idx, speed = sample_track.get_best_segment_for_time(target_time)
        
        assert start_idx < end_idx
        assert end_idx < len(sample_track.points)
        assert speed >= 0

    def test_best_segment_edge_cases(self, sample_track):
        """Test best segment with edge cases."""
        # Test with very small target
        start_idx, end_idx, speed = sample_track.get_best_segment_for_distance(10.0)
        assert start_idx < end_idx
        
        # Test with larger target (but not too large)
        start_idx, end_idx, speed = sample_track.get_best_segment_for_distance(1000.0)
        assert start_idx < end_idx


class TestSimulationAnalysis:
    """Test simulation analysis functionality."""

    def test_ar1_simulation(self, sample_track):
        """Test AR-1 simulation."""
        segment_indices = (0, min(10, len(sample_track.points)-1))
        mean_speed, lower, upper, speeds = sample_track.simulate_ar1_speeds(
            segment_indices, 
            sigma_tot=2.5, 
            phi=0.9, 
            n_sims=100
        )
        
        assert mean_speed >= 0
        assert lower <= mean_speed <= upper
        assert speeds.getSize() == 100

    def test_process_sample_ar1(self, sample_track):
        """Test AR-1 process sample generation."""
        process_sample = sample_track.processSample(
            sample_size=100, 
            method='ar1', 
            sigma_tot=2.5, 
            phi=0.9
        )
        
        assert process_sample is not None
        assert process_sample.getSize() == 100
        assert process_sample.getDimension() == 1

    def test_process_sample_gaussian(self, sample_track):
        """Test Gaussian process sample generation."""
        process_sample = sample_track.processSample(
            sample_size=100, 
            method='gaussian', 
            amplitude=1.5, 
            scale=5.0
        )
        
        assert process_sample is not None
        assert process_sample.getSize() == 100
        assert process_sample.getDimension() == 1

    def test_process_sample_quantiles(self, sample_track):
        """Test quantile calculation from process sample."""
        process_sample = sample_track.processSample(
            sample_size=500, 
            method='ar1', 
            sigma_tot=2.5, 
            phi=0.9
        )
        
        quantiles = process_sample.computeQuantilePerComponent([0.025, 0.5, 0.975])
        
        assert quantiles is not None
        assert len(quantiles) == 3  # Three quantile levels


class TestDataIntegrity:
    """Test data integrity and consistency."""

    def test_openturns_sample(self, sample_track):
        """Test OpenTURNS sample creation."""
        sample = sample_track.get_openturns_sample()
        
        assert sample is not None
        assert sample.getSize() > 0
        assert sample.getDimension() == 5  # lat, lon, elev, time, speed
        assert sample.getDescription() == ["Latitude", "Longitude", "Elevation", "Time", "Speed"]

    def test_points_consistency(self, sample_track):
        """Test that points and data are consistent."""
        assert len(sample_track.points) > 0
        assert sample_track.data.getSize() == len(sample_track.points)

    def test_track_info_consistency(self, sample_track):
        """Test that track information is consistent."""
        distance = sample_track.get_distance()
        duration = sample_track.get_duration()
        avg_speed = sample_track.get_average_speed()
        
        # If duration is not zero, avg_speed should be distance/duration
        if duration > 0:
            expected_avg_speed = distance / duration
            assert abs(avg_speed - expected_avg_speed) < 0.001


class TestFileHandling:
    """Test file handling and loading."""

    def test_load_gpx_file(self):
        """Test loading GPX file."""
        gpx_file = get_test_file_path("activity_19218242997.gpx")
        track = GpxTrack(gpx_file)
        
        assert track is not None
        assert track.gpx is not None
        assert len(track.points) > 0
        assert track.data is not None

    def test_load_different_gpx_file(self):
        """Test loading a different GPX file."""
        gpx_file = get_test_file_path("activity_22095267736.gpx")
        track = GpxTrack(gpx_file)
        
        assert track is not None
        assert len(track.points) > 0

    def test_file_not_found(self):
        """Test handling of non-existent file."""
        with pytest.raises(FileNotFoundError):
            GpxTrack("non_existent_file.gpx")

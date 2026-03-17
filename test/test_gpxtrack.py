"""
Test module for GpxTrack class.
"""
import pytest
import os
import numpy as np
import openturns as ot
import matplotlib.pyplot as plt
from otGpxTrack.Base import GpxTrack


def get_test_file_path(filename):
    """Get the absolute path to a test file."""
    return os.path.join(os.path.dirname(__file__), '..', 'firstexample', filename)


def test_gpxtrack_initialization():
    """Test the initialization of GpxTrack with a valid GPX file."""
    gpx_file = get_test_file_path("activity_19218242997.gpx")
    track = GpxTrack(gpx_file)
    assert track.gpx is not None
    assert len(track.points) > 0
    assert track.data is not None


def test_gpxtrack_distance():
    """Test the distance calculation of GpxTrack."""
    gpx_file = get_test_file_path("activity_19218242997.gpx")
    track = GpxTrack(gpx_file)
    distance = track.get_distance()
    assert distance > 0


def test_gpxtrack_duration():
    """Test the duration calculation of GpxTrack."""
    gpx_file = get_test_file_path("activity_19218242997.gpx")
    track = GpxTrack(gpx_file)
    duration = track.get_duration()
    assert duration > 0


def test_gpxtrack_average_speed():
    """Test the average speed calculation of GpxTrack."""
    gpx_file = get_test_file_path("activity_19218242997.gpx")
    track = GpxTrack(gpx_file)
    avg_speed = track.get_average_speed()
    assert avg_speed >= 0


def test_gpxtrack_openturns_sample():
    """Test the OpenTURNS sample creation of GpxTrack."""
    gpx_file = get_test_file_path("activity_19218242997.gpx")
    track = GpxTrack(gpx_file)
    sample = track.get_openturns_sample()
    assert sample.getSize() > 0
    assert sample.getDimension() == 5  # latitude, longitude, elevation, time, speed
    assert sample.getDescription() == ["Latitude", "Longitude", "Elevation", "Time", "Speed"]


def test_gpxtrack_ar1_simulation():
    """Test the AR-1 speed simulation of GpxTrack."""
    gpx_file = get_test_file_path("activity_19218242997.gpx")
    track = GpxTrack(gpx_file)
    
    # Test with a small segment
    segment_indices = (0, min(10, len(track.points)-1))
    mean_speed, lower, upper, speeds = track.simulate_ar1_speeds(segment_indices, n_sims=100)
    
    assert mean_speed >= 0
    assert lower <= mean_speed <= upper
    assert speeds.getSize() == 100
    assert isinstance(speeds, ot.Sample)


def test_gpxtrack_best_segment():
    """Test the best segment finding for a target distance."""
    gpx_file = get_test_file_path("activity_19218242997.gpx")
    track = GpxTrack(gpx_file)
    
    # Test with a reasonable target distance
    start_idx, end_idx, speed = track.get_best_segment_for_distance(500)
    
    assert start_idx < end_idx
    assert end_idx < len(track.points)
    assert speed >= 0


def test_gpxtrack_best_segment_for_time():
    """Test the best segment finding for a target time."""
    gpx_file = get_test_file_path("activity_19218242997.gpx")
    track = GpxTrack(gpx_file)
    
    # Test with a reasonable target time (10 seconds)
    start_idx, end_idx, speed = track.get_best_segment_for_time(10.0)
    
    assert start_idx < end_idx
    assert end_idx < len(track.points)
    assert speed >= 0


def test_gpxtrack_plot():
    """Test the track plotting functionality."""
    gpx_file = get_test_file_path("activity_19218242997.gpx")
    track = GpxTrack(gpx_file)
    
    # Test plotting with different speed units
    for unit in ["m/s", "km/h", "knots"]:
        fig = track.plot_track(title="Test Track", figsize=(8, 6), speed_unit=unit)
        
        assert fig is not None
        assert len(fig.axes) == 2  # Main plot + colorbar
        assert fig.axes[0].get_title() == "Test Track"
        
        # Close the figure to free memory
        plt.close(fig)

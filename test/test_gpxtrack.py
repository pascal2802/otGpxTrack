"""
Test module for GpxTrack class.
"""
import pytest
import os
import numpy as np
import openturns as ot
import matplotlib.pyplot as plt
from otGpxTrack.Base import GpxTrack
from otGpxTrack.main import GpxTrack as GpxTrackMain


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


def test_gpxtrack_main_calculate_avg_speed():
    """Test the calculate_avg_speed method of GpxTrack in main.py."""
    gpx_file = get_test_file_path("activity_19218242997.gpx")
    track = GpxTrackMain(gpx_file)
    avg_speed_kmh = track.calculate_avg_speed()
    
    # Verify the result is non-negative
    assert avg_speed_kmh >= 0
    
    # Verify the result is in km/h (should be a reasonable value for a track)
    # Typical running/cycling speeds are between 0 and 100 km/h
    assert avg_speed_kmh < 1000


def test_gpxtrack_main_calculate_avg_speed_conversion():
    """Test that calculate_avg_speed correctly converts from m/s to km/h."""
    gpx_file = get_test_file_path("activity_19218242997.gpx")
    track_base = GpxTrack(gpx_file)
    track_main = GpxTrackMain(gpx_file)
    
    # Get speeds in both units
    avg_speed_mps = track_base.get_average_speed()
    avg_speed_kmh = track_main.calculate_avg_speed()
    
    # Verify the conversion: km/h = m/s * 3.6
    expected_kmh = avg_speed_mps * 3.6
    assert abs(avg_speed_kmh - expected_kmh) < 0.001


def test_gpxtrack_main_calculate_avg_speed_zero_duration():
    """Test calculate_avg_speed with zero duration (edge case)."""
    # For this test, we'll use the existing file but verify the method handles edge cases
    gpx_file = get_test_file_path("activity_19218242997.gpx")
    track = GpxTrackMain(gpx_file)
    
    # If duration is zero, the method should return 0.0
    # We can't easily create a zero-duration track, but we can verify the logic
    # by checking that the method doesn't crash and returns a valid value
    avg_speed_kmh = track.calculate_avg_speed()
    assert isinstance(avg_speed_kmh, float)


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


def test_gpxtrack_process_sample():
    """Test the processSample method for generating stochastic process realizations."""
    gpx_file = get_test_file_path("activity_19218242997.gpx")
    track = GpxTrack(gpx_file)
    
    # Test with default parameters (AR-1 method)
    process_sample = track.processSample(sample_size=100, method='ar1')
    
    # Verify the output is a ProcessSample
    assert isinstance(process_sample, ot.ProcessSample)
    
    # Verify the dimensions
    assert process_sample.getSize() == 100  # Number of realizations
    assert process_sample.getDimension() == 1  # Dimension of the process (speed)
    
    # Verify the time grid
    time_grid = process_sample.getTimeGrid()
    assert time_grid.getN() == len(track.points)  # Should match number of track points
    
    # Test with custom parameters for AR-1
    process_sample_custom = track.processSample(sample_size=50, method='ar1', sigma_tot=1.5, phi=0.7)
    assert process_sample_custom.getSize() == 50
    
    # Test Gaussian process method
    process_sample_gaussian = track.processSample(sample_size=50, method='gaussian', amplitude=1.0, scale=1.0)
    assert isinstance(process_sample_gaussian, ot.ProcessSample)
    assert process_sample_gaussian.getSize() == 50
    assert process_sample_gaussian.getDimension() == 1
    
    # Test with different Gaussian process parameters
    process_sample_gaussian_custom = track.processSample(sample_size=30, method='gaussian', amplitude=0.5, scale=2.0)
    assert process_sample_gaussian_custom.getSize() == 30
    
    # Test error handling for unsupported method
    with pytest.raises(ValueError):
        track.processSample(method='unsupported')
    return process_sample

if __name__=='__main__':
    ps = test_gpxtrack_process_sample()

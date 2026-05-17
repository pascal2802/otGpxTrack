"""
Test module for GpxTrack class in main.py.
"""
import pytest
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from otGpxTrack.main import GpxTrack


def get_test_file_path(filename):
    """Get the absolute path to a test file."""
    return os.path.join(os.path.dirname(__file__), '..', 'firstexample', filename)


def test_gpxtrack_main_initialization():
    """Test the initialization of GpxTrack with a valid GPX file."""
    gpx_file = get_test_file_path("activity_19218242997.gpx")
    track = GpxTrack(gpx_file)
    assert track.gpx is not None
    assert len(track.points) > 0


def test_gpxtrack_main_distance():
    """Test the distance calculation of GpxTrack."""
    gpx_file = get_test_file_path("activity_19218242997.gpx")
    track = GpxTrack(gpx_file)
    distance = track.get_distance()
    assert distance > 0


def test_gpxtrack_main_duration():
    """Test the duration calculation of GpxTrack."""
    gpx_file = get_test_file_path("activity_19218242997.gpx")
    track = GpxTrack(gpx_file)
    duration = track.get_duration()
    assert duration > 0


def test_gpxtrack_main_calculate_avg_speed():
    """Test the calculate_avg_speed method of GpxTrack in main.py."""
    gpx_file = get_test_file_path("activity_19218242997.gpx")
    track = GpxTrack(gpx_file)
    avg_speed_kmh = track.calculate_avg_speed()
    
    # Verify the result is non-negative
    assert avg_speed_kmh >= 0
    
    # Verify the result is in km/h (should be a reasonable value for a track)
    # Typical running/cycling speeds are between 0 and 100 km/h
    assert avg_speed_kmh < 1000


def test_gpxtrack_main_calculate_avg_speed_conversion():
    """Test that calculate_avg_speed correctly converts from m/s to km/h."""
    gpx_file = get_test_file_path("activity_19218242997.gpx")
    track = GpxTrack(gpx_file)
    
    # Get distance and duration
    distance = track.get_distance()
    duration = track.get_duration()
    
    # Calculate expected speed in km/h
    expected_kmh = (distance / duration) * 3.6
    avg_speed_kmh = track.calculate_avg_speed()
    
    # Verify the conversion: km/h = m/s * 3.6
    assert abs(avg_speed_kmh - expected_kmh) < 0.001


def test_gpxtrack_main_calculate_avg_speed_zero_duration():
    """Test calculate_avg_speed with zero duration (edge case)."""
    # Create a minimal GPX file with a single point
    import tempfile
    import gpxpy.gpx
    
    # Create a GPX with one point
    gpx = gpxpy.gpx.GPX()
    track = gpxpy.gpx.GPXTrack()
    gpx.tracks.append(track)
    segment = gpxpy.gpx.GPXTrackSegment()
    track.segments.append(segment)
    segment.points.append(gpxpy.gpx.GPXTrackPoint(0.0, 0.0))
    
    # Write to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.gpx', delete=False) as f:
        f.write(gpx.to_xml())
        temp_path = f.name
    
    try:
        # Test with single point (zero duration)
        track = GpxTrack(temp_path)
        avg_speed_kmh = track.calculate_avg_speed()
        assert avg_speed_kmh == 0.0
    finally:
        os.unlink(temp_path)

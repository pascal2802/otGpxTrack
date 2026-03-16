"""
Test module for GpxTrack class.
"""
import pytest
import os
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

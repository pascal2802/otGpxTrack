"""
Main module for GpxTrack with additional utility methods.
"""

import gpxpy


class GpxTrack:
    """
    A class to represent and analyze a GPX track.
    """

    def __init__(self, gpx_file_path):
        """
        Initialize the GpxTrack with a GPX file.

        Args:
            gpx_file_path (str): Path to the GPX file.
        """
        self.gpx_file_path = gpx_file_path
        self.gpx = None
        self.points = []
        self._load_gpx()
        self._extract_points()

    def _load_gpx(self):
        """Load and parse the GPX file."""
        with open(self.gpx_file_path, "rb") as f:
            self.gpx = gpxpy.parse(f)

    def _extract_points(self):
        """Extract track points from the GPX object."""
        for track in self.gpx.tracks:
            for segment in track.segments:
                self.points.extend(segment.points)

    def get_distance(self):
        """
        Calculate the total distance of the track.

        Returns:
            float: Total distance in meters.
        """
        total_distance = 0.0
        for i in range(1, len(self.points)):
            total_distance += self.points[i].distance_3d(self.points[i - 1])
        return total_distance

    def get_duration(self):
        """
        Calculate the total duration of the track.

        Returns:
            float: Total duration in seconds.
        """
        if len(self.points) < 2:
            return 0.0
        start_time = self.points[0].time
        end_time = self.points[-1].time
        return (end_time - start_time).total_seconds()

    def calculate_avg_speed(self):
        """
        Calculate the average speed of the track in km/h using timestamps and coordinates.

        Returns:
            float: Average speed in kilometers per hour.
        """
        distance_meters = self.get_distance()
        duration_seconds = self.get_duration()
        
        if duration_seconds == 0:
            return 0.0
        
        # Convert meters per second to kilometers per hour
        avg_speed_kmh = (distance_meters / duration_seconds) * 3.6
        return avg_speed_kmh

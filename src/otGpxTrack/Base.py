"""
Base module for GpxTrack class.
"""
import gpxpy
import numpy as np
import openturns as ot


class GpxTrack:
    """
    A class to represent and analyze a GPX track using OpenTURNS.
    
    Attributes:
        gpx (gpxpy.gpx.GPX): The parsed GPX object.
        points (list): List of track points.
        data (ot.Sample): OpenTURNS sample containing track data.
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
        self.data = None
        self._load_gpx()
        self._extract_points()
        self._create_openturns_sample()
    
    def _load_gpx(self):
        """Load and parse the GPX file."""
        with open(self.gpx_file_path, 'r') as f:
            self.gpx = gpxpy.parse(f)
    
    def _extract_points(self):
        """Extract track points from the GPX object."""
        for track in self.gpx.tracks:
            for segment in track.segments:
                self.points.extend(segment.points)
    
    def _create_openturns_sample(self):
        """Create an OpenTURNS sample from the track points."""
        if not self.points:
            raise ValueError("No points found in the GPX track.")
        
        # Extract data: latitude, longitude, elevation, time
        latitudes = []
        longitudes = []
        elevations = []
        times = []
        speeds = []
        
        for i, point in enumerate(self.points):
            latitudes.append(point.latitude)
            longitudes.append(point.longitude)
            elevations.append(point.elevation if point.elevation is not None else 0.0)
            times.append(point.time.timestamp() if point.time is not None else 0.0)
            
            # Calculate instantaneous speed
            if i > 0:
                prev_point = self.points[i-1]
                distance = point.distance_3d(prev_point)
                time_diff = (point.time - prev_point.time).total_seconds()
                speed = distance / time_diff if time_diff > 0 else 0.0
            else:
                speed = 0.0
            speeds.append(speed)
        
        # Create OpenTURNS sample
        data = np.column_stack([latitudes, longitudes, elevations, times, speeds])
        self.data = ot.Sample(data)
        self.data.setDescription(["Latitude", "Longitude", "Elevation", "Time", "Speed"])
    
    def get_distance(self):
        """
        Calculate the total distance of the track.
        
        Returns:
            float: Total distance in meters.
        """
        total_distance = 0.0
        for i in range(1, len(self.points)):
            total_distance += self.points[i].distance_3d(self.points[i-1])
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
    
    def get_average_speed(self):
        """
        Calculate the average speed of the track.
        
        Returns:
            float: Average speed in meters per second.
        """
        distance = self.get_distance()
        duration = self.get_duration()
        if duration == 0:
            return 0.0
        return distance / duration
    
    def get_openturns_sample(self):
        """
        Get the OpenTURNS sample containing the track data.
        
        Returns:
            ot.Sample: OpenTURNS sample.
        """
        return self.data

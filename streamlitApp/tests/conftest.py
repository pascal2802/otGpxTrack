"""
Pytest configuration and fixtures for Streamlit app tests.
"""

import os
import sys
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest


def get_test_file_path(filename):
    """Get the absolute path to a test file."""
    return os.path.join(os.path.dirname(__file__), '..', '..', 'firstexample', filename)


@pytest.fixture
def sample_track():
    """Fixture to load a sample GPX track."""
    # Mock the GpxTrack class if openturns is not available
    try:
        from otGpxTrack.Base import GpxTrack
        gpx_file = get_test_file_path("activity_19218242997.gpx")
        return GpxTrack(gpx_file)
    except ImportError:
        # Create a mock track for testing
        class MockPoint:
            def __init__(self, lat, lon, elev, time):
                self.latitude = lat
                self.longitude = lon
                self.elevation = elev
                self.time = time
                self.speed = 0.0
            
            def distance_3d(self, other):
                # Simple distance calculation (not accurate but for testing)
                return ((self.latitude - other.latitude)**2 + 
                        (self.longitude - other.longitude)**2 + 
                        (self.elevation - other.elevation)**2)**0.5 * 111111
        
        class MockTrack:
            def __init__(self):
                self.points = []
                self.data = None
                self.gpx_file_path = "mock.gpx"
                self._create_mock_data()
            
            def _create_mock_data(self):
                import numpy as np
                from datetime import datetime, timedelta
                
                # Create 100 mock points
                start_time = datetime(2024, 1, 1, 12, 0, 0)
                start_lat, start_lon = 48.8566, 2.3522  # Paris coordinates
                
                for i in range(100):
                    time = start_time + timedelta(seconds=i)
                    lat = start_lat + (i * 0.001)
                    lon = start_lon + (i * 0.001)
                    elev = i * 10
                    self.points.append(MockPoint(lat, lon, elev, time))
                
                # Create mock OpenTURNS sample data
                import numpy as np
                latitudes = [p.latitude for p in self.points]
                longitudes = [p.longitude for p in self.points]
                elevations = [p.elevation for p in self.points]
                times = [p.time.timestamp() for p in self.points]
                speeds = [0.0] * len(self.points)
                
                # Calculate speeds
                for i in range(1, len(self.points)):
                    distance = self.points[i].distance_3d(self.points[i-1])
                    time_diff = (self.points[i].time - self.points[i-1].time).total_seconds()
                    speeds[i] = distance / time_diff if time_diff > 0 else 0.0
                
                data = np.column_stack([latitudes, longitudes, elevations, times, speeds])
                
                # Mock OpenTURNS Sample
                class MockSample:
                    def __init__(self, data):
                        self.data = data
                        self.size = data.shape[0]
                        self.dimension = data.shape[1]
                        self.descriptions = ["Latitude", "Longitude", "Elevation", "Time", "Speed"]
                    
                    def getSize(self):
                        return self.size
                    
                    def getDimension(self):
                        return self.dimension
                    
                    def getDescription(self):
                        return self.descriptions
                    
                    def __getitem__(self, index):
                        if isinstance(index, int):
                            return self.data[index]
                        else:
                            return self.data[index]
                
                self.data = MockSample(data)
            
            def get_distance(self):
                total = 0.0
                for i in range(1, len(self.points)):
                    total += self.points[i].distance_3d(self.points[i-1])
                return total
            
            def get_duration(self):
                if len(self.points) < 2:
                    return 0.0
                return (self.points[-1].time - self.points[0].time).total_seconds()
            
            def get_average_speed(self):
                distance = self.get_distance()
                duration = self.get_duration()
                if duration == 0:
                    return 0.0
                return distance / duration
            
            def get_openturns_sample(self):
                return self.data
            
            def processSample(self, sample_size=100, method="ar1", **kwargs):
                # Mock process sample
                class MockProcessSample:
                    def __init__(self, size, dimension):
                        self.size = size
                        self.dimension = dimension
                    
                    def getSize(self):
                        return self.size
                    
                    def getDimension(self):
                        return self.dimension
                    
                    def computeQuantilePerComponent(self, quantiles):
                        # Return mock quantile data
                        results = []
                        for q in quantiles:
                            # Return a sample with the same structure
                            class MockQuantileSample:
                                def __init__(self, size):
                                    self.size = size
                                def __getitem__(self, index):
                                    return [index * 0.1]  # Mock data
                            results.append(MockQuantileSample(len(self.points)))
                        return results
                    
                    def getTimeGrid(self):
                        class MockTimeGrid:
                            def getN(self):
                                return len(self.points)
                        return MockTimeGrid()
                
                return MockProcessSample(sample_size, 1)
            
            def simulate_ar1_speeds(self, segment_indices, **kwargs):
                # Mock AR-1 simulation
                import numpy as np
                n_sims = kwargs.get('n_sims', 100)
                speeds = np.random.normal(5.0, 1.0, n_sims)
                
                class MockSample:
                    def __init__(self, data):
                        self.data = data
                        self.size = len(data)
                    def getSize(self):
                        return self.size
                    @staticmethod
                    def computeQuantilePerComponent(sample, quantile):
                        return np.percentile(sample.data, quantile * 100)
                
                mean_speed = np.mean(speeds)
                lower = np.percentile(speeds, 2.5)
                upper = np.percentile(speeds, 97.5)
                
                return mean_speed, lower, upper, MockSample(speeds)
            
            def get_best_segment_for_distance(self, target_distance):
                # Mock best segment
                return (0, min(10, len(self.points)-1), 5.0)
            
            def get_best_segment_for_time(self, target_time):
                # Mock best segment
                return (0, min(10, len(self.points)-1), 5.0)
            
            def plot_track(self, **kwargs):
                # Mock plot
                import matplotlib.pyplot as plt
                fig, ax = plt.subplots()
                return fig
        
        return MockTrack()

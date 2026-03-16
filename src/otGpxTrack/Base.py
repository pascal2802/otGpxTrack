"""
Base module for GpxTrack class.
"""
import gpxpy
import numpy as np
import openturns as ot


def generate_ar1_error(n_points, sigma_tot=2.5, phi=0.9):
    """
    Generate correlated error drift (AR-1 process) using OpenTURNS.
    
    Args:
        n_points (int): Number of points.
        sigma_tot (float): Total standard deviation.
        phi (float): Autoregressive coefficient.
        
    Returns:
        ot.Sample: Sample of errors.
    """
    sigma_w = sigma_tot * (1 - phi**2)**0.5
    errors = ot.Sample(n_points, 1)
    errors[0] = ot.Point([0.0])
    
    normal_dist = ot.Normal(0.0, sigma_w)
    for t in range(1, n_points):
        error = phi * errors[t-1][0] + normal_dist.getRealization()[0]
        errors[t] = ot.Point([error])
    
    return errors


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
    
    def simulate_ar1_speeds(self, segment_indices, sigma_tot=2.5, phi=0.9, n_sims=1000):
        """
        Simulate speeds using AR-1 model for a segment of the track.
        
        Args:
            segment_indices (tuple): Start and end indices of the segment.
            sigma_tot (float): Total standard deviation for AR-1 process.
            phi (float): Autoregressive coefficient.
            n_sims (int): Number of simulations.
            
        Returns:
            tuple: Mean speed, lower percentile, upper percentile, OpenTURNS sample of all simulated speeds.
        """
        start_idx, end_idx = segment_indices
        segment_points = self.points[start_idx:end_idx+1]
        n_pts = len(segment_points)
        
        if n_pts < 2:
            return 0, 0, 0, ot.Sample()
        
        # Convert latitude and longitude to meters
        lat_to_m = 111111
        lon_to_m = 111111 * np.cos(np.radians(segment_points[0].latitude))
        
        # Extract coordinates and time using OpenTURNS
        x_ref_data = [(p.longitude - segment_points[0].longitude) * lon_to_m for p in segment_points]
        y_ref_data = [(p.latitude - segment_points[0].latitude) * lat_to_m for p in segment_points]
        t_ref_data = [(p.time - segment_points[0].time).total_seconds() for p in segment_points]
        
        x_ref = ot.Sample(n_pts, 1)
        y_ref = ot.Sample(n_pts, 1)
        t_ref = ot.Sample(n_pts, 1)
        
        for i in range(n_pts):
            x_ref[i] = ot.Point([x_ref_data[i]])
            y_ref[i] = ot.Point([y_ref_data[i]])
            t_ref[i] = ot.Point([t_ref_data[i]])
        
        dt_total = t_ref[-1][0] - t_ref[0][0]
        
        # Simulate speeds using OpenTURNS
        v_simulees = ot.Sample(n_sims, 1)
        for i in range(n_sims):
            err_x = generate_ar1_error(n_pts, sigma_tot, phi)
            err_y = generate_ar1_error(n_pts, sigma_tot, phi)
            
            # Calculate cumulative distance of noisy wake
            dist_sim = 0.0
            for j in range(1, n_pts):
                dx = (x_ref[j][0] + err_x[j][0]) - (x_ref[j-1][0] + err_x[j-1][0])
                dy = (y_ref[j][0] + err_y[j][0]) - (y_ref[j-1][0] + err_y[j-1][0])
                dist_sim += (dx**2 + dy**2)**0.5
            
            speed = (dist_sim / dt_total) * 1.94384  # Convert to knots
            v_simulees[i] = ot.Point([speed])
        
        # Calculate statistics using OpenTURNS
        mean_speed = v_simulees.computeMean()[0]
        lower = ot.Sample.computeQuantilePerComponent(v_simulees, 0.025)[0]
        upper = ot.Sample.computeQuantilePerComponent(v_simulees, 0.975)[0]
        
        return mean_speed, lower, upper, v_simulees
    
    def _find_best_segment(self, target_value, is_distance=True):
        """
        Generic method to find the best segment of the track.
        
        Args:
            target_value (float): Target value (distance in meters or time in seconds).
            is_distance (bool): True for distance-based search, False for time-based search.
            
        Returns:
            tuple: Start index, end index, observed speed.
        """
        best_v_obs = 0
        best_indices = (0, 0)
        
        # Calculate cumulative values
        cum_values = [0.0]
        for i in range(1, len(self.points)):
            if is_distance:
                cum_values.append(cum_values[i-1] + self.points[i].distance_3d(self.points[i-1]))
            else:
                cum_values.append(cum_values[i-1] + (self.points[i].time - self.points[i-1].time).total_seconds())
        
        # Find best segment
        for i in range(len(self.points)):
            v_start = cum_values[i]
            for j in range(i+1, len(self.points)):
                if cum_values[j] - v_start >= target_value:
                    dt = (self.points[j].time - self.points[i].time).total_seconds()
                    if dt > 0:
                        if is_distance:
                            v = (target_value / dt) * 1.94384  # Convert to knots
                        else:
                            v = (self.points[j].distance_3d(self.points[i]) / target_value) * 1.94384  # Convert to knots
                        if v > best_v_obs:
                            best_v_obs = v
                            best_indices = (i, j)
                    break
        
        return best_indices[0], best_indices[1], best_v_obs
    
    def get_best_segment_for_distance(self, target_distance):
        """
        Find the best segment of the track for a given target distance.
        
        Args:
            target_distance (float): Target distance in meters.
            
        Returns:
            tuple: Start index, end index, observed speed.
        """
        return self._find_best_segment(target_distance, is_distance=True)
    
    def get_best_segment_for_time(self, target_time):
        """
        Find the best segment of the track for a given target time.
        
        Args:
            target_time (float): Target time in seconds.
            
        Returns:
            tuple: Start index, end index, observed speed.
        """
        return self._find_best_segment(target_time, is_distance=False)

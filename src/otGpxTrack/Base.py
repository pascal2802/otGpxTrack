"""
Base module for GpxTrack class.
"""

import gpxpy
import numpy as np
import openturns as ot
import matplotlib.pyplot as plt


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
    sigma_w = sigma_tot * (1 - phi**2) ** 0.5
    errors = ot.Sample(n_points, 1)
    errors[0] = ot.Point([0.0])

    normal_dist = ot.Normal(0.0, sigma_w)
    eps = normal_dist.getSample(n_points)
    for t in range(1, n_points):
        error = phi * errors[t - 1][0] + eps[t, 0]
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
        with open(self.gpx_file_path, "r") as f:
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
                prev_point = self.points[i - 1]
                distance = point.distance_3d(prev_point)
                time_diff = (point.time - prev_point.time).total_seconds()
                speed = distance / time_diff if time_diff > 0 else 0.0
            else:
                speed = 0.0
            speeds.append(speed)

        # Create OpenTURNS sample
        data = np.column_stack([latitudes, longitudes, elevations, times, speeds])
        self.data = ot.Sample(data)
        self.data.setDescription(
            ["Latitude", "Longitude", "Elevation", "Time", "Speed"]
        )

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

    def processSample(self, sample_size=1000, method="ar1", sigma_tot=2.5, phi=0.9, amplitude=1.0, scale=1.0):
        """
        Generate stochastic process realizations for instantaneous speeds.

        Args:
            sample_size (int): Number of realizations to generate (default: 1000).
            method (str): Method for generating the process ('ar1' for AR-1 process, 'gaussian' for Gaussian process).
            sigma_tot (float): Total standard deviation for AR-1 process.
            phi (float): Autoregressive coefficient for AR-1 process.
            amplitude (float): Amplitude parameter for Gaussian process covariance model.
            scale (float): Scale/length of correlation parameter for Gaussian process covariance model.

        Returns:
            ot.ProcessSample: Stochastic process sample with realizations of instantaneous speeds.
        """
        if not self.points or len(self.points) < 2:
            raise ValueError("Insufficient track points for process generation.")

        # Extract time mesh from the track
        time_values = []
        for point in self.points:
            time_value = point.time.timestamp() if point.time is not None else 0.0
            time_values.append(time_value)
        time_values = [t - time_values[0] for t in time_values]

        # Create 1D mesh for the time domain
        mesh = ot.Mesh(ot.Sample.BuildFromPoint(time_values))

        # Generate stochastic process realizations
        if method == "ar1":
            # Generate AR-1 process realizations for speeds using position errors
            # Convert latitude and longitude to meters for the reference point
            ref_point = self.points[0]
            lat_to_m = 111111.0
            lon_to_m = 111111.0 * np.cos(np.radians(ref_point.latitude))

            # Extract reference coordinates in meters
            x_ref = [
                (p.longitude - ref_point.longitude) * lon_to_m for p in self.points
            ]
            y_ref = [(p.latitude - ref_point.latitude) * lat_to_m for p in self.points]
            t_ref = [(p.time - ref_point.time).total_seconds() for p in self.points]

            # Generate process realizations
            process_realizations = ot.Sample(sample_size, len(self.points))

            for sim_idx in range(sample_size):
                # Generate AR-1 errors for X and Y coordinates (in meters)
                err_x = generate_ar1_error(len(self.points), sigma_tot, phi)
                err_y = generate_ar1_error(len(self.points), sigma_tot, phi)

                # Calculate noisy trajectory and compute instantaneous speeds
                for i in range(len(self.points)):
                    if i == 0:
                        # First point has no speed
                        simulated_speed = 0.0
                    else:
                        # Calculate distance between consecutive noisy points
                        dx = (x_ref[i] + err_x[i][0]) - (x_ref[i - 1] + err_x[i - 1][0])
                        dy = (y_ref[i] + err_y[i][0]) - (y_ref[i - 1] + err_y[i - 1][0])
                        dt = t_ref[i] - t_ref[i - 1]
                        if dt > 0:
                            simulated_speed = np.sqrt(dx**2 + dy**2) / dt
                        else:
                            simulated_speed = 0.0
                    process_realizations[sim_idx, i] = simulated_speed

            # Create ProcessSample using the correct constructor
            # ProcessSample(mesh, K, d) where K=number of fields, d=dimension
            process_sample = ot.ProcessSample(mesh, sample_size, 1)

            # Set the values for each field
            for sim_idx in range(sample_size):
                # Convert the Point to a Sample for the Field constructor
                # The Sample should have dimension 1 and size equal to number of vertices
                field_values = ot.Sample(len(self.points), 1)
                for i in range(len(self.points)):
                    field_values[i, 0] = process_realizations[sim_idx, i]
                process_sample[sim_idx] = ot.Field(mesh, field_values)

            return process_sample
        elif method == "gaussian":
            # Generate Gaussian process realizations for speeds using position errors
            # Convert latitude and longitude to meters for the reference point
            ref_point = self.points[0]
            lat_to_m = 111111.0
            lon_to_m = 111111.0 * np.cos(np.radians(ref_point.latitude))

            # Extract reference coordinates in meters
            x_ref = [
                (p.longitude - ref_point.longitude) * lon_to_m for p in self.points
            ]
            y_ref = [(p.latitude - ref_point.latitude) * lat_to_m for p in self.points]
            t_ref = [(p.time - ref_point.time).total_seconds() for p in self.points]

            # Create time mesh for the Gaussian process
            time_values = []
            for point in self.points:
                time_value = point.time.timestamp() if point.time is not None else 0.0
                time_values.append(time_value)
            time_values = [t - time_values[0] for t in time_values]
            mesh = ot.Mesh(ot.Sample.BuildFromPoint(time_values))

            # Create covariance model for the Gaussian process
            # Using AbsoluteExponential covariance model
            # Parameters must be passed as lists
            cov_model = ot.AbsoluteExponential([scale], [amplitude])

            # Create Gaussian processes for X and Y errors
            gaussian_process_x = ot.GaussianProcess(cov_model, mesh)
            gaussian_process_y = ot.GaussianProcess(cov_model, mesh)

            # Generate process realizations
            process_realizations = ot.Sample(sample_size, len(self.points))

            for sim_idx in range(sample_size):
                # Generate Gaussian process errors for X and Y coordinates (in meters)
                err_x_field = gaussian_process_x.getRealization()
                err_y_field = gaussian_process_y.getRealization()
                
                # Convert fields to samples for easier access
                err_x = ot.Sample(len(self.points), 1)
                err_y = ot.Sample(len(self.points), 1)
                for i in range(len(self.points)):
                    err_x[i, 0] = err_x_field[i, 0]
                    err_y[i, 0] = err_y_field[i, 0]

                # Calculate noisy trajectory and compute instantaneous speeds
                for i in range(len(self.points)):
                    if i == 0:
                        # First point has no speed
                        simulated_speed = 0.0
                    else:
                        # Calculate distance between consecutive noisy points
                        dx = (x_ref[i] + err_x[i][0]) - (x_ref[i - 1] + err_x[i - 1][0])
                        dy = (y_ref[i] + err_y[i][0]) - (y_ref[i - 1] + err_y[i - 1][0])
                        dt = t_ref[i] - t_ref[i - 1]
                        if dt > 0:
                            simulated_speed = np.sqrt(dx**2 + dy**2) / dt
                        else:
                            simulated_speed = 0.0
                    process_realizations[sim_idx, i] = simulated_speed

            # Create ProcessSample using the correct constructor
            # ProcessSample(mesh, K, d) where K=number of fields, d=dimension
            process_sample = ot.ProcessSample(mesh, sample_size, 1)

            # Set the values for each field
            for sim_idx in range(sample_size):
                # Convert the Point to a Sample for the Field constructor
                # The Sample should have dimension 1 and size equal to number of vertices
                field_values = ot.Sample(len(self.points), 1)
                for i in range(len(self.points)):
                    field_values[i, 0] = process_realizations[sim_idx, i]
                process_sample[sim_idx] = ot.Field(mesh, field_values)

            return process_sample
        else:
            raise ValueError(
                f"Unsupported method: {method}. Only 'ar1' and 'gaussian' are currently supported."
            )

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
        segment_points = self.points[start_idx : end_idx + 1]
        n_pts = len(segment_points)

        if n_pts < 2:
            return 0, 0, 0, ot.Sample()

        # Convert latitude and longitude to meters
        lat_to_m = 111111
        lon_to_m = 111111 * np.cos(np.radians(segment_points[0].latitude))

        # Extract coordinates and time using OpenTURNS
        x_ref_data = [
            (p.longitude - segment_points[0].longitude) * lon_to_m
            for p in segment_points
        ]
        y_ref_data = [
            (p.latitude - segment_points[0].latitude) * lat_to_m for p in segment_points
        ]
        t_ref_data = [
            (p.time - segment_points[0].time).total_seconds() for p in segment_points
        ]

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
                dx = (x_ref[j][0] + err_x[j][0]) - (x_ref[j - 1][0] + err_x[j - 1][0])
                dy = (y_ref[j][0] + err_y[j][0]) - (y_ref[j - 1][0] + err_y[j - 1][0])
                dist_sim += (dx**2 + dy**2) ** 0.5

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
                cum_values.append(
                    cum_values[i - 1] + self.points[i].distance_3d(self.points[i - 1])
                )
            else:
                cum_values.append(
                    cum_values[i - 1]
                    + (self.points[i].time - self.points[i - 1].time).total_seconds()
                )

        # Find best segment
        for i in range(len(self.points)):
            v_start = cum_values[i]
            for j in range(i + 1, len(self.points)):
                if cum_values[j] - v_start >= target_value:
                    dt = (self.points[j].time - self.points[i].time).total_seconds()
                    if dt > 0:
                        if is_distance:
                            v = (target_value / dt) * 1.94384  # Convert to knots
                        else:
                            v = (
                                self.points[j].distance_3d(self.points[i])
                                / target_value
                            ) * 1.94384  # Convert to knots
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

    def plot_track(
        self, figsize=(10, 8), title="GPX Track", save_path=None, speed_unit="m/s"
    ):
        """
        Plot the GPX track with points colored by speed using a jet colormap.

        Args:
            figsize (tuple): Figure size (width, height).
            title (str): Plot title.
            save_path (str): Optional path to save the plot.
            speed_unit (str): Unit for speed display ('m/s', 'km/h', or 'knots').

        Returns:
            matplotlib.figure.Figure: The created figure.
        """
        if not self.points:
            raise ValueError("No points to plot.")

        # Extract coordinates and speeds
        longitudes = [point.longitude for point in self.points]
        latitudes = [point.latitude for point in self.points]
        speeds = [
            point.speed if hasattr(point, "speed") else 0.0 for point in self.points
        ]

        # Use speeds from OpenTURNS sample if available
        if self.data is not None and self.data.getDimension() >= 5:
            speeds = [self.data[i][4] for i in range(self.data.getSize())]

        # Convert speeds to desired unit
        if speed_unit == "km/h":
            speeds = [s * 3.6 for s in speeds]
            unit_label = "Speed (km/h)"
        elif speed_unit == "knots":
            speeds = [s * 1.94384 for s in speeds]
            unit_label = "Speed (knots)"
        else:  # m/s
            unit_label = "Speed (m/s)"

        # Create the plot
        fig, ax = plt.subplots(figsize=figsize)

        # Plot points colored by speed
        scatter = ax.scatter(
            longitudes, latitudes, c=speeds, cmap="jet", s=10, alpha=0.7
        )

        # Add colorbar
        cbar = plt.colorbar(scatter, ax=ax)
        cbar.set_label(unit_label)

        # Set plot properties
        ax.set_title(title)
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        ax.grid(True, alpha=0.3)
        ax.set_aspect("equal")

        # Save if path provided
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")

        return fig

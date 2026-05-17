"""
Visualization functions for GPX track analysis.

This module provides functions to create various plots for GPX track data.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib import cm


def plot_track_with_speed(track, figsize=(12, 8), speed_unit="knots", dpi=100):
    """
    Plot the GPX track with points colored by speed.
    
    Args:
        track: GpxTrack instance
        figsize: Figure size (width, height)
        speed_unit: Speed unit ('m/s', 'km/h', 'knots')
        dpi: DPI for the figure
        
    Returns:
        matplotlib.figure.Figure: The created figure
    """
    if not track.points:
        raise ValueError("No points to plot.")
    
    # Extract coordinates and speeds
    longitudes = [point.longitude for point in track.points]
    latitudes = [point.latitude for point in track.points]
    
    # Get speeds from OpenTURNS sample
    if track.data is not None and track.data.getDimension() >= 5:
        speeds = [track.data[i][4] for i in range(track.data.getSize())]
    else:
        speeds = [0.0] * len(track.points)
    
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
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    
    # Plot points colored by speed
    scatter = ax.scatter(
        longitudes, 
        latitudes, 
        c=speeds, 
        cmap="jet", 
        s=20, 
        alpha=0.8,
        edgecolors="none"
    )
    
    # Add colorbar
    cbar = plt.colorbar(scatter, ax=ax, shrink=0.8)
    cbar.set_label(unit_label, fontsize=10)
    
    # Set plot properties
    ax.set_title("GPX Track with Speed Coloring", fontsize=14, fontweight="bold")
    ax.set_xlabel("Longitude", fontsize=12)
    ax.set_ylabel("Latitude", fontsize=12)
    ax.grid(True, alpha=0.3)
    ax.set_aspect("equal")
    
    # Adjust layout
    plt.tight_layout()
    
    return fig


def plot_speed_over_time(track, figsize=(14, 6), speed_unit="knots", 
                         process_sample=None, dpi=100):
    """
    Plot speed over time with optional confidence intervals.
    
    Args:
        track: GpxTrack instance
        figsize: Figure size (width, height)
        speed_unit: Speed unit ('m/s', 'km/h', 'knots')
        process_sample: Optional ProcessSample for confidence intervals
        dpi: DPI for the figure
        
    Returns:
        matplotlib.figure.Figure: The created figure
    """
    if not track.points:
        raise ValueError("No points to plot.")
    
    # Extract time values and speeds
    time_values = []
    observed_speeds = []
    
    for i, point in enumerate(track.points):
        time_value = point.time.timestamp() if point.time is not None else 0.0
        time_values.append(time_value)
        if track.data is not None and track.data.getDimension() >= 5:
            observed_speeds.append(track.data[i][4])
        else:
            observed_speeds.append(0.0)
    
    # Convert to relative time (seconds since start)
    if time_values:
        start_time = time_values[0]
        time_values = [t - start_time for t in time_values]
    
    # Convert speeds to desired unit
    if speed_unit == "km/h":
        observed_speeds = [s * 3.6 for s in observed_speeds]
        unit_label = "Speed (km/h)"
    elif speed_unit == "knots":
        observed_speeds = [s * 1.94384 for s in observed_speeds]
        unit_label = "Speed (knots)"
    else:  # m/s
        unit_label = "Speed (m/s)"
    
    # Create the plot
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    
    # Plot observed speeds
    ax.plot(time_values, observed_speeds, "b-", label="Observed Speed", 
            linewidth=2, alpha=0.8)
    
    # Add confidence intervals if process_sample is provided
    if process_sample is not None:
        try:
            # Calculate quantiles
            quantiles = process_sample.computeQuantilePerComponent([0.025, 0.975])
            
            # Extract quantile values
            n_points = len(track.points)
            quantile_025 = []
            quantile_975 = []
            
            for i in range(n_points):
                q025 = quantiles[0][i][0]
                q975 = quantiles[1][i][0]
                
                # Convert to desired unit
                if speed_unit == "km/h":
                    q025 *= 3.6
                    q975 *= 3.6
                elif speed_unit == "knots":
                    q025 *= 1.94384
                    q975 *= 1.94384
                
                quantile_025.append(q025)
                quantile_975.append(q975)
            
            # Plot confidence interval
            ax.fill_between(
                time_values,
                quantile_025,
                quantile_975,
                alpha=0.3,
                color="blue",
                label="95% Confidence Interval",
            )
        except Exception as e:
            print(f"Error calculating confidence intervals: {e}")
    
    # Customize the plot
    ax.set_title("Speed Over Time", fontsize=14, fontweight="bold")
    ax.set_xlabel("Time (seconds)", fontsize=12)
    ax.set_ylabel(unit_label, fontsize=12)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=10)
    
    # Adjust layout
    plt.tight_layout()
    
    return fig


def plot_elevation_profile(track, figsize=(14, 6), dpi=100):
    """
    Plot elevation profile over distance.
    
    Args:
        track: GpxTrack instance
        figsize: Figure size (width, height)
        dpi: DPI for the figure
        
    Returns:
        matplotlib.figure.Figure: The created figure
    """
    if not track.points:
        raise ValueError("No points to plot.")
    
    # Calculate cumulative distance
    cumulative_distances = [0.0]
    for i in range(1, len(track.points)):
        distance = track.points[i].distance_3d(track.points[i - 1])
        cumulative_distances.append(cumulative_distances[i - 1] + distance)
    
    # Extract elevations
    elevations = []
    for point in track.points:
        elevation = point.elevation if point.elevation is not None else 0.0
        elevations.append(elevation)
    
    # Create the plot
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    
    # Plot elevation profile
    ax.plot(cumulative_distances, elevations, "g-", 
            linewidth=2, label="Elevation")
    
    # Customize the plot
    ax.set_title("Elevation Profile", fontsize=14, fontweight="bold")
    ax.set_xlabel("Distance (meters)", fontsize=12)
    ax.set_ylabel("Elevation (meters)", fontsize=12)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=10)
    
    # Adjust layout
    plt.tight_layout()
    
    return fig


def plot_speed_distribution(track, figsize=(12, 6), speed_unit="knots", 
                            bins=30, dpi=100):
    """
    Plot histogram of speed distribution.
    
    Args:
        track: GpxTrack instance
        figsize: Figure size (width, height)
        speed_unit: Speed unit ('m/s', 'km/h', 'knots')
        bins: Number of bins for histogram
        dpi: DPI for the figure
        
    Returns:
        matplotlib.figure.Figure: The created figure
    """
    if not track.points:
        raise ValueError("No points to plot.")
    
    # Get speeds from OpenTURNS sample
    if track.data is not None and track.data.getDimension() >= 5:
        speeds = [track.data[i][4] for i in range(track.data.getSize())]
    else:
        speeds = [0.0] * len(track.points)
    
    # Convert speeds to desired unit
    if speed_unit == "km/h":
        speeds = [s * 3.6 for s in speeds]
        unit_label = "Speed (km/h)"
    elif speed_unit == "knots":
        speeds = [s * 1.94384 for s in speeds]
        unit_label = "Speed (knots)"
    else:  # m/s
        unit_label = "Speed (m/s)"
    
    # Filter out zero speeds (if any)
    speeds = [s for s in speeds if s > 0]
    
    if not speeds:
        speeds = [0.0]
    
    # Create the plot
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    
    # Plot histogram
    n, bins, patches = ax.hist(speeds, bins=bins, color="#1f77b4", 
                               edgecolor="black", alpha=0.7)
    
    # Customize the plot
    ax.set_title("Speed Distribution", fontsize=14, fontweight="bold")
    ax.set_xlabel(unit_label, fontsize=12)
    ax.set_ylabel("Frequency", fontsize=12)
    ax.grid(True, alpha=0.3)
    
    # Add mean line
    mean_speed = np.mean(speeds)
    ax.axvline(mean_speed, color="red", linestyle="--", 
               linewidth=2, label=f"Mean: {mean_speed:.2f}")
    ax.legend(fontsize=10)
    
    # Adjust layout
    plt.tight_layout()
    
    return fig


def create_comparison_plot(track, figsize=(14, 8), dpi=100):
    """
    Create a comparison plot with multiple subplots.
    
    Args:
        track: GpxTrack instance
        figsize: Figure size (width, height)
        dpi: DPI for the figure
        
    Returns:
        matplotlib.figure.Figure: The created figure
    """
    if not track.points:
        raise ValueError("No points to plot.")
    
    # Create subplots
    fig, axes = plt.subplots(2, 2, figsize=figsize, dpi=dpi)
    
    # Plot 1: Track Map
    longitudes = [point.longitude for point in track.points]
    latitudes = [point.latitude for point in track.points]
    speeds = [track.data[i][4] * 1.94384 for i in range(track.data.getSize())]  # knots
    
    axes[0, 0].scatter(longitudes, latitudes, c=speeds, cmap="jet", s=10, alpha=0.7)
    axes[0, 0].set_title("Track Map")
    axes[0, 0].set_xlabel("Longitude")
    axes[0, 0].set_ylabel("Latitude")
    axes[0, 0].grid(True, alpha=0.3)
    axes[0, 0].set_aspect("equal")
    
    # Plot 2: Speed Over Time
    time_values = [(p.time.timestamp() - track.points[0].time.timestamp()) 
                   for p in track.points]
    speeds_mps = [track.data[i][4] for i in range(track.data.getSize())]
    
    axes[0, 1].plot(time_values, speeds_mps, "b-", linewidth=1.5)
    axes[0, 1].set_title("Speed Over Time")
    axes[0, 1].set_xlabel("Time (s)")
    axes[0, 1].set_ylabel("Speed (m/s)")
    axes[0, 1].grid(True, alpha=0.3)
    
    # Plot 3: Elevation Profile
    cumulative_distances = [0.0]
    for i in range(1, len(track.points)):
        distance = track.points[i].distance_3d(track.points[i - 1])
        cumulative_distances.append(cumulative_distances[i - 1] + distance)
    
    elevations = [p.elevation if p.elevation is not None else 0.0 
                  for p in track.points]
    
    axes[1, 0].plot(cumulative_distances, elevations, "g-", linewidth=1.5)
    axes[1, 0].set_title("Elevation Profile")
    axes[1, 0].set_xlabel("Distance (m)")
    axes[1, 0].set_ylabel("Elevation (m)")
    axes[1, 0].grid(True, alpha=0.3)
    
    # Plot 4: Speed Distribution
    speeds_nonzero = [s for s in speeds_mps if s > 0]
    if speeds_nonzero:
        axes[1, 1].hist(speeds_nonzero, bins=30, color="#1f77b4", 
                       edgecolor="black", alpha=0.7)
        axes[1, 1].set_title("Speed Distribution")
        axes[1, 1].set_xlabel("Speed (m/s)")
        axes[1, 1].set_ylabel("Frequency")
        axes[1, 1].grid(True, alpha=0.3)
    
    # Adjust layout
    plt.tight_layout()
    
    return fig

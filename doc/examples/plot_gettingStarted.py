"""
Getting Started with GpxTrack
==============================

This example demonstrates the basic functionality of the GpxTrack class.
"""

# %%
# Import required modules
from otGpxTrack.Base import GpxTrack
import os

# %%
# Get the path to the example GPX file
example_file = os.path.join("..", "..", "firstexample", "activity_19218242997.gpx")

# %%
# Load the GPX track
track = GpxTrack(example_file)

# %%
# Get basic track information
print("Basic Track Information:")
print(f"  Distance: {track.get_distance():.2f} meters")
print(f"  Duration: {track.get_duration():.2f} seconds")
print(f"  Average Speed: {track.get_average_speed():.2f} m/s")

# %%
# Get OpenTURNS sample
sample = track.get_openturns_sample()
print(f"\nOpenTURNS Sample:")
print(f"  Size: {sample.getSize()}")
print(f"  Dimension: {sample.getDimension()}")
print(f"  Descriptions: {sample.getDescription()}")

# %%
# Find best segments
print("\nBest Segments:")
start_idx, end_idx, speed = track.get_best_segment_for_distance(500)
print(f"  Best 500m: {speed:.2f} knots")

start_idx, end_idx, speed = track.get_best_segment_for_time(10.0)
print(f"  Best 10s: {speed:.2f} knots")

# %%
# AR-1 Simulation for best segments
print("\nAR-1 Simulation Results:")

# Simulate for best 500m segment
mean_speed, lower, upper, _ = track.simulate_ar1_speeds((start_idx, end_idx))
print(f"  Best 500m segment (AR-1):")
print(f"    Mean speed: {mean_speed:.2f} knots")
print(f"    95% CI: [{lower:.2f}, {upper:.2f}] knots")

# Simulate for best 10s segment
start_idx, end_idx, _ = track.get_best_segment_for_time(10.0)
mean_speed, lower, upper, _ = track.simulate_ar1_speeds(
    (start_idx, end_idx), sigma_tot=1.2, phi=0.9
)
print(f"  Best 10s segment (AR-1):")
print(f"    Mean speed: {mean_speed:.2f} knots")
print(f"    95% CI: [{lower:.2f}, {upper:.2f}] knots")

# %%
# Generate stochastic process realizations for instantaneous speeds
print("\nGenerating stochastic process realizations...")
process_sample = track.processSample(
    sample_size=100, method="ar1", sigma_tot=1.2, phi=0.9
)

# %%
# Plot instantaneous speeds with 95% confidence interval using OpenTURNS methods
import matplotlib.pyplot as plt

print("\nPlotting instantaneous speeds with confidence intervals...")
fig, ax = plt.subplots(figsize=(14, 6))

# Extract time values and observed speeds
time_values = []
observed_speeds = []
for i, point in enumerate(track.points):
    time_value = point.time.timestamp() if point.time is not None else 0.0
    time_values.append(time_value)
    observed_speeds.append(track.data[i][4] * 1.94384)  # Convert to knots

# Use OpenTURNS computeQuantilePerComponent method directly on ProcessSample
quantiles = process_sample.computeQuantilePerComponent([0.025, 0.975])
# Extract quantile values - each quantile is a Sample in the ProcessSample
quantile_025 = [
    quantiles[0][i][0] * 1.94384 for i in range(len(track.points))
]  # With conversion to knots
quantile_975 = [
    quantiles[1][i][0] * 1.94384 for i in range(len(track.points))
]  # With conversion to knots

# Plot observed speeds
ax.plot(time_values, observed_speeds, "b-", label="Observed Speed", linewidth=2)

# Plot confidence interval
ax.fill_between(
    time_values,
    quantile_025,
    quantile_975,
    alpha=0.3,
    color="blue",
    label="95% Confidence Interval",
)

# Customize the plot
ax.set_title(
    "Instantaneous Speeds with 95% Confidence Interval (AR-1 Process)", fontsize=14
)
ax.set_xlabel("Time (seconds since epoch)", fontsize=12)
ax.set_ylabel("Speed (knots)", fontsize=12)
ax.grid(True, alpha=0.3)
ax.legend(fontsize=10)

# Save the speed plot
speed_plot_path = "instantaneous_speeds_with_ci.png"
fig.savefig(speed_plot_path, dpi=300, bbox_inches="tight")
print(f"Speed plot saved to: {speed_plot_path}")

# %%
# Plot the track with speed in knots
print("\nGenerating track plot...")
fig = track.plot_track(title="Example GPX Track", figsize=(12, 8), speed_unit="knots")

# %%
# Save the plot
save_path = "getting_started_plot.png"
fig.savefig(save_path, dpi=300, bbox_inches="tight")
print(f"Plot saved to: {save_path}")

# %%
# Show the plot (in interactive environments)
# plt.show()

print("\nExample completed successfully!")

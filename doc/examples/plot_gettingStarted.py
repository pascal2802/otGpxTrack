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
example_file = os.path.join('..', '..', 'firstexample', 'activity_19218242997.gpx')

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
mean_speed, lower, upper, _ = track.simulate_ar1_speeds((start_idx, end_idx))
print(f"  Best 10s segment (AR-1):")
print(f"    Mean speed: {mean_speed:.2f} knots")
print(f"    95% CI: [{lower:.2f}, {upper:.2f}] knots")

# %%
# Plot the track with speed in knots
print("\nGenerating plot...")
fig = track.plot_track(title="Example GPX Track", figsize=(12, 8), speed_unit="knots")

# %%
# Save the plot
save_path = 'getting_started_plot.png'
fig.savefig(save_path, dpi=300, bbox_inches='tight')
print(f"Plot saved to: {save_path}")

# %%
# Show the plot (in interactive environments)
# plt.show()

print("\nExample completed successfully!")

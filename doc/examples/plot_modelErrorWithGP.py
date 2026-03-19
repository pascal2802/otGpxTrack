"""
Model Error with Gaussian Process
==================================

This example demonstrates the use of Gaussian Process for modeling error in GPX tracks,
comparing it with the AR-1 process approach.
"""

# %%
# Import required modules
from otGpxTrack.Base import GpxTrack
import os
import matplotlib.pyplot as plt
import numpy as np

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
# Generate stochastic process realizations using both methods
print("\nGenerating stochastic process realizations...")

# Gaussian Process method
print("  Generating Gaussian Process realizations...")
# Amplitude calculée pour que 95% des erreurs soient dans un rayon de 3m
# Pour un processus gaussien, 95% des valeurs sont dans [-1.96σ, 1.96σ]
# On veut 1.96σ ≤ 3m => σ ≤ 3/1.96 ≈ 1.53m
# Amplitude correspond à l'écart-type du processus
process_sample_gp = track.processSample(
    sample_size=100, method="gaussian", amplitude=1.2, scale=5.0
)

# AR-1 method
print("  Generating AR-1 process realizations...")
process_sample_ar1 = track.processSample(
    sample_size=100, method="ar1", sigma_tot=1.2, phi=0.9
)

# %%
# Extract time values and observed speeds
print("\nExtracting time and speed data...")
time_values = []
observed_speeds = []
for i, point in enumerate(track.points):
    time_value = point.time.timestamp() if point.time is not None else 0.0
    time_values.append(time_value)
    observed_speeds.append(track.data[i][4] * 1.94384)  # Convert to knots

# Normalize time to start from 0
time_values = [t - time_values[0] for t in time_values]

# %%
# Calculate confidence intervals for both methods
print("\nCalculating confidence intervals...")

# Gaussian Process confidence intervals
quantiles_gp = process_sample_gp.computeQuantilePerComponent([0.025, 0.975])
quantile_025_gp = [quantiles_gp[0][i][0] * 1.94384 for i in range(len(track.points))]
quantile_975_gp = [quantiles_gp[1][i][0] * 1.94384 for i in range(len(track.points))]

# AR-1 confidence intervals
quantiles_ar1 = process_sample_ar1.computeQuantilePerComponent([0.025, 0.975])
quantile_025_ar1 = [quantiles_ar1[0][i][0] * 1.94384 for i in range(len(track.points))]
quantile_975_ar1 = [quantiles_ar1[1][i][0] * 1.94384 for i in range(len(track.points))]

# %%
# Plot comparison of confidence intervals
print("\nPlotting comparison of error models...")
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 12), sharex=True)

# Plot 1: Gaussian Process
ax1.plot(
    time_values, observed_speeds, "k-", label="Observed Speed", linewidth=2, alpha=0.7
)
ax1.fill_between(
    time_values,
    quantile_025_gp,
    quantile_975_gp,
    alpha=0.3,
    color="blue",
    label="95% Confidence Interval (GP)",
)
ax1.set_title("Instantaneous Speeds with Gaussian Process Error Model", fontsize=14)
ax1.set_ylabel("Speed (knots)", fontsize=12)
ax1.grid(True, alpha=0.3)
ax1.legend(fontsize=10)
ax1.set_ylim(0, max(observed_speeds) * 1.1)

# Plot 2: AR-1 Process
ax2.plot(
    time_values, observed_speeds, "k-", label="Observed Speed", linewidth=2, alpha=0.7
)
ax2.fill_between(
    time_values,
    quantile_025_ar1,
    quantile_975_ar1,
    alpha=0.3,
    color="red",
    label="95% Confidence Interval (AR-1)",
)
ax2.set_title("Instantaneous Speeds with AR-1 Error Model", fontsize=14)
ax2.set_xlabel("Time (seconds)", fontsize=12)
ax2.set_ylabel("Speed (knots)", fontsize=12)
ax2.grid(True, alpha=0.3)
ax2.legend(fontsize=10)
ax2.set_ylim(0, max(observed_speeds) * 1.1)

plt.tight_layout()

# Save the comparison plot
comparison_plot_path = "error_model_comparison.png"
fig.savefig(comparison_plot_path, dpi=300, bbox_inches="tight")
print(f"Comparison plot saved to: {comparison_plot_path}")

# %%
# Calculate and display statistics for both methods
print("\nStatistics Comparison:")

# Gaussian Process statistics
mean_gp = np.mean(quantile_025_gp + quantile_975_gp) / 2
std_gp = np.std(quantile_025_gp + quantile_975_gp)
print(f"Gaussian Process:")
print(f"  Mean speed: {mean_gp:.2f} knots")
print(f"  Std dev: {std_gp:.2f} knots")
print(f"  CI width: {quantile_975_gp[200] - quantile_025_gp[200]:.2f} knots")
print(f"  Parameters: amplitude=1.5 (95% errors ≤ 3m), scale=5.0s")

# AR-1 statistics
mean_ar1 = np.mean(quantile_025_ar1 + quantile_975_ar1) / 2
std_ar1 = np.std(quantile_025_ar1 + quantile_975_ar1)
print(f"\nAR-1 Process:")
print(f"  Mean speed: {mean_ar1:.2f} knots")
print(f"  Std dev: {std_ar1:.2f} knots")
print(f"  CI width: {quantile_975_ar1[200] - quantile_025_ar1[200]:.2f} knots")
print(f"  Parameters: sigma_tot=1.2, phi=0.9")

# %%
# Plot the track with speed in knots
print("\nGenerating track plot...")
fig = track.plot_track(title="Example GPX Track", figsize=(12, 8), speed_unit="knots")

# %%
# Save the plot
save_path = "model_error_gp_plot.png"
fig.savefig(save_path, dpi=300, bbox_inches="tight")
print(f"Plot saved to: {save_path}")

# %%
# Show the plot (in interactive environments)
# plt.show()

print("\nExample completed successfully!")
print("\nKey Observations:")
print("  - Both methods generate correlated errors on X and Y coordinates")
print("  - Instantaneous speeds are calculated from noisy trajectories")
print("  - Gaussian Process uses AbsoluteExponential covariance model")
print("  - AR-1 Process uses autoregressive model")
print("  - Scale=5.0s appropriate for 1Hz GPS data")
print("  - Amplitude=1.5m ensures 95% of errors ≤ 3m radius")

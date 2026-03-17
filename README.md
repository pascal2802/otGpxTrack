# otGpxTrack

A Python library for statistical analysis of GPX tracks using OpenTURNS.

## Features

- Parse and analyze GPX track files
- Calculate basic track statistics (distance, duration, average speed)
- Generate OpenTURNS samples from track data
- AR-1 process simulation for speed analysis
- Find best segments for distance or time targets

## Installation

```bash
# Clone the repository
git clone https://github.com/pascal2802/otGpxTrack.git
cd otGpxTrack

# Install dependencies using uv
uv sync
```

## Usage

### Basic Example

```python
from otGpxTrack.Base import GpxTrack

# Load a GPX file
track = GpxTrack("path/to/your/track.gpx")

# Get basic statistics
print(f"Distance: {track.get_distance()} meters")
print(f"Duration: {track.get_duration()} seconds")
print(f"Average speed: {track.get_average_speed()} m/s")

# Get OpenTURNS sample
sample = track.get_openturns_sample()
print(f"Sample size: {sample.getSize()}")
print(f"Sample dimension: {sample.getDimension()}")
print(f"Descriptions: {sample.getDescription()}")
```

### AR-1 Simulation

```python
# Find best segment for 500 meters
start_idx, end_idx, speed = track.get_best_segment_for_distance(500)

# Simulate speeds using AR-1 model
mean_speed, lower, upper, speeds = track.simulate_ar1_speeds(
    (start_idx, end_idx), 
    sigma_tot=2.5, 
    phi=0.9, 
    n_sims=1000
)

print(f"Mean speed: {mean_speed:.2f} knots")
print(f"95% CI: [{lower:.2f}, {upper:.2f}]")
```

### Stochastic Process Generation

```python
# Generate stochastic process realizations for instantaneous speeds
process_sample = track.processSample(sample_size=1000, method='ar1')

print(f"Process sample size: {process_sample.getSize()}")
print(f"Process dimension: {process_sample.getDimension()}")
print(f"Time grid vertices: {process_sample.getMesh().getVerticesNumber()}")

# Compute quantiles for confidence intervals
quantiles = process_sample.computeQuantilePerComponent([0.025, 0.975])
print(f"95% CI at first point: [{quantiles[0][0][0]:.2f}, {quantiles[1][0][0]:.2f}] knots")
```

### Best Segment Analysis

```python
# Find best segment for 500 meters
start_idx, end_idx, speed = track.get_best_segment_for_distance(500)
print(f"Best 500m segment: speed = {speed:.2f} knots")

# Find best segment for 10 seconds
start_idx, end_idx, speed = track.get_best_segment_for_time(10.0)
print(f"Best 10s segment: speed = {speed:.2f} knots")
```

## Testing

Run the test suite with:

```bash
uv run pytest
```

## Project Structure

```
otGpxTrack/
├── src/
│   └── otGpxTrack/
│       ├── __init__.py
│       └── Base.py          # Main GpxTrack class
├── test/
│   └── test_gpxtrack.py    # Test suite
├── firstexample/           # Example GPX files
├── pyproject.toml          # Project configuration
└── README.md               # This file
```

## Dependencies

- Python 3.10+
- OpenTURNS
- gpxpy
- numpy
- pandas
- matplotlib (for visualization)

## License

This project is licensed under the MIT License.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## Acknowledgments

- Inspired by the firstexample/gpxAnalyse.py script
- Uses OpenTURNS for statistical analysis
- Built with modern Python tooling (uv, pytest)

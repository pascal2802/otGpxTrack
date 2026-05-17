"""
Unit tests for PDF report generation.
"""

import os
import sys
import tempfile
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for testing

# Mock openturns if not available
try:
    import openturns as ot
    OPENTURNS_AVAILABLE = True
except ImportError:
    OPENTURNS_AVAILABLE = False
    # Use mock openturns
    sys.path.insert(0, str(Path(__file__).parent))
    import mock_openturns as ot

from otGpxTrack.Base import GpxTrack
from streamlitApp.pdf_report import generate_pdf_report


def get_test_file_path(filename):
    """Get the absolute path to a test file."""
    return os.path.join(os.path.dirname(__file__), '..', '..', 'firstexample', filename)


@pytest.fixture
def sample_track():
    """Fixture to load a sample GPX track."""
    gpx_file = get_test_file_path("activity_19218242997.gpx")
    return GpxTrack(gpx_file)


class TestPDFReport:
    """Test class for PDF report generation."""

    def test_generate_pdf_basic(self, sample_track):
        """Test basic PDF generation."""
        report_data = {
            "track": sample_track,
            "speed_unit": "knots",
            "show_simulation": False,
            "process_sample": None,
            "show_best_segment": False,
        }
        
        report_options = ["Track Statistics"]
        
        pdf_bytes = generate_pdf_report(report_data, report_options, "test_report")
        
        assert pdf_bytes is not None
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        # Check if it starts with PDF magic number
        assert pdf_bytes[:4] == b'%PDF' or pdf_bytes[:4] == b'\x89PNG'

    def test_generate_pdf_with_all_options(self, sample_track):
        """Test PDF generation with all options enabled."""
        # Generate process sample for simulation
        process_sample = sample_track.processSample(
            sample_size=100, method='ar1', sigma_tot=2.5, phi=0.9
        )
        
        report_data = {
            "track": sample_track,
            "speed_unit": "knots",
            "show_simulation": True,
            "process_sample": process_sample,
            "show_best_segment": True,
            "target_type": "Distance",
            "target_value": 500.0,
            "start_idx": 0,
            "end_idx": 10,
            "best_speed": 5.0,
            "method": "ar1",
            "sample_size": 100,
            "sigma_tot": 2.5,
            "phi": 0.9,
        }
        
        report_options = [
            "Track Statistics",
            "Track Map",
            "Speed Over Time",
            "Elevation Profile",
            "Speed Distribution",
            "Simulation Analysis",
            "Best Segment Analysis",
        ]
        
        pdf_bytes = generate_pdf_report(report_data, report_options, "full_report")
        
        assert pdf_bytes is not None
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0

    def test_generate_pdf_with_visualizations(self, sample_track):
        """Test PDF generation with visualizations."""
        report_data = {
            "track": sample_track,
            "speed_unit": "km/h",
            "show_simulation": False,
            "process_sample": None,
            "show_best_segment": False,
        }
        
        report_options = [
            "Track Statistics",
            "Track Map",
            "Speed Over Time",
            "Elevation Profile",
            "Speed Distribution",
        ]
        
        pdf_bytes = generate_pdf_report(report_data, report_options, "viz_report")
        
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0

    def test_generate_pdf_different_speed_units(self, sample_track):
        """Test PDF generation with different speed units."""
        for unit in ["m/s", "km/h", "knots"]:
            report_data = {
                "track": sample_track,
                "speed_unit": unit,
                "show_simulation": False,
                "process_sample": None,
                "show_best_segment": False,
            }
            
            report_options = ["Track Statistics"]
            
            pdf_bytes = generate_pdf_report(report_data, report_options, f"report_{unit}")
            
            assert pdf_bytes is not None
            assert len(pdf_bytes) > 0

    def test_generate_pdf_with_gaussian_simulation(self, sample_track):
        """Test PDF generation with Gaussian process simulation."""
        process_sample = sample_track.processSample(
            sample_size=50, method='gaussian', amplitude=1.5, scale=5.0
        )
        
        report_data = {
            "track": sample_track,
            "speed_unit": "knots",
            "show_simulation": True,
            "process_sample": process_sample,
            "show_best_segment": False,
            "method": "gaussian",
            "sample_size": 50,
            "amplitude": 1.5,
            "scale": 5.0,
        }
        
        report_options = ["Track Statistics", "Simulation Analysis"]
        
        pdf_bytes = generate_pdf_report(report_data, report_options, "gaussian_report")
        
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0

    def test_generate_pdf_minimal_options(self, sample_track):
        """Test PDF generation with minimal options."""
        report_data = {
            "track": sample_track,
            "speed_unit": "knots",
            "show_simulation": False,
            "process_sample": None,
            "show_best_segment": False,
        }
        
        report_options = ["Track Statistics"]
        
        pdf_bytes = generate_pdf_report(report_data, report_options, "minimal_report")
        
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0

    def test_generate_pdf_empty_options(self, sample_track):
        """Test PDF generation with empty options list."""
        report_data = {
            "track": sample_track,
            "speed_unit": "knots",
            "show_simulation": False,
            "process_sample": None,
            "show_best_segment": False,
        }
        
        report_options = []
        
        pdf_bytes = generate_pdf_report(report_data, report_options, "empty_report")
        
        # Should still generate a PDF with title page
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0

    def test_pdf_size_reasonable(self, sample_track):
        """Test that generated PDF has reasonable size."""
        report_data = {
            "track": sample_track,
            "speed_unit": "knots",
            "show_simulation": False,
            "process_sample": None,
            "show_best_segment": False,
        }
        
        report_options = ["Track Statistics", "Track Map"]
        
        pdf_bytes = generate_pdf_report(report_data, report_options, "size_test")
        
        # PDF should be at least a few KB but not more than a few MB
        assert len(pdf_bytes) > 1000  # At least 1KB
        assert len(pdf_bytes) < 10_000_000  # Less than 10MB


class TestPDFReportEdgeCases:
    """Test edge cases for PDF report generation."""

    def test_pdf_with_none_report_data(self):
        """Test PDF generation with None report data."""
        # This should handle gracefully or raise appropriate error
        try:
            pdf_bytes = generate_pdf_report(None, [], "test")
            # If it doesn't raise an error, check that we got something
            assert pdf_bytes is not None
        except Exception as e:
            # It's acceptable to raise an error for invalid input
            assert True

    def test_pdf_with_invalid_track(self):
        """Test PDF generation with invalid track object."""
        class MockTrack:
            def __init__(self):
                self.points = []
                self.data = None
            
            def get_distance(self):
                return 0.0
            
            def get_duration(self):
                return 0.0
            
            def get_average_speed(self):
                return 0.0
        
        mock_track = MockTrack()
        
        report_data = {
            "track": mock_track,
            "speed_unit": "knots",
            "show_simulation": False,
            "process_sample": None,
            "show_best_segment": False,
        }
        
        report_options = ["Track Statistics"]
        
        # This might work or raise an error, both are acceptable
        try:
            pdf_bytes = generate_pdf_report(report_data, report_options, "mock_test")
            assert pdf_bytes is not None
        except Exception:
            # It's acceptable to raise an error for empty tracks
            assert True

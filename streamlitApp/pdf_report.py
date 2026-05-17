"""
PDF report generation for GPX track analysis.

This module provides functions to generate comprehensive PDF reports
with analysis results and visualizations.
"""

import io
import tempfile
import os
from datetime import datetime
from pathlib import Path

# Try to import reportlab, fall back to matplotlib for PDF generation
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, mm
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Image,
        Table,
        TableStyle,
        PageBreak,
    )
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from streamlitApp.visualization import (
    plot_track_with_speed,
    plot_speed_over_time,
    plot_elevation_profile,
    plot_speed_distribution,
)


def generate_pdf_report(report_data, report_options, filename="gpx_report"):
    """
    Generate a PDF report with track analysis and visualizations.
    
    Args:
        report_data: Dictionary containing all report data
        report_options: List of sections to include in the report
        filename: Base filename for the report
        
    Returns:
        bytes: PDF content as bytes
    """
    if REPORTLAB_AVAILABLE:
        return _generate_pdf_with_reportlab(report_data, report_options, filename)
    else:
        return _generate_pdf_with_matplotlib(report_data, report_options, filename)


def _generate_pdf_with_reportlab(report_data, report_options, filename):
    """
    Generate PDF using reportlab (preferred method).
    """
    # Extract data
    track = report_data["track"]
    speed_unit = report_data.get("speed_unit", "knots")
    
    # Create a buffer for the PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, 
                           rightMargin=36, leftMargin=36,
                           topMargin=36, bottomMargin=36)
    
    # Create styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        name="Title",
        parent=styles["Heading1"],
        fontSize=24,
        leading=28,
        alignment=1,  # Center
        spaceAfter=20,
    )
    
    heading1_style = ParagraphStyle(
        name="Heading1",
        parent=styles["Heading1"],
        fontSize=18,
        leading=22,
        spaceBefore=12,
        spaceAfter=6,
    )
    
    heading2_style = ParagraphStyle(
        name="Heading2",
        parent=styles["Heading2"],
        fontSize=14,
        leading=18,
        spaceBefore=12,
        spaceAfter=6,
    )
    
    normal_style = ParagraphStyle(
        name="Normal",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        spaceAfter=6,
    )
    
    # Story for the document
    story = []
    
    # Title
    story.append(Paragraph("GPX Track Analysis Report", title_style))
    story.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 
                          normal_style))
    story.append(Spacer(1, 0.2 * inch))
    
    # Track Information
    if "Track Statistics" in report_options:
        story.append(Paragraph("Track Information", heading1_style))
        story.append(Spacer(1, 0.1 * inch))
        
        # Create track info table
        distance = track.get_distance()
        duration = track.get_duration()
        avg_speed = track.get_average_speed()
        
        # Convert speed to desired unit
        if speed_unit == "km/h":
            avg_speed_display = avg_speed * 3.6
            unit = "km/h"
        elif speed_unit == "knots":
            avg_speed_display = avg_speed * 1.94384
            unit = "knots"
        else:
            avg_speed_display = avg_speed
            unit = "m/s"
        
        # Get time range
        if track.points and track.points[0].time and track.points[-1].time:
            start_time = track.points[0].time.strftime('%Y-%m-%d %H:%M:%S')
            end_time = track.points[-1].time.strftime('%Y-%m-%d %H:%M:%S')
        else:
            start_time = "N/A"
            end_time = "N/A"
        
        track_info_data = [
            ["Property", "Value"],
            ["Distance", f"{distance:.2f} meters"],
            ["Duration", f"{duration:.2f} seconds"],
            ["Average Speed", f"{avg_speed_display:.2f} {unit}"],
            ["Number of Points", str(len(track.points))],
            ["Start Time", start_time],
            ["End Time", end_time],
        ]
        
        track_info_table = Table(track_info_data, colWidths=[2 * inch, 3 * inch])
        track_info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        story.append(track_info_table)
        story.append(Spacer(1, 0.2 * inch))
    
    # Best Segment Analysis
    if "Best Segment Analysis" in report_options and report_data.get("show_best_segment"):
        story.append(Paragraph("Best Segment Analysis", heading1_style))
        story.append(Spacer(1, 0.1 * inch))
        
        target_type = report_data.get("target_type", "Distance")
        target_value = report_data.get("target_value", 500)
        start_idx = report_data.get("start_idx", 0)
        end_idx = report_data.get("end_idx", 0)
        best_speed = report_data.get("best_speed", 0)
        
        # Convert speed to desired unit
        if speed_unit == "km/h":
            best_speed_display = best_speed / 1.94384 * 3.6
            unit = "km/h"
        elif speed_unit == "m/s":
            best_speed_display = best_speed / 1.94384
            unit = "m/s"
        else:
            best_speed_display = best_speed
            unit = "knots"
        
        segment_info_data = [
            ["Property", "Value"],
            ["Target Type", target_type],
            ["Target Value", f"{target_value}"],
            ["Start Index", str(start_idx)],
            ["End Index", str(end_idx)],
            ["Best Speed", f"{best_speed_display:.2f} {unit}"],
        ]
        
        segment_table = Table(segment_info_data, colWidths=[2 * inch, 3 * inch])
        segment_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        story.append(segment_table)
        story.append(Spacer(1, 0.2 * inch))
    
    # Simulation Analysis
    if "Simulation Analysis" in report_options and report_data.get("show_simulation"):
        story.append(Paragraph("Simulation Analysis", heading1_style))
        story.append(Spacer(1, 0.1 * inch))
        
        method = report_data.get("method", "ar1")
        sample_size = report_data.get("sample_size", 500)
        
        sim_info = [
            ["Property", "Value"],
            ["Method", method.upper()],
            ["Number of Simulations", str(sample_size)],
        ]
        
        if method == "ar1":
            sigma_tot = report_data.get("sigma_tot", 2.5)
            phi = report_data.get("phi", 0.9)
            sim_info.append(["Sigma Total", f"{sigma_tot}"])
            sim_info.append(["Phi (AR-1 coefficient)", f"{phi}"])
        else:
            amplitude = report_data.get("amplitude", 1.5)
            scale = report_data.get("scale", 5.0)
            sim_info.append(["Amplitude", f"{amplitude}"])
            sim_info.append(["Scale", f"{scale}"])
        
        sim_table = Table(sim_info, colWidths=[2 * inch, 3 * inch])
        sim_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        story.append(sim_table)
        story.append(Spacer(1, 0.2 * inch))
    
    # Visualizations
    temp_dir = tempfile.mkdtemp()
    image_paths = []
    
    try:
        if "Track Map" in report_options:
            story.append(Paragraph("Track Map", heading1_style))
            fig = plot_track_with_speed(track, speed_unit=speed_unit, dpi=150)
            img_path = os.path.join(temp_dir, "track_map.png")
            fig.savefig(img_path, dpi=150, bbox_inches="tight")
            plt.close(fig)
            
            img = Image(img_path, width=6 * inch, height=4 * inch)
            story.append(img)
            story.append(Spacer(1, 0.2 * inch))
            image_paths.append(img_path)
        
        if "Speed Over Time" in report_options:
            story.append(Paragraph("Speed Over Time", heading1_style))
            fig = plot_speed_over_time(track, speed_unit=speed_unit, dpi=150)
            img_path = os.path.join(temp_dir, "speed_time.png")
            fig.savefig(img_path, dpi=150, bbox_inches="tight")
            plt.close(fig)
            
            img = Image(img_path, width=6 * inch, height=3 * inch)
            story.append(img)
            story.append(Spacer(1, 0.2 * inch))
            image_paths.append(img_path)
        
        if "Elevation Profile" in report_options:
            story.append(Paragraph("Elevation Profile", heading1_style))
            fig = plot_elevation_profile(track, dpi=150)
            img_path = os.path.join(temp_dir, "elevation.png")
            fig.savefig(img_path, dpi=150, bbox_inches="tight")
            plt.close(fig)
            
            img = Image(img_path, width=6 * inch, height=3 * inch)
            story.append(img)
            story.append(Spacer(1, 0.2 * inch))
            image_paths.append(img_path)
        
        if "Speed Distribution" in report_options:
            story.append(Paragraph("Speed Distribution", heading1_style))
            fig = plot_speed_distribution(track, speed_unit=speed_unit, dpi=150)
            img_path = os.path.join(temp_dir, "speed_dist.png")
            fig.savefig(img_path, dpi=150, bbox_inches="tight")
            plt.close(fig)
            
            img = Image(img_path, width=6 * inch, height=3 * inch)
            story.append(img)
            story.append(Spacer(1, 0.2 * inch))
            image_paths.append(img_path)
        
        # Build the PDF
        doc.build(story)
        
        # Get the PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes
        
    finally:
        # Cleanup temporary files
        for img_path in image_paths:
            if os.path.exists(img_path):
                os.remove(img_path)
        if os.path.exists(temp_dir):
            os.rmdir(temp_dir)


def _generate_pdf_with_matplotlib(report_data, report_options, filename):
    """
    Fallback PDF generation using matplotlib's PDF backend.
    This creates a PDF with plots but less formatting options.
    """
    from matplotlib.backends.backend_pdf import PdfPages
    
    track = report_data["track"]
    speed_unit = report_data.get("speed_unit", "knots")
    
    # Create a buffer for the PDF
    buffer = io.BytesIO()
    
    with PdfPages(buffer) as pdf:
        # Add title page
        fig = plt.figure(figsize=(11, 8))
        plt.text(0.5, 0.7, "GPX Track Analysis Report", 
                 ha='center', va='center', fontsize=24, fontweight='bold')
        plt.text(0.5, 0.5, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                 ha='center', va='center', fontsize=14)
        plt.axis('off')
        pdf.savefig(fig)
        plt.close(fig)
        
        # Add track statistics
        if "Track Statistics" in report_options:
            fig = plt.figure(figsize=(11, 8))
            plt.text(0.5, 0.9, "Track Information", 
                     ha='center', va='center', fontsize=18, fontweight='bold')
            
            distance = track.get_distance()
            duration = track.get_duration()
            avg_speed = track.get_average_speed()
            
            if speed_unit == "km/h":
                avg_speed_display = avg_speed * 3.6
                unit = "km/h"
            elif speed_unit == "knots":
                avg_speed_display = avg_speed * 1.94384
                unit = "knots"
            else:
                avg_speed_display = avg_speed
                unit = "m/s"
            
            info_text = (
                f"Distance: {distance:.2f} meters\n"
                f"Duration: {duration:.2f} seconds\n"
                f"Average Speed: {avg_speed_display:.2f} {unit}\n"
                f"Number of Points: {len(track.points)}"
            )
            
            plt.text(0.5, 0.5, info_text, ha='center', va='center', fontsize=12)
            plt.axis('off')
            pdf.savefig(fig)
            plt.close(fig)
        
        # Add visualizations
        if "Track Map" in report_options:
            fig = plot_track_with_speed(track, speed_unit=speed_unit, dpi=150)
            pdf.savefig(fig)
            plt.close(fig)
        
        if "Speed Over Time" in report_options:
            fig = plot_speed_over_time(track, speed_unit=speed_unit, dpi=150)
            pdf.savefig(fig)
            plt.close(fig)
        
        if "Elevation Profile" in report_options:
            fig = plot_elevation_profile(track, dpi=150)
            pdf.savefig(fig)
            plt.close(fig)
        
        if "Speed Distribution" in report_options:
            fig = plot_speed_distribution(track, speed_unit=speed_unit, dpi=150)
            pdf.savefig(fig)
            plt.close(fig)
    
    # Get the PDF bytes
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes

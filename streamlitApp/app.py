"""
Streamlit application for GPX track visualization and analysis.

This app allows users to:
- Upload GPX files
- Visualize tracks with speed coloring
- View track statistics
- Generate and download PDF reports
"""

import os
import sys
import tempfile
import streamlit as st
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from otGpxTrack.Base import GpxTrack
from streamlitApp.pdf_report import generate_pdf_report
from streamlitApp.visualization import (
    plot_track_with_speed,
    plot_speed_over_time,
    plot_elevation_profile,
    plot_speed_distribution,
)


def main():
    """Main function for the Streamlit app."""
    # Page configuration
    st.set_page_config(
        page_title="GPX Track Analyzer",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Custom CSS
    st.markdown("""
        <style>
        .main-header {
            font-size: 2.5rem;
            font-weight: bold;
            color: #1f77b4;
            text-align: center;
            margin-bottom: 2rem;
        }
        .stat-box {
            background-color: #f0f2f6;
            padding: 1rem;
            border-radius: 0.5rem;
            border-left: 4px solid #1f77b4;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 2rem;
        }
        </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown('<p class="main-header">📊 GPX Track Analyzer</p>', unsafe_allow_html=True)
    st.markdown("### Upload and analyze your GPX track files")

    # File uploader
    uploaded_file = st.file_uploader(
        "Choose a GPX file",
        type=["gpx"],
        help="Upload a GPX file to visualize and analyze the track",
    )

    if uploaded_file is None:
        # Show example files if available
        st.info("💡 **Tip:** Upload a GPX file to get started, or use one of the example files below.")
        
        example_files = [
            "activity_19218242997.gpx",
            "activity_22095267736.gpx",
        ]
        
        example_dir = Path(__file__).parent.parent / "firstexample"
        if example_dir.exists():
            st.subheader("Example Files")
            cols = st.columns(len(example_files))
            for i, example_file in enumerate(example_files):
                with cols[i]:
                    if (example_dir / example_file).exists():
                        if st.button(f"Load {example_file}", use_container_width=True):
                            with open(example_dir / example_file, "rb") as f:
                                uploaded_file = f.read()
                                uploaded_file = tempfile.NamedTemporaryFile(
                                    delete=False, suffix=".gpx"
                                )
                                uploaded_file.write(uploaded_file)
                                uploaded_file.seek(0)
    
    if uploaded_file is not None:
        # Process the uploaded file
        try:
            with st.spinner("Processing GPX file..."):
                # Save to temp file
                if hasattr(uploaded_file, "name"):
                    temp_file_path = uploaded_file.name
                else:
                    temp_file = tempfile.NamedTemporaryFile(
                        delete=False, suffix=".gpx"
                    )
                    temp_file.write(uploaded_file.getvalue())
                    temp_file_path = temp_file.name
                    temp_file.close()

                # Load the track
                track = GpxTrack(temp_file_path)

                # Display success message
                st.success(f"✅ Successfully loaded GPX file with {len(track.points)} points")

                # Sidebar for analysis options
                st.sidebar.header("Analysis Options")
                
                # Speed unit selection
                speed_unit = st.sidebar.selectbox(
                    "Speed Unit",
                    ["m/s", "km/h", "knots"],
                    index=2,  # Default to knots
                )

                # Simulation options
                st.sidebar.subheader("Simulation Settings")
                show_simulation = st.sidebar.checkbox("Show Simulation Analysis", value=False)
                
                if show_simulation:
                    method = st.sidebar.selectbox(
                        "Simulation Method",
                        ["ar1", "gaussian"],
                        index=0,
                    )
                    sample_size = st.sidebar.slider(
                        "Number of Simulations",
                        100, 1000, 500, 100,
                    )
                    
                    if method == "ar1":
                        sigma_tot = st.sidebar.slider(
                            "Sigma Total", 0.1, 5.0, 2.5, 0.1
                        )
                        phi = st.sidebar.slider(
                            "Phi (AR-1 coefficient)", 0.0, 0.99, 0.9, 0.01
                        )
                    else:  # gaussian
                        amplitude = st.sidebar.slider(
                            "Amplitude", 0.1, 5.0, 1.5, 0.1
                        )
                        scale = st.sidebar.slider(
                            "Scale", 0.1, 10.0, 5.0, 0.1
                        )

                # Best segment analysis
                st.sidebar.subheader("Best Segment Analysis")
                show_best_segment = st.sidebar.checkbox("Show Best Segment Analysis", value=False)
                
                if show_best_segment:
                    target_type = st.sidebar.radio(
                        "Target Type",
                        ["Distance", "Time"],
                        horizontal=True,
                    )
                    if target_type == "Distance":
                        target_value = st.sidebar.number_input(
                            "Target Distance (meters)",
                            min_value=100.0,
                            max_value=10000.0,
                            value=500.0,
                            step=100.0,
                        )
                    else:
                        target_value = st.sidebar.number_input(
                            "Target Time (seconds)",
                            min_value=1.0,
                            max_value=600.0,
                            value=10.0,
                            step=1.0,
                        )

                # Display basic statistics
                st.subheader("📈 Track Statistics")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    distance = track.get_distance()
                    st.metric("Distance", f"{distance:.2f} m")
                
                with col2:
                    duration = track.get_duration()
                    st.metric("Duration", f"{duration:.2f} s")
                
                with col3:
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
                    st.metric("Avg Speed", f"{avg_speed_display:.2f} {unit}")
                
                with col4:
                    if len(track.points) > 0:
                        start_time = track.points[0].time
                        end_time = track.points[-1].time
                        if start_time and end_time:
                            st.metric("Time Range", f"{start_time.strftime('%Y-%m-%d %H:%M')}")

                # Best segment analysis
                if show_best_segment:
                    st.subheader("🏆 Best Segment Analysis")
                    
                    if target_type == "Distance":
                        start_idx, end_idx, speed = track.get_best_segment_for_distance(target_value)
                        segment_type = "distance"
                    else:
                        start_idx, end_idx, speed = track.get_best_segment_for_time(target_value)
                        segment_type = "time"
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Start Index", start_idx)
                    with col2:
                        st.metric("End Index", end_idx)
                    with col3:
                        if speed_unit == "km/h":
                            speed_display = speed / 1.94384 * 3.6  # Convert from knots to km/h
                            unit = "km/h"
                        elif speed_unit == "m/s":
                            speed_display = speed / 1.94384  # Convert from knots to m/s
                            unit = "m/s"
                        else:
                            speed_display = speed
                            unit = "knots"
                        st.metric("Best Speed", f"{speed_display:.2f} {unit}")

                # Simulation analysis
                if show_simulation:
                    st.subheader("🎲 Simulation Analysis")
                    
                    with st.spinner("Running simulations..."):
                        if method == "ar1":
                            process_sample = track.processSample(
                                sample_size=sample_size,
                                method=method,
                                sigma_tot=sigma_tot,
                                phi=phi,
                            )
                        else:
                            process_sample = track.processSample(
                                sample_size=sample_size,
                                method=method,
                                amplitude=amplitude,
                                scale=scale,
                            )
                    
                    # Calculate quantiles
                    quantiles = process_sample.computeQuantilePerComponent([0.025, 0.5, 0.975])
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        lower = quantiles[0][0][0]
                        if speed_unit == "km/h":
                            lower_display = lower * 3.6
                            unit = "km/h"
                        elif speed_unit == "m/s":
                            lower_display = lower
                            unit = "m/s"
                        else:
                            lower_display = lower * 1.94384
                            unit = "knots"
                        st.metric("2.5% Quantile", f"{lower_display:.2f} {unit}")
                    
                    with col2:
                        median = quantiles[1][0][0]
                        if speed_unit == "km/h":
                            median_display = median * 3.6
                        elif speed_unit == "m/s":
                            median_display = median
                        else:
                            median_display = median * 1.94384
                        st.metric("Median", f"{median_display:.2f} {unit}")
                    
                    with col3:
                        upper = quantiles[2][0][0]
                        if speed_unit == "km/h":
                            upper_display = upper * 3.6
                        elif speed_unit == "m/s":
                            upper_display = upper
                        else:
                            upper_display = upper * 1.94384
                        st.metric("97.5% Quantile", f"{upper_display:.2f} {unit}")

                # Tabs for different visualizations
                st.subheader("📊 Visualizations")
                
                tab1, tab2, tab3, tab4 = st.tabs([
                    "Track Map", 
                    "Speed Over Time", 
                    "Elevation Profile",
                    "Speed Distribution"
                ])
                
                with tab1:
                    st.write("### Track Map with Speed Coloring")
                    fig = plot_track_with_speed(track, speed_unit=speed_unit)
                    st.pyplot(fig)
                    
                    # Download plot
                    if st.button("📥 Download Track Plot", key="download_track_plot"):
                        fig.savefig("track_plot.png", dpi=300, bbox_inches="tight")
                        with open("track_plot.png", "rb") as f:
                            st.download_button(
                                label="Download Track Plot",
                                data=f,
                                file_name="track_plot.png",
                                mime="image/png",
                            )
                
                with tab2:
                    st.write("### Speed Over Time")
                    fig = plot_speed_over_time(track, speed_unit=speed_unit)
                    st.pyplot(fig)
                    
                    if show_simulation:
                        st.write("### Speed Over Time with Confidence Intervals")
                        fig_ci = plot_speed_over_time(
                            track, 
                            speed_unit=speed_unit,
                            process_sample=process_sample
                        )
                        st.pyplot(fig_ci)
                
                with tab3:
                    st.write("### Elevation Profile")
                    fig = plot_elevation_profile(track)
                    st.pyplot(fig)
                
                with tab4:
                    st.write("### Speed Distribution")
                    fig = plot_speed_distribution(track, speed_unit=speed_unit)
                    st.pyplot(fig)

                # PDF Report Generation
                st.subheader("📄 Generate PDF Report")
                
                st.write("Generate a comprehensive PDF report with all analysis and visualizations.")
                
                report_options = st.multiselect(
                    "Include in Report",
                    [
                        "Track Statistics",
                        "Track Map",
                        "Speed Over Time",
                        "Elevation Profile",
                        "Speed Distribution",
                        "Simulation Analysis" if show_simulation else None,
                        "Best Segment Analysis" if show_best_segment else None,
                    ],
                    default=[
                        "Track Statistics",
                        "Track Map",
                        "Speed Over Time",
                        "Elevation Profile",
                        "Speed Distribution",
                    ],
                )
                
                # Filter out None values
                report_options = [opt for opt in report_options if opt is not None]
                
                if st.button("📥 Generate PDF Report", type="primary", use_container_width=True):
                    with st.spinner("Generating PDF report..."):
                        # Create report data
                        report_data = {
                            "track": track,
                            "speed_unit": speed_unit,
                            "show_simulation": show_simulation,
                            "process_sample": process_sample if show_simulation else None,
                            "show_best_segment": show_best_segment,
                            "target_type": target_type if show_best_segment else None,
                            "target_value": target_value if show_best_segment else None,
                            "start_idx": start_idx if show_best_segment else None,
                            "end_idx": end_idx if show_best_segment else None,
                            "best_speed": speed if show_best_segment else None,
                            "method": method if show_simulation else None,
                            "sample_size": sample_size if show_simulation else None,
                            "sigma_tot": sigma_tot if show_simulation and method == "ar1" else None,
                            "phi": phi if show_simulation and method == "ar1" else None,
                            "amplitude": amplitude if show_simulation and method == "gaussian" else None,
                            "scale": scale if show_simulation and method == "gaussian" else None,
                        }
                        
                        # Generate PDF
                        pdf_bytes = generate_pdf_report(
                            report_data, 
                            report_options,
                            uploaded_file.name if hasattr(uploaded_file, "name") else "track"
                        )
                        
                        # Download button
                        st.success("✅ PDF report generated successfully!")
                        st.download_button(
                            label="Download PDF Report",
                            data=pdf_bytes,
                            file_name=f"gpx_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                            mime="application/pdf",
                            use_container_width=True,
                        )

                # Cleanup temp file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)

        except Exception as e:
            st.error(f"❌ Error processing GPX file: {str(e)}")
            st.error(f"Error type: {type(e).__name__}")
            import traceback
            with st.expander("Show full error traceback"):
                st.code(traceback.format_exc())

    else:
        # Show welcome message
        st.info("👆 Please upload a GPX file to begin analysis")
        
        # Show example usage
        with st.expander("❓ How to use this app"):
            st.markdown("""
            ### How to Use GPX Track Analyzer
            
            1. **Upload a GPX file** using the file uploader above
            2. **View track statistics** including distance, duration, and average speed
            3. **Explore visualizations** in the tabs:
               - Track Map: See your route with speed coloring
               - Speed Over Time: Analyze speed variations
               - Elevation Profile: View elevation changes
               - Speed Distribution: See speed histogram
            
            4. **Optional Analysis**:
               - Enable simulation analysis in the sidebar to run stochastic simulations
               - Enable best segment analysis to find optimal segments
            
            5. **Generate PDF Report**: Create a comprehensive report with all your analysis
            
            ### Features
            - ✅ Visualize GPX tracks with speed coloring
            - ✅ Calculate track statistics (distance, duration, speed)
            - ✅ Run AR-1 and Gaussian process simulations
            - ✅ Find best segments for distance or time targets
            - ✅ Generate downloadable PDF reports
            - ✅ Support for multiple speed units (m/s, km/h, knots)
            """)


if __name__ == "__main__":
    main()

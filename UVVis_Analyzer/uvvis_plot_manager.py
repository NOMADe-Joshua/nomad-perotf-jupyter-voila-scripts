"""
UVVis Plot Management Module
Handles all plotting operations for UVVis spectra.
"""

__author__ = "Adapted from JV Analysis"
__institution__ = "Helmholtz-Zentrum Berlin / KIT"
__created__ = "January 2025"

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np


class UVVisPlotManager:
    """Manages UVVis spectroscopy plotting"""
    
    def __init__(self):
        self.plot_output_path = ""
    
    def set_output_path(self, path):
        self.plot_output_path = path
    
    def create_spectra_plot(self, measurements, color_scheme=None, plot_mode='overlay'):
        """
        Create UV-Vis spectra plot
        
        Args:
            measurements: List of measurement dictionaries
            color_scheme: List of colors
            plot_mode: 'overlay', 'separate', or 'grid'
        """
        if not measurements:
            fig = go.Figure()
            fig.update_layout(title="No data available")
            return fig, "uvvis_spectra.html"
        
        if color_scheme is None:
            color_scheme = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
        
        if plot_mode == 'overlay':
            return self._create_overlay_plot(measurements, color_scheme)
        elif plot_mode == 'grid':
            return self._create_grid_plot(measurements, color_scheme)
        else:
            return self._create_separate_plots(measurements, color_scheme)
    
    def _create_overlay_plot(self, measurements, color_scheme):
        """Create single plot with all spectra overlaid"""
        fig = go.Figure()
        
        for i, measurement in enumerate(measurements):
            wavelength = measurement['wavelength']
            intensity = measurement['intensity']
            name = f"{measurement['sample_name']} - {measurement['measurement_name']}"
            color = color_scheme[i % len(color_scheme)]
            
            fig.add_trace(go.Scatter(
                x=wavelength,
                y=intensity,
                mode='lines',
                name=name,
                line=dict(color=color, width=2),
                hovertemplate='λ: %{x:.1f} nm<br>Intensity: %{y:.4f}<extra></extra>'
            ))
        
        fig.update_layout(
            title='UV-Vis Absorption Spectra',
            xaxis_title='Wavelength [nm]',
            yaxis_title='Intensity / Absorbance',
            template="plotly_white",
            legend=dict(
                x=0.02,
                y=0.98,
                xanchor="left",
                yanchor="top",
                bgcolor="rgba(255,255,255,0.85)",
                bordercolor="black",
                borderwidth=1
            ),
            width=1600,
            height=1000,
            hovermode='closest'
        )
        
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
        
        return fig, "uvvis_overlay_spectra.html"
    
    def _create_grid_plot(self, measurements, color_scheme):
        """Create grid of subplots"""
        num_measurements = len(measurements)
        cols = 2
        rows = (num_measurements + cols - 1) // cols
        
        fig = make_subplots(
            rows=rows, cols=cols,
            subplot_titles=[f"{m['sample_name']}<br>{m['measurement_name']}" for m in measurements],
            vertical_spacing=0.12,
            horizontal_spacing=0.10
        )
        
        for i, measurement in enumerate(measurements):
            row = (i // cols) + 1
            col = (i % cols) + 1
            
            wavelength = measurement['wavelength']
            intensity = measurement['intensity']
            color = color_scheme[i % len(color_scheme)]
            
            fig.add_trace(go.Scatter(
                x=wavelength,
                y=intensity,
                mode='lines',
                name=measurement['sample_name'],
                line=dict(color=color, width=2),
                showlegend=False,
                hovertemplate='λ: %{x:.1f} nm<br>Intensity: %{y:.4f}<extra></extra>'
            ), row=row, col=col)
        
        fig.update_xaxes(title_text="Wavelength [nm]", showgrid=True)
        fig.update_yaxes(title_text="Intensity", showgrid=True)
        
        fig.update_layout(
            title='UV-Vis Spectra Grid',
            template="plotly_white",
            width=1600,
            height=600 * rows,
            hovermode='closest'
        )
        
        return fig, "uvvis_grid_spectra.html"
    
    def _create_separate_plots(self, measurements, color_scheme):
        """Create separate plot for each measurement"""
        figs = []
        names = []
        
        for i, measurement in enumerate(measurements):
            fig = go.Figure()
            
            wavelength = measurement['wavelength']
            intensity = measurement['intensity']
            color = color_scheme[i % len(color_scheme)]
            
            fig.add_trace(go.Scatter(
                x=wavelength,
                y=intensity,
                mode='lines',
                line=dict(color=color, width=2),
                hovertemplate='λ: %{x:.1f} nm<br>Intensity: %{y:.4f}<extra></extra>'
            ))
            
            fig.update_layout(
                title=f"{measurement['sample_name']} - {measurement['measurement_name']}",
                xaxis_title='Wavelength [nm]',
                yaxis_title='Intensity',
                template="plotly_white",
                width=1200,
                height=700,
                showlegend=False
            )
            
            fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
            fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
            
            figs.append(fig)
            names.append(f"uvvis_{measurement['sample_name']}_{measurement['measurement_name']}.html")
        
        return figs, names

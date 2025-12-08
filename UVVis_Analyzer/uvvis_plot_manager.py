"""
UVVis Plot Management Module
Handles all plotting operations for UVVis spectra.
"""

__author__ = "Joshua Damm"
__institution__ = "KIT"
__created__ = "December 2025"

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from scipy.interpolate import CubicSpline
from scipy.signal import argrelextrema, savgol_filter
from scipy.optimize import curve_fit
from scipy.stats import linregress


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
    
    @staticmethod
    def _gaussian(x, amp, cen, wid):
        """Gaussian function for peak fitting"""
        return amp * np.exp(-((x - cen) ** 2) / (2 * wid**2))
    
    @staticmethod
    def _find_peaks_and_fit_gaussian(x, y):
        """Find peaks in derivative and fit Gaussian"""
        peaks = argrelextrema(y, np.greater)[0]
        if peaks.size == 0:
            return []
        
        results = []
        y_masked = np.copy(y)
        
        while True:
            peaks = argrelextrema(y_masked, np.greater)[0]
            if peaks.size == 0:
                break
            
            peak = peaks[np.argmax(y_masked[peaks])]
            peak_energy = x[peak]
            
            if len(results) > 0 and y_masked[peak] < results[0][1][0] / 4:
                break
            
            fitting_range = (x > peak_energy - 0.1) & (x < peak_energy + 0.1)
            width = 0.05
            
            try:
                popt, _ = curve_fit(
                    UVVisPlotManager._gaussian,
                    x[fitting_range],
                    y[fitting_range],
                    p0=[y[peak], peak_energy, width],
                )
                results.append((popt[1], popt, fitting_range))
            except RuntimeError:
                break
            
            y_masked[fitting_range] = 0
        
        return results
    
    @staticmethod
    def _find_best_tauc_fit(x, y, min_range=0.15, max_range=0.35):
        """Find best linear fit in Tauc plot"""
        best_fit = None
        best_r2 = -np.inf

        for start in range(len(x)):
            for end in range(start + 5, len(x)):
                x_fit = x[start:end]
                y_fit = y[start:end]

                if len(x_fit) < 10:
                    continue

                energy_range = x_fit[-1] - x_fit[0]
                if energy_range < min_range or energy_range > max_range:
                    continue

                slope, intercept, r_value, *_ = linregress(x_fit, y_fit)
                r_squared = r_value**2
                
                if slope < 0 or r_squared < 0.98:
                    continue

                x0 = -intercept / slope
                if 0.5 < x0 < 3.5:
                    if r_squared > best_r2:
                        best_r2 = r_squared
                        best_fit = {
                            "x_fit": x_fit,
                            "y_fit": y_fit,
                            "slope": slope,
                            "intercept": intercept,
                            "bandgap": x0,
                            "r2": r_squared
                        }

        return best_fit
    
    def create_bandgap_derivative_plot(self, measurements, colors=None, x_axis='energy'):
        """
        Create bandgap determination plot using derivative method
        
        Args:
            measurements: List of measurement dictionaries
            colors: Color scheme
            x_axis: 'energy' or 'wavelength'
        """
        if not measurements:
            fig = go.Figure()
            fig.update_layout(title="No data available")
            return fig, "uvvis_bandgap_derivative.html"
        
        if colors is None:
            colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
        
        # Create subplots: [Absorption, Derivative]
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('Absorption Spectrum', 'Derivative (Bandgap Detection)'),
            horizontal_spacing=0.12
        )
        
        for i, measurement in enumerate(measurements):
            try:
                wavelength = measurement['wavelength']
                intensity = measurement['intensity']
                name = f"{measurement['sample_name']}"
                color = colors[i % len(colors)]
                
                # Convert to photon energy
                photon_energy = 1239.841984 / wavelength
                
                # Sort by energy
                sorted_indices = np.argsort(photon_energy)
                energy_sorted = photon_energy[sorted_indices]
                absorption_sorted = intensity[sorted_indices]
                
                # Interpolate and smooth
                energy_range = np.linspace(energy_sorted.min(), energy_sorted.max(), 1001)
                spline = CubicSpline(energy_sorted, absorption_sorted)
                interpolated_absorption = spline(energy_range)
                smoothed_absorption = savgol_filter(interpolated_absorption, window_length=101, polyorder=3)
                derivative = np.gradient(smoothed_absorption, energy_range)
                
                # Find bandgap peaks
                peaks_result = self._find_peaks_and_fit_gaussian(energy_range, derivative)
                
                bandgap_list = [f"{bg_energy:.2f} eV" for bg_energy, _, _ in peaks_result]
                bandgap_label = "Bandgap: " + (", ".join(bandgap_list) if bandgap_list else "Not detected")
                
                if x_axis == 'wavelength':
                    # Convert back to wavelength
                    wavelength_range = 1239.841984 / energy_range[::-1]
                    smoothed_absorption = smoothed_absorption[::-1]
                    derivative = derivative[::-1]
                    
                    x_data = wavelength
                    x_smooth = wavelength_range
                    x_label = 'Wavelength [nm]'
                    
                    # Add absorption trace
                    fig.add_trace(go.Scatter(
                        x=x_data, y=intensity,
                        mode='markers',
                        name=name,
                        marker=dict(color=color, size=4, opacity=0.5),
                        showlegend=True,
                        legendgroup=f'group{i}'
                    ), row=1, col=1)
                    
                    fig.add_trace(go.Scatter(
                        x=x_smooth, y=smoothed_absorption,
                        mode='lines',
                        line=dict(color=color, width=2),
                        showlegend=False,
                        legendgroup=f'group{i}'
                    ), row=1, col=1)
                    
                    # Add derivative trace
                    fig.add_trace(go.Scatter(
                        x=x_smooth, y=derivative,
                        mode='lines',
                        name=f"{name}<br>{bandgap_label}",
                        line=dict(color=color, width=2),
                        showlegend=True,
                        legendgroup=f'group{i}'
                    ), row=1, col=2)
                    
                    # Add bandgap markers
                    for bandgap_energy, popt, fitting_range in peaks_result:
                        lambda_bg = 1239.841984 / bandgap_energy
                        lambda_fit = 1239.841984 / energy_range[fitting_range][::-1]
                        
                        fig.add_trace(go.Scatter(
                            x=lambda_fit,
                            y=self._gaussian(energy_range[fitting_range], *popt)[::-1],
                            mode='lines',
                            line=dict(color=color, dash='dot'),
                            showlegend=False,
                            legendgroup=f'group{i}'
                        ), row=1, col=2)
                        
                        fig.add_vline(x=lambda_bg, line_dash="dash", line_color=color, row=1, col=2,
                                     annotation_text=f"{bandgap_energy:.2f} eV")
                    
                    # Invert x-axis for wavelength
                    fig.update_xaxes(autorange="reversed", row=1, col=1)
                    fig.update_xaxes(autorange="reversed", row=1, col=2)
                    
                else:  # x_axis == 'energy'
                    x_data = energy_sorted
                    x_smooth = energy_range
                    x_label = 'Photon Energy [eV]'
                    
                    # Add absorption trace
                    fig.add_trace(go.Scatter(
                        x=x_data, y=absorption_sorted,
                        mode='markers',
                        name=name,
                        marker=dict(color=color, size=4, opacity=0.5),
                        showlegend=True,
                        legendgroup=f'group{i}'
                    ), row=1, col=1)
                    
                    fig.add_trace(go.Scatter(
                        x=x_smooth, y=smoothed_absorption,
                        mode='lines',
                        line=dict(color=color, width=2),
                        showlegend=False,
                        legendgroup=f'group{i}'
                    ), row=1, col=1)
                    
                    # Add derivative trace
                    fig.add_trace(go.Scatter(
                        x=x_smooth, y=derivative,
                        mode='lines',
                        name=f"{name}<br>{bandgap_label}",
                        line=dict(color=color, width=2),
                        showlegend=True,
                        legendgroup=f'group{i}'
                    ), row=1, col=2)
                    
                    # Add bandgap markers
                    for bandgap_energy, popt, fitting_range in peaks_result:
                        fig.add_trace(go.Scatter(
                            x=energy_range[fitting_range],
                            y=self._gaussian(energy_range[fitting_range], *popt),
                            mode='lines',
                            line=dict(color=color, dash='dot'),
                            showlegend=False,
                            legendgroup=f'group{i}'
                        ), row=1, col=2)
                        
                        fig.add_vline(x=bandgap_energy, line_dash="dash", line_color=color, row=1, col=2,
                                     annotation_text=f"{bandgap_energy:.2f} eV")
            
            except Exception as e:
                print(f"Error processing {measurement['sample_name']}: {e}")
                continue
        
        # Update layout
        fig.update_xaxes(title_text=x_label, showgrid=True, row=1, col=1)
        fig.update_xaxes(title_text=x_label, showgrid=True, row=1, col=2)
        fig.update_yaxes(title_text='Absorption [%]', showgrid=True, row=1, col=1)
        fig.update_yaxes(title_text='d(Absorption)/dE', showgrid=True, row=1, col=2)
        
        fig.update_layout(
            title='UVVis Bandgap Determination (Derivative Method)',
            template="plotly_white",
            width=1600,
            height=700,
            hovermode='closest'
        )
        
        filename = f"uvvis_bandgap_derivative_{x_axis}.html"
        return fig, filename
    
    def create_tauc_plot(self, measurements, colors=None, thickness_nm=550):
        """
        Create Tauc plot for direct bandgap determination
        
        Args:
            measurements: List of measurement dictionaries (must include reflection/transmission)
            colors: Color scheme
            thickness_nm: Film thickness in nanometers
        """
        if not measurements:
            fig = go.Figure()
            fig.update_layout(title="No data available")
            return fig, "uvvis_tauc_plot.html"
        
        if colors is None:
            colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
        
        fig = go.Figure()
        
        for i, measurement in enumerate(measurements):
            try:
                wavelength = measurement['wavelength']
                
                # Check if reflection/transmission data available
                if 'reflection' not in measurement or 'transmission' not in measurement:
                    print(f"Warning: No reflection/transmission data for {measurement['sample_name']}, skipping Tauc plot")
                    continue
                
                reflection = measurement['reflection']
                transmission = measurement['transmission']
                
                # Calculate absorption coefficient
                # alpha = 1/d * ln((1-R)^2 / T)
                alpha = (1 / thickness_nm) * np.log((1 - reflection)**2 / transmission)
                
                # Convert to photon energy
                photon_energy = 1239.841984 / wavelength
                
                # Calculate Tauc variable: (alpha * hv)^2
                tauc = (alpha * photon_energy) ** 2
                
                # Sort by energy
                sorted_indices = np.argsort(photon_energy)
                energy_sorted = photon_energy[sorted_indices]
                tauc_sorted = tauc[sorted_indices]
                
                # Smooth data
                tauc_smooth = savgol_filter(tauc_sorted, 51, 3)
                
                # Find best fit
                fit_result = self._find_best_tauc_fit(energy_sorted, tauc_smooth)
                
                color = colors[i % len(colors)]
                name = measurement['sample_name']
                
                if fit_result is None:
                    label = f"{name} (no fit)"
                    
                    fig.add_trace(go.Scatter(
                        x=energy_sorted,
                        y=tauc_sorted,
                        mode='lines',
                        name=label,
                        line=dict(color=color, width=2, dash='dot'),
                        opacity=0.5
                    ))
                else:
                    bandgap = fit_result['bandgap']
                    r2 = fit_result['r2']
                    label = f"{name} (Eg = {bandgap:.2f} eV, R² = {r2:.3f})"
                    
                    # Plot data
                    fig.add_trace(go.Scatter(
                        x=energy_sorted,
                        y=tauc_sorted,
                        mode='lines',
                        name=label,
                        line=dict(color=color, width=2),
                        opacity=0.7
                    ))
                    
                    # Plot fit line
                    x_fit = fit_result['x_fit']
                    slope = fit_result['slope']
                    intercept = fit_result['intercept']
                    
                    max_index = np.where(energy_sorted >= x_fit[-1])[0][0]
                    x_line = np.linspace(bandgap, energy_sorted[max_index], 100)
                    y_line = slope * x_line + intercept
                    
                    fig.add_trace(go.Scatter(
                        x=x_line,
                        y=y_line,
                        mode='lines',
                        line=dict(color=color, dash='dash', width=2),
                        showlegend=False
                    ))
                    
                    # Mark bandgap
                    fig.add_trace(go.Scatter(
                        x=[bandgap],
                        y=[0],
                        mode='markers',
                        marker=dict(color=color, size=10, symbol='circle'),
                        showlegend=False,
                        hovertemplate=f'Bandgap: {bandgap:.2f} eV<extra></extra>'
                    ))
            
            except Exception as e:
                print(f"Error processing Tauc plot for {measurement['sample_name']}: {e}")
                continue
        
        fig.update_layout(
            title=f'Tauc Plot (Direct Bandgap, thickness={thickness_nm} nm)',
            xaxis_title='Photon Energy [eV]',
            yaxis_title='(αhν)² [a.u.]',
            template="plotly_white",
            width=1200,
            height=800,
            hovermode='closest'
        )
        
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
        
        return fig, "uvvis_tauc_plot.html"

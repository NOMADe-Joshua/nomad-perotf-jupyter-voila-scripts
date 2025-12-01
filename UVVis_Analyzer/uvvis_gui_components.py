"""
UVVis GUI Components Module
Contains UI components for the UVVis Analysis Dashboard.
"""

__author__ = "Adapted from JV Analysis"
__institution__ = "Helmholtz-Zentrum Berlin / KIT"
__created__ = "January 2025"

import ipywidgets as widgets
from IPython.display import display, clear_output, HTML
import sys
import os

# Add parent directory
parent_dir = os.path.dirname(os.path.dirname(os.getcwd()))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# CRITICAL FIX: Add JV-Analysis directory to path
jv_dir = os.path.join(parent_dir, 'JV-Analysis_v6')
if jv_dir not in sys.path:
    sys.path.append(jv_dir)

# Reuse authentication UI from JV analysis
from gui_components import AuthenticationUI, SaveUI


class UVVisAuthenticationUI(AuthenticationUI):
    """Reuse JV authentication UI"""
    pass


class UVVisBatchSelector:
    """Batch selection UI for UVVis"""
    
    def __init__(self, callback):
        self.callback = callback
        self._create_widgets()
    
    def _create_widgets(self):
        self.batch_selector = widgets.SelectMultiple(
            options=[],
            description='Batches:',
            style={'description_width': 'initial'},
            layout=widgets.Layout(width='400px', height='200px')
        )
        
        self.load_button = widgets.Button(
            description='Load Data',
            button_style='success',
            layout=widgets.Layout(width='150px')
        )
        
        self.load_button.on_click(lambda b: self.callback(self.batch_selector))
        
        self.widget = widgets.VBox([
            widgets.HTML("<h3>Select Batches</h3>"),
            self.batch_selector,
            self.load_button
        ])
    
    def set_options(self, options):
        self.batch_selector.options = options
    
    def get_widget(self):
        return self.widget


class UVVisPlotUI:
    """Plot selection UI for UVVis"""
    
    def __init__(self):
        self._create_widgets()
    
    def _create_widgets(self):
        """Create widgets"""
        self.plot_mode_radio = widgets.RadioButtons(
            options=[
                'Overlay (all in one)', 
                'Grid (2x2 layout)', 
                'Separate (one per sample)',
                '🔬 Bandgap Analysis (Derivative)',  # NEW
                '📊 Tauc Plot (Direct Bandgap)'      # NEW
            ],
            value='Overlay (all in one)',
            description='Plot Mode:',
            style={'description_width': 'initial'}
        )
        
        # NEW: X-axis selection for bandgap analysis
        self.x_axis_radio = widgets.RadioButtons(
            options=['Photon Energy (eV)', 'Wavelength (nm)'],
            value='Photon Energy (eV)',
            description='X-Axis:',
            style={'description_width': 'initial'},
            layout=widgets.Layout(display='none')  # Hidden by default
        )
        
        # NEW: Thickness input for Tauc plot
        self.thickness_input = widgets.FloatText(
            value=550,
            description='Thickness (nm):',
            style={'description_width': 'initial'},
            layout=widgets.Layout(display='none', width='200px')  # Hidden by default
        )
        
        self.plot_button = widgets.Button(
            description='Create Plots',
            button_style='success',
            layout=widgets.Layout(width='150px')
        )
        
        self.plotted_content = widgets.Output()
        
        # Setup observer for plot mode changes
        self.plot_mode_radio.observe(self._on_plot_mode_change, names='value')
        
        self.widget = widgets.VBox([
            widgets.HTML("<h3>Plot Settings</h3>"),
            self.plot_mode_radio,
            self.x_axis_radio,       # NEW
            self.thickness_input,     # NEW
            self.plot_button,
            widgets.HTML("<hr>"),
            widgets.HTML("<h3>Generated Plots</h3>"),
            self.plotted_content
        ])
    
    def _on_plot_mode_change(self, change):
        """Show/hide additional options based on plot mode"""
        mode = change['new']
        
        if 'Bandgap Analysis' in mode:
            self.x_axis_radio.layout.display = 'flex'
            self.thickness_input.layout.display = 'none'
        elif 'Tauc Plot' in mode:
            self.x_axis_radio.layout.display = 'none'
            self.thickness_input.layout.display = 'flex'
        else:
            self.x_axis_radio.layout.display = 'none'
            self.thickness_input.layout.display = 'none'
    
    def get_plot_mode(self):
        """Get plot mode"""
        mode_map = {
            'Overlay (all in one)': 'overlay',
            'Grid (2x2 layout)': 'grid',
            'Separate (one per sample)': 'separate',
            '🔬 Bandgap Analysis (Derivative)': 'bandgap_derivative',
            '📊 Tauc Plot (Direct Bandgap)': 'tauc_plot'
        }
        return mode_map.get(self.plot_mode_radio.value, 'overlay')
    
    def get_x_axis_mode(self):
        """Get x-axis mode for bandgap analysis"""
        if 'Energy' in self.x_axis_radio.value:
            return 'energy'
        else:
            return 'wavelength'
    
    def get_thickness(self):
        """Get thickness for Tauc plot"""
        return self.thickness_input.value
    
    def set_plot_callback(self, callback):
        self.plot_button.on_click(callback)
    
    def get_widget(self):
        return self.widget


class UVVisSaveUI(SaveUI):
    """Reuse JV save UI"""
    pass

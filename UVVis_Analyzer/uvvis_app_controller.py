"""
UVVis Application Controller
Main orchestrator for the UVVis Analysis Dashboard.
"""

__author__ = "Joshua Damm"
__institution__ = "KIT"
__created__ = "December 2025"

import ipywidgets as widgets
from IPython.display import display, clear_output, Markdown
import os
import sys

# Add parent directory
parent_dir = os.path.dirname(os.path.dirname(os.getcwd()))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# CRITICAL FIX: Add JV-Analysis directory to path for shared components
jv_dir = os.path.join(parent_dir, 'JV-Analysis_v6')
if jv_dir not in sys.path:
    sys.path.append(jv_dir)

# Now imports should work
from uvvis_data_manager import UVVisDataManager
from uvvis_plot_manager import UVVisPlotManager
from uvvis_gui_components import UVVisAuthenticationUI, UVVisBatchSelector, UVVisPlotUI, UVVisSaveUI
from gui_components import ColorSchemeSelector  # From JV-Analysis
from resizable_plot_utility import ResizablePlotManager  # From JV-Analysis

# Import batch sorting utilities
try:
    from batch_selection import sort_by_date_desc
except ImportError:
    # Fallback if batch_selection.py not available
    import re
    def extract_date(s):
        match = re.search(r'20\d{6}', s)
        return int(match.group()) if match else None
    
    def sort_by_date_desc(data_list):
        return sorted(
            data_list,
            key=lambda x: extract_date(x) if extract_date(x) else 0,
            reverse=True
        )


class SimpleAuthManager:
    """Simplified authentication manager"""
    
    def __init__(self, base_url, api_endpoint):
        self.base_url = base_url
        self.api_endpoint = api_endpoint
        self.url = f"{base_url}{api_endpoint}"
        self.current_token = None
        self.current_user_info = None
        self.status_callback = None
    
    def set_status_callback(self, callback):
        self.status_callback = callback
    
    def _update_status(self, message, color=None):
        """Update status through callback if available"""
        if self.status_callback:
            self.status_callback(message, color)
    
    def authenticate_with_credentials(self, username, password):
        import requests
        if not username or not password:
            raise ValueError("Username and Password required")
        
        auth_dict = dict(username=username, password=password)
        token_url = f"{self.url}/auth/token"
        
        try:
            response = requests.get(token_url, params=auth_dict, timeout=10)
            response.raise_for_status()
            
            token_data = response.json()
            self.current_token = token_data['access_token']
            return self.current_token
        except requests.exceptions.RequestException as e:
            self._handle_request_error(e)
            raise
    
    def authenticate_with_token(self, token=None):
        if token is None:
            token = os.environ.get('NOMAD_CLIENT_ACCESS_TOKEN')
            if not token:
                raise ValueError("Token not found in environment variable 'NOMAD_CLIENT_ACCESS_TOKEN'.")
        self.current_token = token
        return self.current_token
    
    def verify_token(self):
        import requests
        if not self.current_token:
            raise ValueError("No token available for verification.")
            
        verify_url = f"{self.url}/users/me"
        headers = {'Authorization': f'Bearer {self.current_token}'}
        
        try:
            verify_response = requests.get(verify_url, headers=headers, timeout=10)
            verify_response.raise_for_status()
            self.current_user_info = verify_response.json()
            return self.current_user_info
        except requests.exceptions.RequestException as e:
            self._handle_request_error(e)
            raise
    
    def _handle_request_error(self, e):
        """Handle and format request errors consistently"""
        import json
        if e.response is not None:
            try:
                error_detail = e.response.json().get('detail', e.response.text)
                if isinstance(error_detail, list):
                    error_message = f"API Error ({e.response.status_code}): {json.dumps(error_detail)}"
                else:
                    error_message = f"API Error ({e.response.status_code}): {error_detail or e.response.text}"
            except json.JSONDecodeError:
                error_message = f"API Error ({e.response.status_code}): {e.response.text}"
        else:
            error_message = f"Network/API Error: {e}"
        
        self._update_status(f'Status: {error_message}', 'red')
    
    def is_authenticated(self):
        return self.current_token is not None
    
    def clear_authentication(self):
        self.current_token = None
        self.current_user_info = None


class UVVisAnalysisApp:
    """Main UVVis analysis application"""
    
    def __init__(self):
        self.auth_manager = SimpleAuthManager("http://elnserver.lti.kit.edu", "/nomad-oasis/api/v1")
        self.data_manager = UVVisDataManager(self.auth_manager)
        self.plot_manager = UVVisPlotManager()
        
        self.global_plot_data = {'figs': [], 'names': []}
        
        self._init_ui_components()
        self._create_tabs()
        self._setup_callbacks()
        self._auto_authenticate()
    
    def _init_ui_components(self):
        self.auth_ui = UVVisAuthenticationUI(self.auth_manager)
        self.batch_selector = UVVisBatchSelector(self._load_data_from_selection)
        self.plot_ui = UVVisPlotUI()
        self.save_ui = UVVisSaveUI()
        self.color_selector = ColorSchemeSelector()
        
        self.load_status_output = widgets.Output(
            layout=widgets.Layout(border='1px solid #eee', padding='10px', margin='10px 0')
        )
    
    def _create_tabs(self):
        self.select_batch_tab = widgets.VBox([
            widgets.HTML("<h3>Select Batches</h3>"),
            self.batch_selector.get_widget(),
            self.load_status_output
        ])
        
        plot_tab_content = widgets.VBox([
            self.plot_ui.get_widget(),
            widgets.HTML("<hr>"),
            self.color_selector.get_widget()
        ])
        
        self.tabs = widgets.Tab()
        self.tabs.children = [
            self.select_batch_tab,
            plot_tab_content,
            self.save_ui.get_widget()
        ]
        
        for i, title in enumerate(['Select Batches', 'Create Plots', 'Save Results']):
            self.tabs.set_title(i, title)
    
    def _setup_callbacks(self):
        self.auth_ui.set_success_callback(self._on_auth_success)
        self.plot_ui.set_plot_callback(self._on_create_plots)
        self.save_ui.set_save_callbacks(self._on_save_plots, lambda b: None, self._on_save_all)
        # NEW: filter button behavior
        self.batch_selector.set_filter_callback(self._on_filter_batches)
    
    def _auto_authenticate(self):
        is_hub = bool(os.environ.get('JUPYTERHUB_USER'))
        self.auth_ui.auth_method_selector.value = 'Token (from ENV)' if is_hub else 'Username/Password'
        self.auth_ui._on_auth_button_clicked(None)
    
    def _on_auth_success(self):
        self.tabs.selected_index = 0
        self.auth_ui.close_settings()
        self._init_batch_selection()
    
    def _init_batch_selection(self):
        """Initialize batch selection after authentication"""
        try:
            from api_calls import get_all_batches_wth_data
            url = self.auth_manager.url
            token = self.auth_manager.current_token
            
            # Get batch lab_ids that have UVVis data (matches JV-Analysis approach)
            batch_lab_ids = get_all_batches_wth_data(url, token, 'peroTF_UVvisMeasurement')
            
            # Sort batches by date (newest first) using shared utility
            batch_lab_ids_sorted = sort_by_date_desc(batch_lab_ids)
            
            # Display batch lab_ids directly (like JV-Analysis does)
            batch_options = [(lab_id, lab_id) for lab_id in batch_lab_ids_sorted]
            self.batch_selector.set_options(batch_options)
            
        except Exception as e:
            with self.load_status_output:
                print(f"❌ Error loading batches: {e}")
    
    # NEW: filter to batches that actually have UVVis data (triggered by button)
    def _on_filter_batches(self):
        try:
            from api_calls import get_all_batches_wth_data
            url = self.auth_manager.url
            token = self.auth_manager.current_token
            if not self.auth_manager.is_authenticated():
                with self.load_status_output:
                    print("❌ Authentication required")
                return
            with self.load_status_output:
                self.load_status_output.clear_output(wait=True)
                print("🔍 Filtering batches for UVVis data...")
            batch_lab_ids = get_all_batches_wth_data(url, token, 'peroTF_UVvisMeasurement')
            batch_lab_ids_sorted = sort_by_date_desc(batch_lab_ids)
            self.batch_selector.set_options([(lab_id, lab_id) for lab_id in batch_lab_ids_sorted])
            with self.load_status_output:
                print(f"✅ Found {len(batch_lab_ids_sorted)} batches with UVVis data")
        except Exception as e:
            with self.load_status_output:
                print(f"❌ Error filtering batches: {e}")
    
    def _load_data_from_selection(self, batch_selector):
        batch_lab_ids = list(batch_selector.value) if batch_selector.value else []
        
        success = self.data_manager.load_batch_data(batch_lab_ids, self.load_status_output)
        
        if success:
            with self.load_status_output:
                print(self.data_manager.get_summary_statistics())
            self.tabs.selected_index = 1
    
    def _on_create_plots(self, b):
        if not self.data_manager.has_data():
            with self.plot_ui.plotted_content:
                print("❌ No data loaded")
            return
        
        measurements = self.data_manager.get_data()['samples']
        colors = self.color_selector.get_colors(num_colors=len(measurements))
        selected_modes = [mode for mode, enabled in self.plot_ui.get_selected_plot_modes() if enabled]
        
        # Get x-axis setting (applies to all plots)
        x_axis_mode = self.plot_ui.get_x_axis_mode()
        
        figs, names = [], []
        with self.plot_ui.plotted_content:
            clear_output(wait=True)
            print("🔄 Creating plots...")
        
        try:
            if 'spectra_custom' in selected_modes:
                layout_mode = self.plot_ui.get_layout_mode()
                selected_channels = [c for c, enabled in self.plot_ui.get_selected_channels() if enabled]
                if not selected_channels:
                    raise ValueError("Select at least one channel (Reflection/Transmission/Absorption).")
                spectra_figs, spectra_names = self.plot_manager.create_spectra_plot(
                    measurements,
                    color_scheme=colors,
                    layout_mode=layout_mode,
                    channels=selected_channels,
                    x_axis=x_axis_mode  # NEW: Pass x_axis setting
                )
                if not isinstance(spectra_figs, list):
                    spectra_figs, spectra_names = [spectra_figs], [spectra_names]
                figs += spectra_figs
                names += spectra_names
            if 'bandgap_derivative' in selected_modes:
                fig, name = self.plot_manager.create_bandgap_derivative_plot(
                    measurements, colors, x_axis_mode  # x_axis_mode already used here
                )
                figs.append(fig)
                names.append(name)
            if 'tauc_plot' in selected_modes:
                thickness = self.plot_ui.get_thickness()
                fig, name = self.plot_manager.create_tauc_plot(
                    measurements, colors, thickness
                )
                figs.append(fig)
                names.append(name)
            
            if not figs:
                raise ValueError("No plot type selected.")
            
            self.global_plot_data = {'figs': figs, 'names': names}
            
            with self.plot_ui.plotted_content:
                clear_output(wait=True)
                ResizablePlotManager.display_plots_resizable(
                    figs, names, container_widget=self.plot_ui.plotted_content
                )
                print("✅ Plots created! Proceed to save tab.")
            
            self.tabs.selected_index = 2
            
        except Exception as e:
            with self.plot_ui.plotted_content:
                clear_output(wait=True)
                print(f"❌ Plot creation failed: {e}")
                import traceback
                traceback.print_exc()
    
    def _on_save_plots(self, b):
        if not self.global_plot_data.get('figs'):
            with self.save_ui.download_output:
                print("❌ No plots to save")
            return
        
        try:
            zip_content = self.save_ui.create_plots_zip(
                self.global_plot_data['figs'],
                self.global_plot_data['names']
            )
            self.save_ui.trigger_download(zip_content, 'uvvis_plots.zip', 'application/zip')
        except Exception as e:
            with self.save_ui.download_output:
                print(f"❌ Save failed: {e}")
    
    def _on_save_all(self, b):
        self._on_save_plots(b)
    
    def get_dashboard(self):
        return widgets.VBox([
            widgets.HTML("<h1>UVVis Analysis Dashboard</h1>"),
            self.auth_ui.get_widget(),
            self.tabs
        ], layout=widgets.Layout(max_width="1200px", margin="0 auto", padding='15px'))

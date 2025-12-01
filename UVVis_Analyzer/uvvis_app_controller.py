"""
UVVis Application Controller
Main orchestrator for the UVVis Analysis Dashboard.
"""

__author__ = "Adapted from JV Analysis"
__institution__ = "Helmholtz-Zentrum Berlin / KIT"
__created__ = "January 2025"

import ipywidgets as widgets
from IPython.display import display, clear_output, Markdown
import os
import sys

# Add parent directory
parent_dir = os.path.dirname(os.path.dirname(os.getcwd()))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Add JV-Analysis directory for shared components
jv_dir = os.path.join(parent_dir, 'JV-Analysis_v6')
if jv_dir not in sys.path:
    sys.path.append(jv_dir)

from uvvis_data_manager import UVVisDataManager
from uvvis_plot_manager import UVVisPlotManager
from uvvis_gui_components import UVVisAuthenticationUI, UVVisBatchSelector, UVVisPlotUI, UVVisSaveUI
from gui_components import ColorSchemeSelector
from resizable_plot_utility import ResizablePlotManager


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
    
    def authenticate_with_credentials(self, username, password):
        import requests
        if not username or not password:
            raise ValueError("Username and Password required")
        
        auth_dict = dict(username=username, password=password)
        token_url = f"{self.url}/auth/token"
        
        response = requests.get(token_url, params=auth_dict, timeout=10)
        response.raise_for_status()
        
        token_data = response.json()
        self.current_token = token_data['access_token']
        return self.current_token
    
    def authenticate_with_token(self, token=None):
        if token is None:
            token = os.environ.get('NOMAD_CLIENT_ACCESS_TOKEN')
            if not token:
                raise ValueError("Token not found")
        self.current_token = token
        return self.current_token
    
    def verify_token(self):
        import requests
        verify_url = f"{self.url}/users/me"
        headers = {'Authorization': f'Bearer {self.current_token}'}
        verify_response = requests.get(verify_url, headers=headers, timeout=10)
        verify_response.raise_for_status()
        self.current_user_info = verify_response.json()
        return self.current_user_info
    
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
            from api_calls import get_user_batches
            url = self.auth_manager.url
            token = self.auth_manager.current_token
            
            batches = get_user_batches(url, token)
            batch_options = [(f"{b['upload_id']} - {b.get('upload_name', 'Unnamed')}", b['upload_id']) for b in batches]
            self.batch_selector.set_options(batch_options)
            
        except Exception as e:
            with self.load_status_output:
                print(f"❌ Error loading batches: {e}")
    
    def _load_data_from_selection(self, batch_selector):
        batch_ids = list(batch_selector.value) if batch_selector.value else []
        
        success = self.data_manager.load_batch_data(batch_ids, self.load_status_output)
        
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
        plot_mode = self.plot_ui.get_plot_mode()
        colors = self.color_selector.get_colors(num_colors=len(measurements))
        
        with self.plot_ui.plotted_content:
            clear_output(wait=True)
            print("🔄 Creating plots...")
        
        try:
            figs, names = self.plot_manager.create_spectra_plot(measurements, colors, plot_mode)
            
            if not isinstance(figs, list):
                figs = [figs]
                names = [names]
            
            self.global_plot_data = {'figs': figs, 'names': names}
            
            with self.plot_ui.plotted_content:
                clear_output(wait=True)
                ResizablePlotManager.display_plots_resizable(figs, names, container_widget=self.plot_ui.plotted_content)
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

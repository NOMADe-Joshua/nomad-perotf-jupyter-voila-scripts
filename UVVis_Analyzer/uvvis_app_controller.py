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

# Add parent directory for shared modules
parent_dir = os.path.dirname(os.getcwd())
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# CRITICAL FIX: Add JV-Analysis directory to path for shared components
jv_dir = os.path.join(parent_dir, 'JV-Analysis_v6')
if jv_dir not in sys.path:
    sys.path.append(jv_dir)

# Import shared authentication module (like JV script does)
try:
    from auth_manager import AuthenticationManager
    import access_token
except ImportError as e:
    print(f"⚠️ Warning: Could not import shared auth modules: {e}")
    AuthenticationManager = None

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


class UVVisAnalysisApp:
    """Main UVVis analysis application"""
    
    def __init__(self):
        # Use shared AuthenticationManager from parent directory (like JV script)
        if AuthenticationManager:
            self.auth_manager = AuthenticationManager("http://elnserver.lti.kit.edu", "/nomad-oasis/api/v1")
        else:
            # Fallback: create minimal auth manager if shared module not available
            print("⚠️ Warning: Using fallback authentication - shared auth_manager not found")
            self.auth_manager = self._create_minimal_auth_manager()
        
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
        self.bandgap_download_box = widgets.VBox()
        
        self.load_status_output = widgets.Output(
            layout=widgets.Layout(border='1px solid #eee', padding='10px', margin='10px 0')
        )
    
    def _create_tabs(self):
        self.select_batch_tab = widgets.VBox([
            widgets.HTML("<h3>Select Upload</h3>"),
            widgets.HTML("<p><i>Select one or multiple batches</i></p>"),
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
            widgets.VBox([
                self.save_ui.get_widget(),
                widgets.HTML("<hr>"),
                widgets.HTML("<h3>Bandgap Table Downloads</h3>"),
                self.bandgap_download_box
            ])
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
            
            # NEW: Automatically adjust color count to number of variations
            num_variations = self._count_unique_variations()
            self.color_selector.set_num_colors(num_variations)
            
            self.tabs.selected_index = 1
    
    # NEW: Helper method to count unique variations
    def _count_unique_variations(self):
        """Count unique variations/samples in loaded data"""
        if not self.data_manager.has_data():
            return 6  # Default fallback
        
        measurements = self.data_manager.get_data()['samples']
        variations = set(m.get('variation', m.get('sample_name', '')) for m in measurements)
        num_variations = len(variations)
        
        # Ensure reasonable bounds (min 2, max 20)
        num_variations = max(2, min(20, num_variations))
        
        with self.load_status_output:
            print(f"🎨 Auto-adjusted color palette: {num_variations} colors for {len(variations)} unique variations")
        
        return num_variations
    
    def _on_create_plots(self, b):
        if not self.data_manager.has_data():
            with self.plot_ui.plotted_content:
                print("❌ No data loaded")
            return
        
        measurements = self.data_manager.get_data()['samples']
        selected_modes = [mode for mode, enabled in self.plot_ui.get_selected_plot_modes() if enabled]
        
        # Get x-axis setting (applies to all plots)
        x_axis_mode = self.plot_ui.get_x_axis_mode()
        
        # NEW: build variation->color map preserving measurement order (not sorted)
        # Track unique variations in order of first appearance
        seen_variations = {}
        for measurement in measurements:
            var = measurement.get('variation', measurement.get('sample_name', ''))
            if var not in seen_variations:
                seen_variations[var] = len(seen_variations)
        
        # Get colors for number of unique variations
        colors = self.color_selector.get_colors(num_colors=len(seen_variations))
        # Map each variation to its color in order of first appearance
        color_map = {var: colors[idx % len(colors)] for var, idx in seen_variations.items()}
        
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
                    x_axis=x_axis_mode,
                    color_map=color_map  # NEW
                )
                if not isinstance(spectra_figs, list):
                    spectra_figs, spectra_names = [spectra_figs], [spectra_names]
                figs += spectra_figs
                names += spectra_names
            if 'bandgap_derivative' in selected_modes:
                bandgap_options = self.plot_ui.get_bandgap_options()
                fig, name, bandgap_table = self.plot_manager.create_bandgap_derivative_plot(
                    measurements, colors, x_axis_mode, color_map=color_map,
                    bandgap_options=bandgap_options
                )
                figs.append(fig)
                names.append(name)
                
                # Store bandgap table for display
                if bandgap_table and bandgap_options.get('show_table', True):
                    if not hasattr(self, 'bandgap_tables'):
                        self.bandgap_tables = []
                    self.bandgap_tables.append(bandgap_table)
                    # Persist latest tables for save tab
                    self.latest_bandgap_tables = list(getattr(self, 'bandgap_tables', []))
            if 'tauc_plot' in selected_modes:
                thickness = self.plot_ui.get_thickness()
                fig, name = self.plot_manager.create_tauc_plot(
                    measurements, colors, thickness, color_map=color_map  # NEW
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
                
                # Display bandgap tables if available
                if hasattr(self, 'bandgap_tables') and self.bandgap_tables:
                    for table_data in self.bandgap_tables:
                        self._display_bandgap_table(table_data)
                    # Update save-tab downloads
                    self._update_bandgap_downloads(self.bandgap_tables)
                    # Clear for next plot creation (but keep latest for save tab)
                    self.bandgap_tables = []
                
                print("✅ Plots created! You can now save them using the 'Save Results' tab.")
            
            # Removed: self.tabs.selected_index = 2
            
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
    
    def _display_bandgap_table(self, table_data):
        """Display bandgap table below plots and offer downloads"""
        import pandas as pd
        from IPython.display import display, HTML
        import io
        import plotly.graph_objects as go
        import ipywidgets as widgets
        import base64
        
        if not table_data:
            return
        
        # Create dataframe for reuse (CSV + plotly table)
        df = pd.DataFrame([
            {
                'Sample': row['Sample'],
                'Bandgap(s) [eV]': ', '.join([f"{bg:.2f}" for bg in sorted(row['Bandgaps (eV)'])]),
                '# Peaks': len(row['Bandgaps (eV)'])
            }
            for row in table_data
        ])
        
        # Create HTML table for inline display
        html = '<div style="margin-top: 20px; padding: 15px; background-color: #f8f9fa; border-radius: 5px;">'
        html += '<h4 style="margin-top: 0; color: #2c3e50; display: flex; align-items: center; gap: 10px;">📊 Fitted Bandgap Values</h4>'
        html += '<table style="width: 100%; border-collapse: collapse; background: white;">'
        html += '<thead><tr style="background-color: #007bff; color: white;">'
        html += '<th style="padding: 10px; text-align: left; border: 1px solid #ddd;">Sample</th>'
        html += '<th style="padding: 10px; text-align: left; border: 1px solid #ddd;">Bandgap(s) [eV]</th>'
        html += '<th style="padding: 10px; text-align: center; border: 1px solid #ddd;"># Peaks</th>'
        html += '</tr></thead><tbody>'
        
        for _, row in df.iterrows():
            html += f'<tr>'
            html += f'<td style="padding: 8px; border: 1px solid #ddd;">{row["Sample"]}</td>'
            html += f'<td style="padding: 8px; border: 1px solid #ddd; font-family: monospace;">{row["Bandgap(s) [eV]"]}</td>'
            html += f'<td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{row["# Peaks"]}</td>'
            html += f'</tr>'
        
        html += '</tbody></table>'
        html += '<div style="margin-top: 10px; display: flex; gap: 10px; flex-wrap: wrap;">'
        html += '<span style="color: #6c757d;">Download:</span>'
        html += '</div>'
        html += '</div>'
        
        # Prepare downloads (FileDownload may be missing on older ipywidgets)
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False, sep=';')
        csv_bytes = csv_buffer.getvalue().encode('utf-8')
        csv_dl = None
        try:
            csv_dl = widgets.FileDownload(
                data=csv_bytes,
                filename='bandgaps.csv',
                description='⬇️ CSV',
                button_style='primary',
                layout=widgets.Layout(width='120px')
            )
        except AttributeError:
            b64 = base64.b64encode(csv_bytes).decode('utf-8')
            csv_link = widgets.HTML(
                value=f'<a download="bandgaps.csv" href="data:text/csv;base64,{b64}" '
                      f'style="text-decoration:none"><button style="padding:6px 12px;background:#007bff;color:white;border:none;border-radius:4px;">⬇️ CSV</button></a>'
            )
            csv_dl = csv_link
        
        # Plotly table to image (PNG) using kaleido if available
        png_bytes = None
        try:
            fig = go.Figure(data=[go.Table(
                header=dict(values=list(df.columns), fill_color='#007bff', font=dict(color='white', size=10), align='left', height=25),
                cells=dict(values=[df[col] for col in df.columns], align='left', height=22, font=dict(size=9))
            )])
            fig.update_layout(
                width=650, 
                height=50 + 22 * len(df),
                margin=dict(l=0, r=0, t=0, b=0),
                paper_bgcolor='white',
                plot_bgcolor='white'
            )
            png_bytes = fig.to_image(format='png', scale=2)
        except Exception as e:
            png_bytes = None
            print(f"⚠️ PNG export unavailable (kaleido missing?): {e}")
        
        png_dl = None
        if png_bytes:
            try:
                png_dl = widgets.FileDownload(
                    data=png_bytes,
                    filename='bandgaps.png',
                    description='⬇️ PNG',
                    button_style='info',
                    layout=widgets.Layout(width='120px')
                )
            except AttributeError:
                b64 = base64.b64encode(png_bytes).decode('utf-8')
                png_link = widgets.HTML(
                    value=f'<a download="bandgaps.png" href="data:image/png;base64,{b64}" '
                          f'style="text-decoration:none"><button style="padding:6px 12px;background:#17a2b8;color:white;border:none;border-radius:4px;">⬇️ PNG</button></a>'
                )
                png_dl = png_link
        
        # Display table and buttons
        display(HTML(html))
        downloads = [csv_dl] + ([png_dl] if png_dl else [])
        display(widgets.HBox(downloads))

    def _update_bandgap_downloads(self, tables):
        """Populate bandgap download buttons on Save Results tab"""
        import pandas as pd
        import io
        import base64
        import plotly.graph_objects as go
        import ipywidgets as widgets

        self.bandgap_download_box.children = []
        if not tables:
            self.bandgap_download_box.children = [widgets.HTML("<i>No bandgap table available. Create plots first.</i>")]
            return

        # Merge all tables into one DataFrame
        rows = []
        for table in tables:
            for row in table:
                rows.append({
                    'Sample': row['Sample'],
                    'Bandgap(s) [eV]': ', '.join([f"{bg:.2f}" for bg in sorted(row['Bandgaps (eV)'])]),
                    '# Peaks': len(row['Bandgaps (eV)'])
                })
        df = pd.DataFrame(rows)

        # CSV download
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False, sep=';')
        csv_bytes = csv_buffer.getvalue().encode('utf-8')
        csv_widget = None
        try:
            csv_widget = widgets.FileDownload(
                data=csv_bytes,
                filename='bandgaps.csv',
                description='⬇️ CSV',
                button_style='primary',
                layout=widgets.Layout(width='120px')
            )
        except AttributeError:
            b64 = base64.b64encode(csv_bytes).decode('utf-8')
            csv_widget = widgets.HTML(
                value=f'<a download="bandgaps.csv" href="data:text/csv;base64,{b64}" '
                      f'style="text-decoration:none"><button style="padding:6px 12px;background:#007bff;color:white;border:none;border-radius:4px;">⬇️ CSV</button></a>'
            )

        # PNG download (optional, kaleido)
        png_widget = None
        try:
            fig = go.Figure(data=[go.Table(
                header=dict(values=list(df.columns), fill_color='#007bff', font=dict(color='white', size=10), align='left', height=25),
                cells=dict(values=[df[col] for col in df.columns], align='left', height=22, font=dict(size=9))
            )])
            fig.update_layout(
                width=650,
                height=50 + 22 * len(df),
                margin=dict(l=0, r=0, t=0, b=0),
                paper_bgcolor='white',
                plot_bgcolor='white'
            )
            png_bytes = fig.to_image(format='png', scale=2)
            try:
                png_widget = widgets.FileDownload(
                    data=png_bytes,
                    filename='bandgaps.png',
                    description='⬇️ PNG',
                    button_style='info',
                    layout=widgets.Layout(width='120px')
                )
            except AttributeError:
                b64 = base64.b64encode(png_bytes).decode('utf-8')
                png_widget = widgets.HTML(
                    value=f'<a download="bandgaps.png" href="data:image/png;base64,{b64}" '
                          f'style="text-decoration:none"><button style="padding:6px 12px;background:#17a2b8;color:white;border:none;border-radius:4px;">⬇️ PNG</button></a>'
                )
        except Exception as e:
            print(f"⚠️ PNG export unavailable (kaleido missing?): {e}")

        downloads = [w for w in [csv_widget, png_widget] if w is not None]
        if downloads:
            self.bandgap_download_box.children = [widgets.HBox(downloads)]
        else:
            self.bandgap_download_box.children = [widgets.HTML("<i>Downloads unavailable.</i>")]
    
    def get_dashboard(self):
        return widgets.VBox([
            widgets.HTML("<h1>UVVis Analysis Dashboard</h1>"),
            self.auth_ui.get_widget(),
            self.tabs
        ], layout=widgets.Layout(max_width="1200px", margin="0 auto", padding='15px'))

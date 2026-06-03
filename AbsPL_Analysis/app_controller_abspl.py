"""
Modular AbsPL app controller with JV-style Select Upload flow.
"""

import os
import sys
import requests
import ipywidgets as widgets
from IPython.display import display, clear_output

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
JV_DIR = os.path.abspath(os.path.join(ROOT, "JV-Analysis_v6"))

for path in [ROOT, HERE, JV_DIR]:
    if path not in sys.path:
        sys.path.append(path)

from auth_manager import AuthenticationManager
from batch_selection import create_batch_selection
from diagnostic_helper_abspl import debug_logger_abspl
from data_manager_abspl import AbsPLDataManager
from plot_manager_abspl import AbsPLPlotManager
from gui_components_abspl import AbsPLGUIComponents
from resizable_plot_utility_abspl import ResizablePlotManager
from auth_ui import AuthenticationUI


class AbsPLAppController:
    def __init__(self, url_base="http://elnserver.lti.kit.edu", api_endpoint="/nomad-oasis/api/v1"):
        self.auth_manager = AuthenticationManager(url_base, api_endpoint)
        self.data_manager = AbsPLDataManager(self.auth_manager)
        self.plot_manager = AbsPLPlotManager()
        self.gui = AbsPLGUIComponents()
        self.resizable_plot_manager = ResizablePlotManager()

        self.auth_ui = AuthenticationUI(self.auth_manager)
        self.batch_selection_container = widgets.Output()
        self.load_status_output = widgets.Output(
            layout=widgets.Layout(border="1px solid #eee", padding="10px", margin="10px 0 0 0", min_height="100px")
        )

        self.refresh_diag_button = widgets.Button(description="Refresh Diagnostics", button_style="info")
        self.clear_diag_button = widgets.Button(description="Clear Diagnostics")

        self.main_layout = widgets.Tab()

        self._bind_events()
        self._build_layout()
        self._auto_authenticate()

    def _bind_events(self):
        self.auth_ui.set_success_callback(self._on_auth_success)

        self.gui.apply_filters_button.on_click(self._on_apply_filters)
        self.gui.create_plots_button.on_click(self._on_create_plots)

        self.refresh_diag_button.on_click(self._on_refresh_diagnostics)
        self.clear_diag_button.on_click(self._on_clear_diagnostics)

    def _build_layout(self):
        select_upload_tab = widgets.VBox(
            [
                self.auth_ui.get_widget(),
                widgets.HTML("<h3>Select Upload</h3>"),
                widgets.HTML("<p><i>Select one or multiple batches</i></p>"),
                self.batch_selection_container,
                self.load_status_output,
            ]
        )

        diagnostics_box = widgets.VBox(
            [
                widgets.HBox([self.refresh_diag_button, self.clear_diag_button]),
                self.gui.output_diagnostics,
            ]
        )

        self.main_layout.children = [select_upload_tab, self.gui.filter_panel, self.gui.plot_panel, diagnostics_box]
        self.main_layout.set_title(0, "Select Upload")
        self.main_layout.set_title(1, "Select Filters")
        self.main_layout.set_title(2, "Select Plots")
        self.main_layout.set_title(3, "Diagnostics")

    def _auto_authenticate(self):
        """Auto-authenticate exactly like JV flow."""
        is_hub_environment = bool(os.environ.get("JUPYTERHUB_USER"))

        if is_hub_environment:
            self.auth_ui.auth_method_selector.value = "Token (from ENV)"
            self.auth_ui.local_auth_box.layout.display = "none"
        else:
            self.auth_ui.auth_method_selector.value = "Username/Password"
            self.auth_ui.local_auth_box.layout.display = "flex"

        self.auth_ui._on_auth_button_clicked(None)

    def _on_auth_success(self):
        self.main_layout.selected_index = 0
        self._init_batch_selection()

    def _init_batch_selection(self):
        with self.batch_selection_container:
            clear_output(wait=True)

            if not self.auth_manager.is_authenticated():
                print("Please authenticate first before loading batch data.")
                return

            try:
                url = self.auth_manager.url
                token = self.auth_manager.current_token
                batch_selection_widget = create_batch_selection(url, token, self._load_data_from_selection)
                display(batch_selection_widget)
                debug_logger_abspl.add("AUTH", "Batch selector initialized", level="SUCCESS")
            except requests.exceptions.RequestException as exc:
                print(f"Server error while loading batch selection: {exc}")
                debug_logger_abspl.add("AUTH", f"Batch selector server error: {exc}", level="ERROR")
            except Exception as exc:
                print(f"Error while loading batch selection: {exc}")
                debug_logger_abspl.add("AUTH", f"Batch selector init failed: {exc}", level="ERROR")

        self._on_refresh_diagnostics(None)

    def _load_data_from_selection(self, batch_selector):
        batch_ids = list(batch_selector.value) if batch_selector.value else []

        with self.load_status_output:
            clear_output(wait=True)
            print(f"Loading selected batches: {len(batch_ids)}")

        try:
            ok = self.data_manager.load_batch_data(batch_ids)
            if ok:
                options = self.data_manager.get_filter_options()
                self.gui.update_filter_options(options)
                with self.load_status_output:
                    print("Loaded successfully. Filter options updated.")
                debug_logger_abspl.add("LOAD", f"Loaded data for {len(batch_ids)} batches", level="SUCCESS")
            else:
                with self.load_status_output:
                    print("No AbsPL data found for selected filters.")
                debug_logger_abspl.add("LOAD", "No AbsPL data found", level="WARNING")
        except Exception as exc:
            with self.load_status_output:
                print(f"Data loading failed: {exc}")
            debug_logger_abspl.add("LOAD", f"Data loading failed: {exc}", level="ERROR")

        self._on_refresh_diagnostics(None)

    def _on_apply_filters(self, _):
        cfg = self.gui.get_filter_config()
        summary_df, spectra_df = self.data_manager.apply_filters(cfg)

        with self.load_status_output:
            clear_output(wait=True)
            print(f"Filtered summary rows: {len(summary_df)}")
            print(f"Filtered spectra rows: {len(spectra_df)}")

        self._on_refresh_diagnostics(None)

    def _make_figure(self, spec, summary_df, spectra_df):
        ptype = spec.get("plot_type")
        a = spec.get("option_a")
        b = spec.get("option_b")
        c = spec.get("option_c")

        if ptype == "Spectra Overlay":
            normalize = b == "yes"
            log_y = c == "log"
            return self.plot_manager.spectra_overlay(spectra_df, color_by=a, normalize=normalize, log_y=log_y)

        if ptype == "Average Spectra":
            y_source = b if b in ["auto", "luminescence_flux_density", "raw_spectrum_counts"] else "auto"
            return self.plot_manager.average_spectra(spectra_df, group_by=a, y_source=y_source)

        if ptype == "Sweep Heatmap":
            sample = None if a in [None, "-"] else a
            source = b if b in ["raw_spectrum_counts", "luminescence_flux_density"] else "raw_spectrum_counts"
            return self.plot_manager.sweep_heatmap(spectra_df, sample=sample, intensity_source=source)

        if ptype == "Scalar Boxplot":
            return self.plot_manager.scalar_boxplot(summary_df, y_col=a, x_col=b)

        if ptype == "Scalar Scatter":
            return self.plot_manager.scalar_scatter(summary_df, x_col=a, y_col=b, color_col=c)

        return None

    def _on_create_plots(self, _):
        summary_df, spectra_df = self.data_manager.get_filtered_data()
        if summary_df.empty or spectra_df.empty:
            summary_df = self.data_manager.get_data().get("summary")
            spectra_df = self.data_manager.get_data().get("spectra")

        specs = self.gui.get_plot_specs()
        if not specs:
            with self.load_status_output:
                clear_output(wait=True)
                print("No plot rows configured.")
            return

        figs = []
        names = []
        for i, spec in enumerate(specs, start=1):
            try:
                fig = self._make_figure(spec, summary_df, spectra_df)
                if fig is not None:
                    figs.append(fig)
                    names.append(f"abspl_plot_{i}")
                    debug_logger_abspl.add("PLOT", f"Generated plot {i}: {spec['plot_type']}", level="SUCCESS")
            except Exception as exc:
                debug_logger_abspl.add("PLOT", f"Plot {i} failed ({spec.get('plot_type')}): {exc}", level="ERROR")

        with self.gui.output_plots:
            clear_output(wait=True)
            if not figs:
                print("No figures generated.")
            else:
                self.resizable_plot_manager.display_plots_resizable(figs, filenames=names)

        self._on_refresh_diagnostics(None)

    def _on_refresh_diagnostics(self, _):
        self.gui.output_diagnostics.value = debug_logger_abspl.get_html()

    def _on_clear_diagnostics(self, _):
        debug_logger_abspl.clear()
        self._on_refresh_diagnostics(None)

    def display(self):
        self._on_refresh_diagnostics(None)
        display(self.main_layout)
        return self.main_layout


def launch_abspl_app(url_base="http://elnserver.lti.kit.edu"):
    app = AbsPLAppController(url_base=url_base)
    app.display()
    return app

"""
GUI components for modular AbsPL analysis app.
"""

import ipywidgets as widgets


class AbsPLGUIComponents:
    def __init__(self):
        self.data_loaded = False
        self.filter_options = {
            "measurement_types": [],
            "samples": [],
            "laser_spot_sizes": [],
            "numeric_columns": [],
        }

        self.output_messages = widgets.Output(layout=widgets.Layout(border="1px solid #d0d5dd", padding="8px"))
        self.output_plots = widgets.Output()
        self.output_diagnostics = widgets.HTML(value="")

        self._build_filter_widgets()
        self._build_plot_widgets()

    def _build_filter_widgets(self):
        self.measurement_types = widgets.SelectMultiple(
            options=[], description="Type", layout=widgets.Layout(width="360px", height="110px")
        )
        self.samples = widgets.SelectMultiple(
            options=[], description="Samples", layout=widgets.Layout(width="560px", height="160px")
        )
        self.laser_spot_sizes = widgets.SelectMultiple(
            options=[], description="Spot size", layout=widgets.Layout(width="360px", height="110px")
        )

        self.cycle_mode = widgets.Dropdown(
            options=[("All cycles", "all"), ("First cycle", "first"), ("Last cycle", "last"), ("Specific cycles", "specific")],
            value="all",
            description="Cycle mode",
            layout=widgets.Layout(width="320px"),
        )
        self.specific_cycles = widgets.Text(
            value="", description="Cycles", placeholder="e.g. 1,2,5", layout=widgets.Layout(width="260px")
        )

        self.num_col = widgets.Dropdown(options=[], description="Numeric", layout=widgets.Layout(width="260px"))
        self.num_op = widgets.Dropdown(
            options=[">", ">=", "<", "<=", "==", "!="], value=">", description="Op", layout=widgets.Layout(width="160px")
        )
        self.num_val = widgets.FloatText(value=0.0, description="Value", layout=widgets.Layout(width="180px"))
        self.add_numeric_filter_btn = widgets.Button(description="Add Numeric Filter", button_style="info")
        self.clear_numeric_filter_btn = widgets.Button(description="Clear Numeric Filters")
        self.numeric_filter_list = widgets.SelectMultiple(
            options=[], description="Active", layout=widgets.Layout(width="700px", height="120px")
        )

        self.apply_filters_button = widgets.Button(description="Apply Filters", button_style="primary")

        self.add_numeric_filter_btn.on_click(self._add_numeric_filter)
        self.clear_numeric_filter_btn.on_click(self._clear_numeric_filters)

        self._numeric_filters = []

        numeric_box = widgets.HBox([
            self.num_col,
            self.num_op,
            self.num_val,
            self.add_numeric_filter_btn,
            self.clear_numeric_filter_btn,
        ])

        self.filter_panel = widgets.VBox(
            [
                widgets.HTML("<h3>Filter Measurements</h3>"),
                widgets.HBox([self.measurement_types, self.laser_spot_sizes]),
                self.samples,
                widgets.HBox([self.cycle_mode, self.specific_cycles]),
                widgets.HTML("<b>Numeric filter (pre-plot):</b>"),
                numeric_box,
                self.numeric_filter_list,
                self.apply_filters_button,
            ]
        )

    def _build_plot_widgets(self):
        self.plot_rows = []
        self.plot_rows_container = widgets.VBox([])

        self.add_plot_button = widgets.Button(description="Add Plot", button_style="success")
        self.clear_plots_button = widgets.Button(description="Clear Plot Rows")
        self.create_plots_button = widgets.Button(description="Create Plots", button_style="primary")

        self.add_plot_button.on_click(self._add_plot_row)
        self.clear_plots_button.on_click(self._clear_plot_rows)

        self.plot_panel = widgets.VBox(
            [
                widgets.HTML("<h3>Select Plots</h3>"),
                widgets.HBox([self.add_plot_button, self.clear_plots_button, self.create_plots_button]),
                self.plot_rows_container,
                self.output_plots,
            ]
        )

        self._add_plot_row(None)

    def _add_numeric_filter(self, _):
        col = self.num_col.value
        if not col:
            return
        item = (str(col), str(self.num_op.value), float(self.num_val.value))
        self._numeric_filters.append(item)
        self._sync_numeric_filter_list()

    def _clear_numeric_filters(self, _):
        self._numeric_filters = []
        self._sync_numeric_filter_list()

    def _sync_numeric_filter_list(self):
        opts = [f"{c} {op} {v}" for c, op, v in self._numeric_filters]
        self.numeric_filter_list.options = opts

    def _add_plot_row(self, _):
        kind = widgets.Dropdown(
            options=[
                "Spectra Overlay",
                "Average Spectra",
                "Sweep Heatmap",
                "Scalar Boxplot",
                "Scalar Scatter",
            ],
            value="Spectra Overlay",
            description="Plot",
            layout=widgets.Layout(width="260px"),
        )
        opt_a = widgets.Dropdown(description="A", layout=widgets.Layout(width="240px"))
        opt_b = widgets.Dropdown(description="B", layout=widgets.Layout(width="240px"))
        opt_c = widgets.Dropdown(description="C", layout=widgets.Layout(width="240px"))
        remove_btn = widgets.Button(description="Remove", button_style="danger", layout=widgets.Layout(width="100px"))

        row = {"kind": kind, "a": opt_a, "b": opt_b, "c": opt_c, "remove": remove_btn}

        def refresh_options(*_args):
            scalar_cols = self.filter_options.get("numeric_columns", [])
            sample_opts = self.filter_options.get("samples", [])
            if kind.value == "Spectra Overlay":
                opt_a.options = ["condition", "sample_id", "batch", "measurement_type", "laser_spot_size"]
                opt_a.value = "condition"
                opt_b.options = [("Normalize: No", "no"), ("Normalize: Yes", "yes")]
                opt_b.value = "no"
                opt_c.options = [("Y scale linear", "linear"), ("Y scale log", "log")]
                opt_c.value = "linear"
            elif kind.value == "Average Spectra":
                opt_a.options = ["condition", "sample_id", "batch", "measurement_type"]
                opt_a.value = "condition"
                opt_b.options = [("Source: Auto", "auto"), ("Flux", "luminescence_flux_density"), ("Raw", "raw_spectrum_counts")]
                opt_b.value = "auto"
                opt_c.options = ["-"]
                opt_c.value = "-"
            elif kind.value == "Sweep Heatmap":
                opt_a.options = sample_opts if sample_opts else ["-"]
                opt_a.value = opt_a.options[0]
                opt_b.options = [("Raw", "raw_spectrum_counts"), ("Flux", "luminescence_flux_density"), ("Auto", "auto")]
                opt_b.value = "raw_spectrum_counts"
                opt_c.options = ["-"]
                opt_c.value = "-"
            elif kind.value == "Scalar Boxplot":
                opts = scalar_cols if scalar_cols else ["luminescence_quantum_yield"]
                opt_a.options = opts
                opt_a.value = opts[0]
                opt_b.options = ["condition", "sample_id", "batch", "measurement_type", "laser_spot_size"]
                opt_b.value = "condition"
                opt_c.options = ["-"]
                opt_c.value = "-"
            elif kind.value == "Scalar Scatter":
                opts = scalar_cols if scalar_cols else ["laser_intensity_suns", "luminescence_quantum_yield"]
                opt_a.options = opts
                opt_a.value = opts[0]
                opt_b.options = opts
                opt_b.value = opts[1] if len(opts) > 1 else opts[0]
                opt_c.options = ["condition", "sample_id", "batch", "measurement_type", "laser_spot_size"]
                opt_c.value = "condition"

        kind.observe(refresh_options, names="value")

        def remove_row(_btn):
            self.plot_rows = [r for r in self.plot_rows if r is not row]
            self._render_plot_rows()

        remove_btn.on_click(remove_row)

        self.plot_rows.append(row)
        refresh_options()
        self._render_plot_rows()

    def _clear_plot_rows(self, _):
        self.plot_rows = []
        self._render_plot_rows()

    def _render_plot_rows(self):
        widget_rows = []
        for row in self.plot_rows:
            widget_rows.append(widgets.HBox([row["kind"], row["a"], row["b"], row["c"], row["remove"]]))
        self.plot_rows_container.children = tuple(widget_rows)

    def update_filter_options(self, options):
        self.filter_options = options

        self.measurement_types.options = options.get("measurement_types", [])
        self.measurement_types.value = tuple(options.get("measurement_types", []))

        self.samples.options = options.get("samples", [])
        self.samples.value = tuple([])

        self.laser_spot_sizes.options = options.get("laser_spot_sizes", [])
        self.laser_spot_sizes.value = tuple(options.get("laser_spot_sizes", []))

        numeric_columns = options.get("numeric_columns", [])
        self.num_col.options = numeric_columns
        self.num_col.value = numeric_columns[0] if numeric_columns else None

        for row in self.plot_rows:
            try:
                row["kind"].value = row["kind"].value
            except Exception:
                pass

    def get_filter_config(self):
        cycles = []
        text = self.specific_cycles.value.strip()
        if text:
            for part in text.split(","):
                part = part.strip()
                if part.isdigit():
                    cycles.append(int(part))

        return {
            "measurement_types": list(self.measurement_types.value),
            "samples": list(self.samples.value),
            "laser_spot_sizes": list(self.laser_spot_sizes.value),
            "cycle_mode": self.cycle_mode.value,
            "specific_cycles": cycles,
            "numeric_filters": list(self._numeric_filters),
        }

    def get_plot_specs(self):
        specs = []
        for row in self.plot_rows:
            specs.append(
                {
                    "plot_type": row["kind"].value,
                    "option_a": row["a"].value,
                    "option_b": row["b"].value,
                    "option_c": row["c"].value,
                }
            )
        return specs

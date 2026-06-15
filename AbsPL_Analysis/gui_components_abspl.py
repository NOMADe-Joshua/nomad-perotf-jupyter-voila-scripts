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
            "cycles": [],
            "numeric_columns": [],
        }
        self._filter_rows = []
        self.selection_rows = []
        self._auto_apply_callback = None
        self._suspend_auto_apply = False

        self.output_messages = widgets.Output(layout=widgets.Layout(border="1px solid #d0d5dd", padding="8px"))
        self.output_plots = widgets.Output()
        self.output_diagnostics = widgets.HTML(value="")

        self._build_filter_widgets()
        self._build_plot_widgets()

    def _build_filter_widgets(self):
        self.selection_rows_container = widgets.VBox([])
        self.add_filter_row_button = widgets.Button(description="Add Selection", button_style="info")
        self.clear_filter_rows_button = widgets.Button(description="Clear Selections")
        self.apply_filters_button = widgets.Button(description="Apply Filters", button_style="primary")
        self.auto_apply_toggle = widgets.Checkbox(value=False, description="Apply instantly")

        self.add_filter_row_button.on_click(self._add_selection_row)
        self.clear_filter_rows_button.on_click(self._clear_selection_rows)

        self.filter_panel = widgets.VBox(
            [
                widgets.HTML("<h3>Filter Measurements</h3>"),
                widgets.HTML("<p style='margin: 0 0 8px 0;'>Define optional dropdown filters per row: Sample -> Type -> Spot size -> Cycle.</p>"),
                widgets.HTML("<p style='margin: 0 0 8px 0; color: #666;'>If no specific filter is selected, all loaded data is used.</p>"),
                widgets.HBox([self.add_filter_row_button, self.clear_filter_rows_button, self.apply_filters_button, self.auto_apply_toggle]),
                self.selection_rows_container,
            ]
        )

    def set_auto_apply_callback(self, callback):
        self._auto_apply_callback = callback

    def _trigger_auto_apply(self):
        if self._suspend_auto_apply:
            return
        if not self.auto_apply_toggle.value:
            return
        if self._auto_apply_callback is not None:
            self._auto_apply_callback()

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

    def _with_all_option(self, values):
        return [("All", "__all__")] + [(str(v), v) for v in values]

    def _add_selection_row(self, _):
        sample_options = self._with_all_option(self.filter_options.get("samples", []))
        sample_dd = widgets.Dropdown(options=sample_options, value="__all__", description="Sample", layout=widgets.Layout(width="320px"))
        type_dd = widgets.Dropdown(options=[("All", "__all__")], value="__all__", description="Type", layout=widgets.Layout(width="260px"))
        spot_dd = widgets.Dropdown(options=[("All", "__all__")], value="__all__", description="Spot", layout=widgets.Layout(width="240px"))
        cycle_dd = widgets.Dropdown(options=[("All", "__all__")], value="__all__", description="Cycle", layout=widgets.Layout(width="200px"))
        remove_btn = widgets.Button(description="Remove", button_style="danger", layout=widgets.Layout(width="90px"))

        row = {
            "sample": sample_dd,
            "type": type_dd,
            "spot": spot_dd,
            "cycle": cycle_dd,
            "remove": remove_btn,
        }

        sample_dd.observe(lambda _c, r=row: self._on_selection_row_changed(r, source="sample"), names="value")
        type_dd.observe(lambda _c, r=row: self._on_selection_row_changed(r, source="type"), names="value")
        spot_dd.observe(lambda _c, r=row: self._on_selection_row_changed(r, source="spot"), names="value")
        cycle_dd.observe(lambda _c: self._trigger_auto_apply(), names="value")

        def _remove(_btn):
            self.selection_rows = [x for x in self.selection_rows if x is not row]
            self._render_selection_rows()

        remove_btn.on_click(_remove)

        self.selection_rows.append(row)
        self._update_row_options(row, source="sample")
        self._render_selection_rows()
        self._trigger_auto_apply()

    def _clear_selection_rows(self, _):
        self.selection_rows = []
        self._render_selection_rows()
        self._trigger_auto_apply()

    def _on_selection_row_changed(self, row, source="sample"):
        self._update_row_options(row, source=source)
        self._trigger_auto_apply()

    def _render_selection_rows(self):
        boxes = []
        for row in self.selection_rows:
            boxes.append(widgets.HBox([row["sample"], row["type"], row["spot"], row["cycle"], row["remove"]]))
        self.selection_rows_container.children = tuple(boxes)

    def _update_row_options(self, row, source="sample"):
        rows = self._filter_rows
        if not rows:
            row["type"].options = [("All", "__all__")]
            row["spot"].options = [("All", "__all__")]
            row["cycle"].options = [("All", "__all__")]
            row["type"].value = "__all__"
            row["spot"].value = "__all__"
            row["cycle"].value = "__all__"
            return

        sample_val = row["sample"].value
        type_val = row["type"].value
        spot_val = row["spot"].value

        if sample_val != "__all__":
            rows_after_sample = [r for r in rows if r["sample_id"] == sample_val]
        else:
            rows_after_sample = rows

        type_values = sorted({r["measurement_type"] for r in rows_after_sample})
        type_options = self._with_all_option(type_values)
        row["type"].options = type_options
        row["type"].value = type_val if any(v == type_val for _, v in type_options) else "__all__"

        type_selected = row["type"].value
        if type_selected != "__all__":
            rows_after_type = [r for r in rows_after_sample if r["measurement_type"] == type_selected]
        else:
            rows_after_type = rows_after_sample

        spot_values = sorted({r["laser_spot_size"] for r in rows_after_type})
        spot_options = self._with_all_option(spot_values)
        row["spot"].options = spot_options
        row["spot"].value = spot_val if any(v == spot_val for _, v in spot_options) else "__all__"

        spot_selected = row["spot"].value
        if spot_selected != "__all__":
            rows_after_spot = [r for r in rows_after_type if r["laser_spot_size"] == spot_selected]
        else:
            rows_after_spot = rows_after_type

        cycle_values = sorted({r["cycle_number"] for r in rows_after_spot})
        cycle_options = self._with_all_option(cycle_values)
        current_cycle = row["cycle"].value
        row["cycle"].options = cycle_options
        row["cycle"].value = current_cycle if any(v == current_cycle for _, v in cycle_options) else "__all__"

    def _add_plot_row(self, _):
        kind = widgets.Dropdown(
            options=[
                "PL (only)",
                "PL + PL (sweep ~1 sun)",
                "Sweep",
                "LuQY vs Laser Intensity",
            ],
            value="PL (only)",
            description="Plot",
            layout=widgets.Layout(width="300px"),
        )
        opt_a = widgets.Dropdown(description="A", layout=widgets.Layout(width="240px"))
        opt_b = widgets.Dropdown(description="B", layout=widgets.Layout(width="240px"))
        opt_c = widgets.Dropdown(description="C", layout=widgets.Layout(width="240px"))
        include_sweep = widgets.Checkbox(value=True, description="Show nearest sweep (~1 sun)", indent=False, layout=widgets.Layout(width="260px"))
        legend_table = widgets.Checkbox(value=False, description="Legend as table below", indent=False, layout=widgets.Layout(width="220px"))
        fit_enabled = widgets.Checkbox(value=False, description="Linear fit", indent=False, layout=widgets.Layout(width="130px"))
        fit_min = widgets.Text(value="", description="Fit min", layout=widgets.Layout(width="170px"))
        fit_max = widgets.Text(value="", description="Fit max", layout=widgets.Layout(width="170px"))
        remove_btn = widgets.Button(description="Remove", button_style="danger", layout=widgets.Layout(width="100px"))

        row = {
            "kind": kind,
            "a": opt_a,
            "b": opt_b,
            "c": opt_c,
            "include_sweep": include_sweep,
            "legend_table": legend_table,
            "fit_enabled": fit_enabled,
            "fit_min": fit_min,
            "fit_max": fit_max,
            "remove": remove_btn,
        }

        def refresh_options(*_args):
            if kind.value in ["PL (only)", "PL + PL (sweep ~1 sun)"]:
                include_sweep.layout.display = "none"
                fit_enabled.layout.display = "none"
                fit_min.layout.display = "none"
                fit_max.layout.display = "none"
                opt_a.description = "Color by"
                opt_b.description = "Source"
                opt_c.description = "-"
                opt_a.options = [("Sample", "sample_id"), ("Condition", "condition"), ("Batch", "batch"), ("Spot size", "laser_spot_size")]
                opt_a.value = "sample_id"
                opt_b.options = [("Auto", "auto"), ("Flux density", "luminescence_flux_density"), ("Raw counts", "raw_spectrum_counts")]
                opt_c.options = [("-", "-")]
                opt_c.value = "-"
            elif kind.value == "Sweep":
                include_sweep.layout.display = "none"
                fit_enabled.layout.display = "none"
                fit_min.layout.display = "none"
                fit_max.layout.display = "none"
                opt_a.description = "Mode"
                opt_b.description = "Color by"
                opt_c.description = "Source"
                opt_a.options = [("Combined", "combined"), ("Separate substrates", "separate_substrates")]
                opt_a.value = "combined"
                opt_b.options = [("Sample", "sample_id"), ("Condition", "condition"), ("Batch", "batch"), ("Spot size", "laser_spot_size")]
                opt_b.value = "condition"
                opt_c.options = [("Auto", "auto"), ("Flux density", "luminescence_flux_density"), ("Raw counts", "raw_spectrum_counts")]
                opt_c.value = "raw_spectrum_counts"
            elif kind.value == "LuQY vs Laser Intensity":
                include_sweep.layout.display = "none"
                fit_enabled.layout.display = "flex"
                fit_min.layout.display = "flex"
                fit_max.layout.display = "flex"
                opt_a.description = "Mode"
                opt_b.description = "Color by"
                opt_c.description = "X scale"
                opt_a.options = [("Combined (all files)", "combined"), ("Per sample", "per_sample")]
                opt_a.value = "combined"
                opt_b.options = [("Sample", "sample_id"), ("Condition", "condition"), ("Batch", "batch"), ("Measurement type", "measurement_type")]
                opt_b.value = "sample_id"
                opt_c.options = [("Linear", "linear"), ("Log", "log")]
                opt_c.value = "linear"

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
            top_row = widgets.HBox(
                [
                    row["kind"],
                    row["a"],
                    row["b"],
                    row["c"],
                    row["remove"],
                ]
            )
            bottom_row = widgets.HBox(
                [
                    row["include_sweep"],
                    row["legend_table"],
                    row["fit_enabled"],
                    row["fit_min"],
                    row["fit_max"],
                ]
            )
            widget_rows.append(
                widgets.VBox(
                    [
                        top_row,
                        bottom_row,
                    ]
                )
            )
        self.plot_rows_container.children = tuple(widget_rows)

    def update_filter_options(self, options):
        self._suspend_auto_apply = True
        self.filter_options = options
        self._filter_rows = options.get("filter_rows", [])

        for row in self.selection_rows:
            sample_values = self.filter_options.get("samples", [])
            sample_options = self._with_all_option(sample_values)
            current_sample = row["sample"].value
            row["sample"].options = sample_options
            row["sample"].value = current_sample if any(v == current_sample for _, v in sample_options) else "__all__"
            self._update_row_options(row, source="sample")

        if not self.selection_rows:
            self._add_selection_row(None)

        for row in self.plot_rows:
            try:
                row["kind"].value = row["kind"].value
            except Exception:
                pass
        self._suspend_auto_apply = False

    def get_filter_config(self):
        row_filters = []
        for row in self.selection_rows:
            row_filters.append(
                {
                    "sample": row["sample"].value,
                    "measurement_type": row["type"].value,
                    "laser_spot_size": row["spot"].value,
                    "cycle": row["cycle"].value,
                }
            )

        return {
            "row_filters": row_filters,
        }

    def get_plot_specs(self):
        def _parse_optional_float(value):
            text = str(value).strip() if value is not None else ""
            if not text:
                return None
            try:
                return float(text)
            except Exception:
                return None

        specs = []
        for row in self.plot_rows:
            plot_type_value = row["kind"].value
            include_sweep_pl = plot_type_value == "PL + PL (sweep ~1 sun)"

            normalized_plot_type = plot_type_value
            if plot_type_value in ["PL (only)", "PL + PL (sweep ~1 sun)"]:
                normalized_plot_type = "PL"

            specs.append(
                {
                    "plot_type": normalized_plot_type,
                    "option_a": row["a"].value,
                    "option_b": row["b"].value,
                    "option_c": row["c"].value,
                    "include_sweep_pl": include_sweep_pl,
                    "plot_type_ui": plot_type_value,
                    "legend_table_below": bool(row["legend_table"].value),
                    "fit_enabled": bool(row["fit_enabled"].value),
                    "fit_min": _parse_optional_float(row["fit_min"].value),
                    "fit_max": _parse_optional_float(row["fit_max"].value),
                }
            )
        return specs

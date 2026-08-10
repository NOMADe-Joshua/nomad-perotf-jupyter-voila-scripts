"""
XRD Analysis Application Controller
Loads XRD diffractograms from the NOMAD API and provides interactive peak analysis.
"""
import os
import sys
import io
import base64
import zipfile
import traceback
import requests
import numpy as np
import pandas as pd
import ipywidgets as widgets
from IPython.display import display, clear_output, Javascript
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# ── Path setup ───────────────────────────────────────────────────────────────
_this_dir   = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_this_dir)
for _p in (_this_dir, _parent_dir):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from auth_ui import AuthenticationUI
from batch_selection import create_batch_selection
from fitting_engine import FittingEngine


# ── Auth manager ─────────────────────────────────────────────────────────────

class SimpleAuthManager:
    """Auth manager – mirrors the JV-Analysis pattern."""

    def __init__(self, base_url: str, api_endpoint: str):
        self.base_url    = base_url
        self.api_endpoint = api_endpoint
        self.url          = f"{base_url}{api_endpoint}"
        self.current_token     = None
        self.current_user_info = None
        self.api_client      = self  # compat shim expected by AuthenticationUI
        self.status_callback = None

    def set_status_callback(self, callback):
        self.status_callback = callback

    def _update_status(self, message, color=None):
        if self.status_callback:
            self.status_callback(message, color)

    def authenticate_with_credentials(self, username: str, password: str) -> str:
        if not username or not password:
            raise ValueError("Username and password are required.")
        resp = requests.get(
            f"{self.url}/auth/token",
            params=dict(username=username, password=password),
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        if "access_token" not in data:
            raise ValueError("Server did not return an access_token.")
        self.current_token = data["access_token"]
        return self.current_token

    def authenticate_with_token(self, token: str = None) -> str:
        if token is None:
            token = os.environ.get("NOMAD_CLIENT_ACCESS_TOKEN", "")
        self.current_token = token
        return self.current_token

    def verify_token(self) -> dict:
        if not self.current_token:
            raise ValueError("Not authenticated.")
        resp = requests.get(
            f"{self.url}/users/me",
            headers={"Authorization": f"Bearer {self.current_token}"},
            timeout=10,
        )
        resp.raise_for_status()
        self.current_user_info = resp.json()
        return self.current_user_info

    def is_authenticated(self) -> bool:
        return self.current_token is not None and self.current_user_info is not None

    def clear_authentication(self):
        self.current_token     = None
        self.current_user_info = None

    def get_user_display_name(self) -> str:
        if not self.current_user_info:
            return "Unknown"
        return self.current_user_info.get(
            "name", self.current_user_info.get("username", "Unknown")
        )


# ── XRD array extraction helper ──────────────────────────────────────────────

def _extract_xrd_arrays(archive_data: dict):
    """
    Robustly extract (two_theta, intensity) arrays from a NOMAD archive dict.
    Tries several common field-name patterns used in peroTF_XRD_XY entries.
    Returns (None, None) if nothing recognisable is found.
    """
    _ANGLE_KEYS = [
        "two_theta", "two_theta_array", "angle", "angles",
        "2theta", "x_values", "q_values", "two_theta_values",
    ]
    _INTENSITY_KEYS = [
        "intensity", "intensity_array", "counts", "i_values",
        "intensities", "y_values", "yobs", "count",
    ]

    def _to_1d(val):
        if val is None:
            return None
        try:
            arr = np.asarray(val, dtype=float).ravel()
            return arr if arr.size > 1 else None
        except Exception:
            return None

    def _search(d: dict):
        if not isinstance(d, dict):
            return None, None
        for ak in _ANGLE_KEYS:
            for ik in _INTENSITY_KEYS:
                a = _to_1d(d.get(ak))
                i = _to_1d(d.get(ik))
                if a is not None and i is not None and len(a) == len(i):
                    return a, i
        return None, None

    # 1. Top-level flat fields
    a, i = _search(archive_data)
    if a is not None:
        return a, i

    # 2. Nested under 'data'
    a, i = _search(archive_data.get("data", {}))
    if a is not None:
        return a, i

    # 3. Nested under 'diffractogram' (list or dict)
    diffr = archive_data.get("diffractogram")
    if isinstance(diffr, list) and diffr:
        diffr = diffr[0]
    if isinstance(diffr, dict):
        a, i = _search(diffr)
        if a is not None:
            return a, i

    return None, None


# ── Colour helpers ────────────────────────────────────────────────────────────

_COMPONENT_COLORS = [
    "rgba(44,160,44,0.75)",
    "rgba(214,39,40,0.75)",
    "rgba(148,103,189,0.75)",
    "rgba(140,86,75,0.75)",
    "rgba(227,119,194,0.75)",
    "rgba(127,127,127,0.75)",
    "rgba(188,189,34,0.75)",
    "rgba(23,190,207,0.75)",
]

_COLOR_MAP = {
    "Plotly":   px.colors.qualitative.Plotly,
    "Set1":     px.colors.qualitative.Set1,
    "Set2":     px.colors.qualitative.Set2,
    "Set3":     px.colors.qualitative.Set3,
    "Pastel":   px.colors.qualitative.Pastel,
    "Dark2":    px.colors.qualitative.Dark2,
    "Alphabet": px.colors.qualitative.Alphabet,
    "Viridis":  px.colors.sequential.Viridis[::-1],
    "Plasma":   px.colors.sequential.Plasma[::-1],
}


# ── Main application ──────────────────────────────────────────────────────────

class XRDAnalysisApp:
    """
    Interactive XRD analysis app for Voilà / JupyterLab.

    Tab 0  Login & Upload   – authenticate and load XRD data from NOMAD
    Tab 1  XRD Patterns     – overlay / compare diffractograms
    Tab 2  Peak Analysis    – detect peaks and fit Gaussian profiles
    Tab 3  Export           – download plot (HTML) or data (ZIP/CSV)
    """

    BASE_URL     = "http://elnserver.lti.kit.edu"
    API_ENDPOINT = "/nomad-oasis/api/v1"

    # ── init ─────────────────────────────────────────────────────────────────

    def __init__(self):
        self.auth_manager    = SimpleAuthManager(self.BASE_URL, self.API_ENDPOINT)
        self.fitting_engine  = FittingEngine()

        self.loaded_patterns: dict = {}   # label → {two_theta, intensity, …}
        self.selected_batch_ids: list = []
        self._last_overlay_fig = None
        self._detected_peaks: list = []
        self._peak_label  = ""
        self._peak_x      = None
        self._peak_y_norm = None

        self._build_ui()
        self._setup_callbacks()
        self._auto_authenticate()

    # ── widget construction ───────────────────────────────────────────────────

    def _build_ui(self):
        # -- auth (reuse parent component) ------------------------------------
        self.auth_ui = AuthenticationUI(self.auth_manager)

        # -- status / batch loading -------------------------------------------
        self.load_status = widgets.Output(
            layout=widgets.Layout(
                border="1px solid #e0e0e0", padding="10px",
                min_height="50px", margin="8px 0",
            )
        )
        self.batch_container = widgets.Output()

        # ── Tab 1 : XRD Patterns ─────────────────────────────────────────────
        self.pattern_selector = widgets.SelectMultiple(
            options=[],
            description="Patterns:",
            layout=widgets.Layout(width="420px", height="220px"),
            style={"description_width": "72px"},
        )
        self.select_all_btn   = widgets.Button(
            description="Select All",
            layout=widgets.Layout(width="110px"),
        )
        self.deselect_all_btn = widgets.Button(
            description="Deselect All",
            layout=widgets.Layout(width="110px"),
        )

        self.normalize_cb = widgets.Checkbox(
            value=True, description="Normalize (0–1)",
            indent=False, layout=widgets.Layout(width="170px"),
        )
        self.offset_cb    = widgets.Checkbox(
            value=True, description="Vertical offset",
            indent=False, layout=widgets.Layout(width="160px"),
        )
        self.offset_step  = widgets.BoundedFloatText(
            value=0.15, min=0.0, max=10.0, step=0.05,
            description="Step:",
            layout=widgets.Layout(width="140px"),
            style={"description_width": "44px"},
        )
        self.log_scale_cb = widgets.Checkbox(
            value=False, description="Log intensity",
            indent=False, layout=widgets.Layout(width="150px"),
        )
        self.color_dropdown = widgets.Dropdown(
            options=list(_COLOR_MAP.keys()),
            value="Plotly", description="Colors:",
            layout=widgets.Layout(width="220px"),
            style={"description_width": "60px"},
        )
        self.line_width_input = widgets.BoundedFloatText(
            value=1.5, min=0.5, max=6.0, step=0.5,
            description="Line width:",
            layout=widgets.Layout(width="185px"),
            style={"description_width": "90px"},
        )
        self.plot_btn = widgets.Button(
            description="📊  Plot Selected",
            button_style="success",
            layout=widgets.Layout(width="170px", height="38px"),
        )
        self.plot_output = widgets.Output(
            layout=widgets.Layout(
                border="1px solid #e0e0e0", padding="8px", margin="8px 0",
            )
        )

        # ── Tab 2 : Peak Analysis ─────────────────────────────────────────────
        self.ref_pattern_dropdown = widgets.Dropdown(
            options=[], description="Pattern:",
            layout=widgets.Layout(width="440px"),
            style={"description_width": "72px"},
        )
        self.prominence_input = widgets.BoundedFloatText(
            value=0.05, min=0.001, max=1.0, step=0.005,
            description="Prominence:",
            layout=widgets.Layout(width="190px"),
            style={"description_width": "100px"},
        )
        self.distance_input = widgets.BoundedIntText(
            value=5, min=1, max=500,
            description="Distance:",
            layout=widgets.Layout(width="165px"),
            style={"description_width": "80px"},
        )
        self.bg_model_dropdown = widgets.Dropdown(
            options=["None", "Linear", "Polynomial"],
            value="Linear", description="Background:",
            layout=widgets.Layout(width="215px"),
            style={"description_width": "90px"},
        )
        self.detect_btn = widgets.Button(
            description="🔍  Detect Peaks",
            button_style="primary",
            layout=widgets.Layout(width="155px", height="38px"),
        )
        self.fit_btn = widgets.Button(
            description="📈  Fit Peaks",
            button_style="warning",
            layout=widgets.Layout(width="145px", height="38px"),
            disabled=True,
        )
        self.peak_plot_output = widgets.Output(
            layout=widgets.Layout(
                border="1px solid #e0e0e0", padding="8px", margin="8px 0",
            )
        )
        self.peak_table_output = widgets.Output(
            layout=widgets.Layout(
                border="1px solid #e0e0e0", padding="8px", margin="8px 0",
                max_height="270px", overflow_y="auto",
            )
        )

        # ── Tab 3 : Export ────────────────────────────────────────────────────
        self.export_html_btn = widgets.Button(
            description="💾  Download Plot (HTML)",
            button_style="info",
            layout=widgets.Layout(width="215px"),
        )
        self.export_csv_btn = widgets.Button(
            description="📄  Download Data (ZIP)",
            button_style="info",
            layout=widgets.Layout(width="195px"),
        )
        self.export_output = widgets.Output(
            layout=widgets.Layout(
                border="1px solid #e0e0e0", padding="8px", margin="8px 0",
            )
        )

        self.tabs = widgets.Tab()
        self._assemble_tabs()

    # ── tab assembly ──────────────────────────────────────────────────────────

    def _assemble_tabs(self):
        # ── Tab 0 ─────────────────────────────────────────────────────────────
        tab0 = widgets.VBox([
            self.auth_ui.get_widget(),
            widgets.HTML("<h3 style='margin-top:20px;'>📁 Select Uploads</h3>"),
            widgets.HTML(
                "<p style='color:#555; margin:0 0 8px 0;'>"
                "Select one or more batches that contain XRD measurements "
                "(<code>peroTF_XRD_XY</code>). "
                "Click <b>Load</b> in the batch widget to fetch the data.</p>"
            ),
            self.batch_container,
            self.load_status,
        ])

        # ── Tab 1 ─────────────────────────────────────────────────────────────
        selector_box = widgets.VBox(
            [
                widgets.HTML("<b>Patterns</b>"),
                self.pattern_selector,
                widgets.HBox([self.select_all_btn, self.deselect_all_btn]),
            ],
            layout=widgets.Layout(margin="0 24px 0 0"),
        )
        options_box = widgets.VBox([
            widgets.HTML("<b>Plot options</b>"),
            self.normalize_cb,
            widgets.HBox([self.offset_cb, self.offset_step]),
            self.log_scale_cb,
            self.color_dropdown,
            self.line_width_input,
            widgets.HTML("&nbsp;"),
            self.plot_btn,
        ])
        tab1 = widgets.VBox([
            widgets.HTML("<h3>XRD Diffractograms</h3>"),
            widgets.HBox([selector_box, options_box]),
            widgets.HTML("<hr style='margin:12px 0;'>"),
            self.plot_output,
        ])

        # ── Tab 2 ─────────────────────────────────────────────────────────────
        tab2 = widgets.VBox([
            widgets.HTML("<h3>Peak Analysis</h3>"),
            widgets.HTML(
                "<p style='color:#555; margin:0 0 8px 0;'>"
                "Select a single pattern, detect peaks, then optionally fit "
                "Gaussian profiles to each peak.</p>"
            ),
            self.ref_pattern_dropdown,
            widgets.HTML("<hr style='margin:8px 0;'>"),
            widgets.HTML("<b>Detection parameters</b>"),
            widgets.HBox([
                self.prominence_input,
                self.distance_input,
                self.bg_model_dropdown,
            ]),
            widgets.HBox(
                [self.detect_btn, self.fit_btn],
                layout=widgets.Layout(margin="10px 0"),
            ),
            self.peak_plot_output,
            widgets.HTML("<b>Peak parameters</b>"),
            self.peak_table_output,
        ])

        # ── Tab 3 ─────────────────────────────────────────────────────────────
        tab3 = widgets.VBox([
            widgets.HTML("<h3>Export</h3>"),
            widgets.HTML(
                "<p style='color:#555; margin:0 0 8px 0;'>"
                "Download the current overlay plot as a self-contained HTML file, "
                "or export all loaded patterns as CSV files bundled in a ZIP archive.</p>"
            ),
            widgets.HBox(
                [self.export_html_btn, self.export_csv_btn],
                layout=widgets.Layout(margin="8px 0"),
            ),
            self.export_output,
        ])

        self.tabs.children = [tab0, tab1, tab2, tab3]
        for idx, title in enumerate(
            ["Login & Upload", "XRD Patterns", "Peak Analysis", "Export"]
        ):
            self.tabs.set_title(idx, title)

    # ── callbacks ─────────────────────────────────────────────────────────────

    def _setup_callbacks(self):
        self.auth_ui.set_success_callback(self._on_auth_success)
        self.select_all_btn.on_click(
            lambda _: setattr(
                self.pattern_selector, "value", self.pattern_selector.options
            )
        )
        self.deselect_all_btn.on_click(
            lambda _: setattr(self.pattern_selector, "value", ())
        )
        self.plot_btn.on_click(self._on_plot)
        self.detect_btn.on_click(self._on_detect_peaks)
        self.fit_btn.on_click(self._on_fit_peaks)
        self.export_html_btn.on_click(self._on_export_html)
        self.export_csv_btn.on_click(self._on_export_csv)

    def _auto_authenticate(self):
        is_hub = bool(os.environ.get("JUPYTERHUB_USER"))
        if is_hub:
            self.auth_ui.auth_method_selector.value = "Token (from ENV)"
            self.auth_ui.local_auth_box.layout.display = "none"
        else:
            self.auth_ui.auth_method_selector.value = "Username/Password"
            self.auth_ui.local_auth_box.layout.display = "flex"
        self.auth_ui._on_auth_button_clicked(None)

    # ── auth / data loading ───────────────────────────────────────────────────

    def _on_auth_success(self):
        self.tabs.selected_index = 0
        self._init_batch_selection()

    def _init_batch_selection(self):
        with self.batch_container:
            clear_output(wait=True)
            if not self.auth_manager.is_authenticated():
                return
            try:
                widget = create_batch_selection(
                    self.auth_manager.url,
                    self.auth_manager.current_token,
                    self._load_xrd_from_selection,
                )
                display(widget)
            except Exception as exc:
                print(f"⚠  Could not create batch selector: {exc}")

    def _load_xrd_from_selection(self, batch_selector):
        """Fetch XRD entries for all selected batches and populate the app."""
        from api_calls import get_ids_in_batch, get_all_xrd

        batch_ids = list(batch_selector.value) if batch_selector.value else []
        self.selected_batch_ids = batch_ids

        if not batch_ids:
            with self.load_status:
                clear_output(wait=True)
                print("Please select at least one batch.")
            return

        with self.load_status:
            clear_output(wait=True)
            print(f"⏳  Loading XRD data for {len(batch_ids)} batch(es)…")

        url   = self.auth_manager.url
        token = self.auth_manager.current_token

        try:
            # Collect sample IDs from all selected batches
            all_sample_ids: list = []
            failed_batches: list = []
            for bid in batch_ids:
                try:
                    ids = get_ids_in_batch(url, token, [bid])
                    all_sample_ids.extend(ids)
                except Exception as exc:
                    failed_batches.append(bid)
                    with self.load_status:
                        print(f"  ⚠  Batch {bid}: {exc}")

            if not all_sample_ids:
                with self.load_status:
                    clear_output(wait=True)
                    print("❌  No samples found in the selected batches.")
                return

            with self.load_status:
                print(
                    f"   Found {len(all_sample_ids)} sample(s). "
                    "Fetching XRD measurements…"
                )

            xrd_raw = get_all_xrd(url, token, all_sample_ids)

            # Parse and store patterns
            self.loaded_patterns = {}
            skipped = 0
            for lab_id, measurements in xrd_raw.items():
                for i, (archive_data, metadata) in enumerate(measurements):
                    two_theta, intensity = _extract_xrd_arrays(archive_data)
                    if two_theta is None:
                        skipped += 1
                        continue
                    suffix = f"_m{i + 1}" if len(measurements) > 1 else ""
                    label  = f"{lab_id}{suffix}"
                    upload = (
                        metadata.get("upload_name")
                        or metadata.get("upload_id", "?")
                    )[:50]
                    self.loaded_patterns[label] = {
                        "two_theta": two_theta,
                        "intensity": intensity,
                        "sample_id": lab_id,
                        "upload":    upload,
                        "mainfile":  metadata.get("mainfile", ""),
                    }

            n = len(self.loaded_patterns)
            with self.load_status:
                clear_output(wait=True)
                if n:
                    print(f"✅  Loaded {n} XRD pattern(s) from "
                          f"{len(xrd_raw)} sample(s).")
                    if skipped:
                        print(f"   ⚠  {skipped} entr(y/ies) skipped "
                              "(unrecognised data format).")
                    if failed_batches:
                        print(f"   ⚠  Failed batches: {failed_batches}")
                else:
                    print("❌  No XRD patterns could be extracted.")
                    print(
                        "   Verify that the selected batches contain "
                        "peroTF_XRD_XY entries with recognisable "
                        "two_theta / intensity fields."
                    )
                    if skipped:
                        print(f"   ({skipped} entries had unrecognised formats.)")
                    return

            labels = sorted(self.loaded_patterns.keys())
            self.pattern_selector.options = labels
            self.pattern_selector.value   = tuple(labels[: min(8, len(labels))])
            self.ref_pattern_dropdown.options = labels
            self.ref_pattern_dropdown.value   = labels[0] if labels else None
            self.tabs.selected_index = 1

        except Exception as exc:
            with self.load_status:
                clear_output(wait=True)
                print(f"❌  Error loading XRD data:\n{exc}")
                traceback.print_exc()

    # ── overlay plot ──────────────────────────────────────────────────────────

    def _color_palette(self, n: int) -> list:
        palette = _COLOR_MAP.get(self.color_dropdown.value,
                                  px.colors.qualitative.Plotly)
        if n <= len(palette):
            return list(palette[:n])
        return [palette[i % len(palette)] for i in range(n)]

    def _on_plot(self, _b=None):
        selected = list(self.pattern_selector.value)
        if not selected:
            with self.plot_output:
                clear_output(wait=True)
                print("No patterns selected.")
            return

        normalize  = self.normalize_cb.value
        use_offset = self.offset_cb.value
        step       = self.offset_step.value
        log_y      = self.log_scale_cb.value
        lw         = self.line_width_input.value
        colors     = self._color_palette(len(selected))

        fig = go.Figure()

        for idx, label in enumerate(selected):
            p = self.loaded_patterns[label]
            x = p["two_theta"]
            y = p["intensity"].astype(float)

            if normalize:
                ymax = y.max()
                if ymax > 0:
                    y = y / ymax

            if use_offset:
                y = y + idx * step

            fig.add_trace(go.Scatter(
                x=x, y=y,
                mode="lines",
                name=label,
                line=dict(color=colors[idx], width=lw),
                hovertemplate=(
                    f"<b>{label}</b><br>"
                    "2θ: %{x:.3f}°<br>"
                    "I: %{y:.4f}<extra></extra>"
                ),
            ))

        fig.update_layout(
            title=dict(text="XRD Diffractograms", font=dict(size=18)),
            xaxis_title="2θ (°)",
            yaxis_title="Normalised Intensity" if normalize else "Intensity (counts)",
            yaxis_type="log" if log_y else "linear",
            template="plotly_white",
            height=600,
            legend=dict(
                orientation="v",
                yanchor="top",  y=1.0,
                xanchor="left", x=1.01,
                bgcolor="rgba(255,255,255,0.92)",
                bordercolor="lightgray", borderwidth=1,
            ),
            margin=dict(l=70, r=30, t=70, b=60),
            hovermode="x unified",
        )
        fig.update_xaxes(showgrid=True, gridcolor="lightgray", gridwidth=1)
        fig.update_yaxes(showgrid=True, gridcolor="lightgray", gridwidth=1)

        self._last_overlay_fig = fig
        with self.plot_output:
            clear_output(wait=True)
            fig.show()

    # ── peak analysis ─────────────────────────────────────────────────────────

    def _on_detect_peaks(self, _b=None):
        label = self.ref_pattern_dropdown.value
        if not label or label not in self.loaded_patterns:
            with self.peak_plot_output:
                clear_output(wait=True)
                print("Please select a pattern from the dropdown.")
            return

        p = self.loaded_patterns[label]
        x = p["two_theta"]
        y = p["intensity"].astype(float)
        ymax = y.max()
        y_norm = y / ymax if ymax > 0 else y

        try:
            peaks = self.fitting_engine.detect_peaks(
                x, y_norm,
                prominence=self.prominence_input.value,
                distance=self.distance_input.value,
            )
            self._detected_peaks = peaks
            self._peak_label     = label
            self._peak_x         = x
            self._peak_y_norm    = y_norm

            self.fit_btn.disabled = len(peaks) == 0

            self._draw_peak_plot(label, x, y_norm, peaks)
            self._draw_peak_table(peaks)

            if not peaks:
                with self.peak_table_output:
                    print("No peaks found. Try lowering Prominence or Distance.")

        except Exception as exc:
            with self.peak_plot_output:
                clear_output(wait=True)
                print(f"Peak detection failed: {exc}")

    def _draw_peak_plot(self, label, x, y_norm, peaks, fit_result=None):
        """Render normalised pattern with peak markers and optional fit overlay."""
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=x, y=y_norm,
            mode="lines",
            name=label,
            line=dict(color="#1f77b4", width=2),
            hovertemplate="2θ: %{x:.3f}°<br>I: %{y:.4f}<extra></extra>",
        ))

        if fit_result is not None:
            fig.add_trace(go.Scatter(
                x=x, y=fit_result.best_fit,
                mode="lines", name="Total fit",
                line=dict(color="crimson", width=2.5, dash="dash"),
            ))
            if hasattr(fit_result, "eval_components"):
                for ci, (cname, cvals) in enumerate(
                    fit_result.eval_components().items()
                ):
                    if not cname.startswith("p"):
                        continue  # skip background components
                    fig.add_trace(go.Scatter(
                        x=x, y=cvals,
                        mode="lines",
                        name=cname,
                        line=dict(
                            color=_COMPONENT_COLORS[ci % len(_COMPONENT_COLORS)],
                            width=1.5, dash="dot",
                        ),
                    ))

        if peaks:
            pk_x   = [pk["center"] for pk in peaks]
            pk_y   = [pk["height"] + 0.04 for pk in peaks]
            pk_txt = [f"{pk['center']:.3f}°" for pk in peaks]
            fig.add_trace(go.Scatter(
                x=pk_x, y=pk_y,
                mode="markers+text",
                marker=dict(symbol="triangle-down", size=11, color="orangered"),
                text=pk_txt,
                textposition="top center",
                textfont=dict(size=9, color="orangered"),
                name="Detected peaks",
                hovertemplate="2θ = %{x:.3f}°<extra></extra>",
            ))

        fig.update_layout(
            title=f"Peak Analysis — {label}",
            xaxis_title="2θ (°)",
            yaxis_title="Normalised Intensity",
            template="plotly_white",
            height=520,
            legend=dict(
                orientation="v",
                yanchor="top",  y=1.0,
                xanchor="left", x=1.01,
                bgcolor="rgba(255,255,255,0.92)",
                bordercolor="lightgray", borderwidth=1,
            ),
            margin=dict(l=70, r=30, t=70, b=60),
            hovermode="x unified",
        )
        fig.update_xaxes(showgrid=True, gridcolor="lightgray")
        fig.update_yaxes(showgrid=True, gridcolor="lightgray")

        with self.peak_plot_output:
            clear_output(wait=True)
            fig.show()

    def _draw_peak_table(self, peaks, fit_result=None):
        """Print a tidy table of detected (and optionally fitted) peak parameters."""
        with self.peak_table_output:
            clear_output(wait=True)
            if not peaks:
                return

            rows = []
            for i, pk in enumerate(peaks):
                row = {
                    "Peak": i + 1,
                    "2θ detected (°)": f"{pk['center']:.4f}",
                    "Height (norm.)":  f"{pk['height']:.4f}",
                    "FWHM est. (°)":   f"{pk.get('sigma', 0) * 2.355:.4f}",
                }
                if fit_result is not None:
                    prefix = f"p{i}_"
                    c = fit_result.params.get(f"{prefix}center")
                    s = fit_result.params.get(f"{prefix}sigma")
                    a = fit_result.params.get(f"{prefix}amplitude")
                    row["2θ fitted (°)"]   = f"{c.value:.4f}" if c else "—"
                    row["FWHM fitted (°)"] = f"{abs(s.value) * 2.355:.4f}" if s else "—"
                    row["Amplitude"]       = f"{a.value:.5f}" if a else "—"
                rows.append(row)

            df = pd.DataFrame(rows)
            if fit_result is not None:
                r2 = getattr(fit_result, "rsquared", None)
                if r2 is not None:
                    print(f"Fit  R² = {r2:.6f}\n")

            print(df.to_string(index=False))

    def _on_fit_peaks(self, _b=None):
        if not self._detected_peaks:
            with self.peak_plot_output:
                clear_output(wait=True)
                print("Please detect peaks first.")
            return

        x      = self._peak_x
        y_norm = self._peak_y_norm
        label  = self._peak_label

        peak_models = [
            {
                "type":   "Gaussian",
                "center": float(pk["center"]),
                "height": float(pk["height"]),
                "sigma":  max(float(pk.get("sigma", 0.1)), 0.01),
                "gamma":  1.0,
            }
            for pk in self._detected_peaks
        ]

        try:
            self.fitting_engine.create_fit_parameters(
                peak_models,
                background_model=self.bg_model_dropdown.value,
                poly_degree=2,
            )
            result = self.fitting_engine.fit_current_spectrum(x, y_norm)
            self._draw_peak_plot(label, x, y_norm,
                                  self._detected_peaks, fit_result=result)
            self._draw_peak_table(self._detected_peaks, fit_result=result)

        except Exception as exc:
            with self.peak_plot_output:
                clear_output(wait=True)
                print(f"Fitting failed: {exc}")
                traceback.print_exc()

    # ── export ────────────────────────────────────────────────────────────────

    def _on_export_html(self, _b=None):
        if self._last_overlay_fig is None:
            with self.export_output:
                clear_output(wait=True)
                print("No overlay plot available. "
                      "Create a plot in the XRD Patterns tab first.")
            return

        html  = self._last_overlay_fig.to_html(include_plotlyjs="cdn",
                                                full_html=True)
        b64   = base64.b64encode(html.encode()).decode()
        ts    = datetime.now().strftime("%Y%m%d_%H%M%S")
        fname = f"XRD_overlay_{ts}.html"

        js = f"""
(function(){{
    var a = document.createElement('a');
    a.href = 'data:text/html;base64,{b64}';
    a.download = '{fname}';
    document.body.appendChild(a); a.click(); document.body.removeChild(a);
}})();"""
        with self.export_output:
            clear_output(wait=True)
            print(f"✅  Downloading {fname} …")
            display(Javascript(js))

    def _on_export_csv(self, _b=None):
        if not self.loaded_patterns:
            with self.export_output:
                clear_output(wait=True)
                print("No data loaded.")
            return

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for label, p in self.loaded_patterns.items():
                csv = pd.DataFrame({
                    "two_theta_deg": p["two_theta"],
                    "intensity":     p["intensity"],
                }).to_csv(index=False)
                safe = "".join(
                    c if c.isalnum() or c in "_-" else "_" for c in label
                )
                zf.writestr(f"{safe}.csv", csv)

        buf.seek(0)
        b64   = base64.b64encode(buf.read()).decode()
        ts    = datetime.now().strftime("%Y%m%d_%H%M%S")
        fname = f"XRD_data_{ts}.zip"

        js = f"""
(function(){{
    var b64 = '{b64}';
    var bs  = atob(b64);
    var arr = new Uint8Array(bs.length);
    for (var i = 0; i < bs.length; i++) arr[i] = bs.charCodeAt(i);
    var blob = new Blob([arr], {{type: 'application/zip'}});
    var url  = URL.createObjectURL(blob);
    var a    = document.createElement('a');
    a.href = url; a.download = '{fname}';
    document.body.appendChild(a); a.click();
    document.body.removeChild(a); URL.revokeObjectURL(url);
}})();"""
        with self.export_output:
            clear_output(wait=True)
            print(f"✅  Downloading {fname} "
                  f"({len(self.loaded_patterns)} pattern(s)) …")
            display(Javascript(js))

    # ── public API ────────────────────────────────────────────────────────────

    def get_dashboard(self) -> widgets.VBox:
        """Return the complete application widget ready for display()."""
        header = widgets.HTML("""
        <div style="
            background: linear-gradient(135deg, #1f3964 0%, #1B6B5E 100%);
            padding: 18px 26px; border-radius: 10px;
            margin-bottom: 16px; color: white;
        ">
          <h1 style="margin: 0 0 5px 0; font-size: 1.85em; font-weight: 700;">
            🔬 XRD Analysis Dashboard
          </h1>
          <p style="margin: 0; opacity: 0.85; font-size: 0.95em;">
            Load diffractograms from the NOMAD API &nbsp;·&nbsp;
            Overlay &amp; compare patterns &nbsp;·&nbsp;
            Peak detection &amp; Gaussian fitting &nbsp;·&nbsp;
            Export HTML / CSV
          </p>
        </div>
        """)
        return widgets.VBox(
            [header, self.tabs],
            layout=widgets.Layout(
                max_width="1200px", margin="0 auto", padding="15px"
            ),
        )

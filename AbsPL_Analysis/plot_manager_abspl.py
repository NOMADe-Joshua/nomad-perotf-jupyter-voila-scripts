"""
Plot manager for AbsPL analysis.
Creates multiple figure types from filtered spectral data.
"""

import math
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


class AbsPLPlotManager:
    def __init__(self):
        self.font_size_axis = 14
        self.font_size_title = 16
        self.font_size_legend = 10

    def set_font_sizes(self, axis_size=None, title_size=None, legend_size=None):
        if axis_size is not None:
            self.font_size_axis = int(axis_size)
        if title_size is not None:
            self.font_size_title = int(title_size)
        if legend_size is not None:
            self.font_size_legend = int(legend_size)

    def _apply_layout(self, fig, title, x_title, y_title):
        fig.update_layout(
            title=dict(text=title, font=dict(size=self.font_size_title)),
            xaxis_title=x_title,
            yaxis_title=y_title,
            template="plotly_white",
            legend=dict(font=dict(size=self.font_size_legend)),
            margin=dict(l=80, r=40, t=70, b=70),
            width=1400,
            height=850,
        )
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor="#eaecf0", tickfont=dict(size=self.font_size_axis))
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="#eaecf0", tickfont=dict(size=self.font_size_axis))
        return fig

    def _rgba_from_color(self, color, alpha=0.18):
        if isinstance(color, str) and color.startswith("rgb("):
            return color.replace("rgb(", "rgba(").replace(")", f",{alpha})")
        if isinstance(color, str) and color.startswith("#") and len(color) == 7:
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
            return f"rgba({r},{g},{b},{alpha})"
        return f"rgba(31,119,180,{alpha})"

    def spectra_overlay(self, df, color_by="condition", normalize=False, log_y=False, y_source="auto"):
        fig = go.Figure()
        if df is None or df.empty:
            return self._apply_layout(go.Figure(), "No data", "Wavelength (nm)", "Intensity")

        if color_by not in df.columns:
            color_by = "condition" if "condition" in df.columns else "sample"

        categories = df[color_by].fillna("Unknown").astype(str).unique().tolist()
        colors = px.colors.qualitative.Plotly
        color_map = {c: colors[i % len(colors)] for i, c in enumerate(categories)}

        for _, row in df.iterrows():
            x = row.get("wavelength", None)
            if y_source == "luminescence_flux_density":
                y = row.get("luminescence_flux_density", None)
            elif y_source == "raw_spectrum_counts":
                y = row.get("raw_spectrum_counts", None)
            else:
                y = row.get("y_data", None)
            if not isinstance(x, list) or not isinstance(y, list):
                continue
            if len(x) == 0 or len(y) == 0:
                continue
            n = min(len(x), len(y))
            x = np.asarray(x[:n], dtype=float)
            y = np.asarray(y[:n], dtype=float)
            mask = np.isfinite(x) & np.isfinite(y)
            x = x[mask]
            y = y[mask]
            if x.size == 0:
                continue

            if normalize:
                ymax = np.nanmax(y)
                if np.isfinite(ymax) and ymax > 0:
                    y = y / ymax

            if log_y:
                valid = y > 0
                x = x[valid]
                y = y[valid]
                if y.size == 0:
                    continue

            label = str(row.get(color_by, "Unknown"))
            sample = str(row.get("sample_id", "?"))
            cycle = row.get("cycle_number", "?")
            mtype = str(row.get("measurement_type", "unknown"))
            trace_name = f"{label} | S:{sample} | C:{cycle} | {mtype}"

            fig.add_trace(
                go.Scatter(
                    x=x.tolist(),
                    y=y.tolist(),
                    mode="lines",
                    line=dict(width=2, color=color_map.get(label, colors[0])),
                    name=trace_name,
                    legendgroup=label,
                    showlegend=True,
                )
            )

        y_title = "Normalized intensity" if normalize else "Intensity"
        fig = self._apply_layout(fig, "AbsPL Spectra Overlay", "Wavelength (nm)", y_title)
        if log_y:
            fig.update_yaxes(type="log", title="Intensity (log scale)")
        return fig

    def average_spectra(self, df, group_by="condition", y_source="auto"):
        fig = go.Figure()
        if df is None or df.empty:
            return self._apply_layout(go.Figure(), "No data", "Wavelength (nm)", "Intensity")

        if group_by not in df.columns:
            group_by = "condition" if "condition" in df.columns else "sample"

        colors = px.colors.qualitative.D3
        for idx, (group_name, gdf) in enumerate(df.groupby(group_by)):
            curves = []
            wavelength_ref = None
            for _, row in gdf.iterrows():
                x = row.get("wavelength", None)
                if y_source == "luminescence_flux_density":
                    y = row.get("luminescence_flux_density", None)
                elif y_source == "raw_spectrum_counts":
                    y = row.get("raw_spectrum_counts", None)
                else:
                    y = row.get("y_data", None)
                if not isinstance(x, list) or not isinstance(y, list):
                    continue
                n = min(len(x), len(y))
                if n < 5:
                    continue
                x = np.asarray(x[:n], dtype=float)
                y = np.asarray(y[:n], dtype=float)
                mask = np.isfinite(x) & np.isfinite(y)
                x = x[mask]
                y = y[mask]
                if x.size < 5:
                    continue
                if wavelength_ref is None:
                    wavelength_ref = x
                if wavelength_ref is not None and len(x) == len(wavelength_ref) and np.allclose(x, wavelength_ref):
                    curves.append(y)

            if wavelength_ref is None or not curves:
                continue

            arr = np.vstack(curves)
            y_mean = np.nanmean(arr, axis=0)
            y_std = np.nanstd(arr, axis=0)

            color = colors[idx % len(colors)]
            fig.add_trace(go.Scatter(x=wavelength_ref, y=y_mean, mode="lines", name=f"{group_name} (mean)", line=dict(color=color, width=3)))
            fig.add_trace(go.Scatter(
                x=np.concatenate([wavelength_ref, wavelength_ref[::-1]]),
                y=np.concatenate([y_mean - y_std, (y_mean + y_std)[::-1]]),
                fill="toself",
                fillcolor=self._rgba_from_color(color, 0.18),
                line=dict(color="rgba(0,0,0,0)"),
                hoverinfo="skip",
                showlegend=False,
                name=f"{group_name} std",
            ))

        return self._apply_layout(fig, "Average Spectra by Group", "Wavelength (nm)", "Intensity")

    def sweep_heatmap(self, df, sample=None, intensity_source="raw_spectrum_counts"):
        if df is None or df.empty:
            return self._apply_layout(go.Figure(), "No data", "Wavelength (nm)", "Cycle")

        sweep_df = df[df["measurement_type"] == "sweep"].copy()
        if sweep_df.empty:
            return self._apply_layout(go.Figure(), "No sweep data available", "Wavelength (nm)", "Cycle")

        if sample is None:
            sample = sweep_df["sample_id"].value_counts().index[0]

        s = sweep_df[sweep_df["sample_id"] == sample].sort_values("cycle_number")
        if s.empty:
            return self._apply_layout(go.Figure(), f"No sweep data for sample {sample}", "Wavelength (nm)", "Cycle")

        rows = []
        wavelengths = None
        cycle_labels = []
        for _, row in s.iterrows():
            x = row.get("wavelength")
            y = row.get(intensity_source, row.get("y_data"))
            if not isinstance(x, list) or not isinstance(y, list):
                continue
            n = min(len(x), len(y))
            if n < 5:
                continue
            x = np.asarray(x[:n], dtype=float)
            y = np.asarray(y[:n], dtype=float)
            mask = np.isfinite(x) & np.isfinite(y)
            x = x[mask]
            y = y[mask]
            if x.size < 5:
                continue
            if wavelengths is None:
                wavelengths = x
            if len(x) != len(wavelengths) or not np.allclose(x, wavelengths):
                continue
            rows.append(y)
            cycle_labels.append(int(row.get("cycle_number", len(cycle_labels) + 1)))

        if wavelengths is None or not rows:
            return self._apply_layout(go.Figure(), f"Could not build heatmap for sample {sample}", "Wavelength (nm)", "Cycle")

        z = np.vstack(rows)
        fig = go.Figure(data=go.Heatmap(x=wavelengths, y=cycle_labels, z=z, colorscale="Viridis", colorbar=dict(title="Intensity")))
        fig = self._apply_layout(fig, f"Sweep Heatmap - Sample {sample}", "Wavelength (nm)", "Cycle")
        return fig

    def scalar_boxplot(self, df, y_col="plqy", x_col="condition"):
        if df is None or df.empty or y_col not in df.columns:
            return self._apply_layout(go.Figure(), "No scalar data", x_col, y_col)
        data = df.copy()
        data[y_col] = pd.to_numeric(data[y_col], errors="coerce")
        data = data.dropna(subset=[y_col])
        if data.empty:
            return self._apply_layout(go.Figure(), f"No valid values in {y_col}", x_col, y_col)
        if x_col not in data.columns:
            x_col = "condition" if "condition" in data.columns else "sample"
        fig = px.box(data, x=x_col, y=y_col, color=x_col, points="all")
        return self._apply_layout(fig, f"{y_col} distribution by {x_col}", x_col, y_col)

    def scalar_scatter(self, df, x_col="laser_intensity_suns", y_col="plqy", color_col="condition"):
        if df is None or df.empty:
            return self._apply_layout(go.Figure(), "No scalar data", x_col, y_col)
        data = df.copy()
        for col in [x_col, y_col]:
            if col in data.columns:
                data[col] = pd.to_numeric(data[col], errors="coerce")
        if x_col not in data.columns or y_col not in data.columns:
            return self._apply_layout(go.Figure(), "Missing scalar columns", x_col, y_col)
        data = data.dropna(subset=[x_col, y_col])
        if data.empty:
            return self._apply_layout(go.Figure(), "No valid scalar pairs", x_col, y_col)
        if color_col not in data.columns:
            color_col = "condition" if "condition" in data.columns else None
        fig = px.scatter(data, x=x_col, y=y_col, color=color_col, hover_data=["sample_id", "cycle_number", "measurement_type"])
        fig.update_traces(mode="markers+lines")
        return self._apply_layout(fig, f"{y_col} vs {x_col}", x_col, y_col)

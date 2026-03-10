"""
Plot manager for EQE curves.
"""

import os
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import integrate as sp_integrate

# ---------------------------------------------------------------------------
# AM1.5G spectrum — loaded once, cached at module level
# File format: [empty], energy (eV), photon flux (photons/cm²/s/eV)
# ---------------------------------------------------------------------------
_AM15G_ENERGY = None   # eV, ascending
_AM15G_FLUX   = None   # photons/cm²/s/eV


def _get_am15g():
    global _AM15G_ENERGY, _AM15G_FLUX
    if _AM15G_ENERGY is None:
        _dir = os.path.dirname(os.path.realpath(__file__))
        _fpath = os.path.join(_dir, "AM15G.dat.txt")
        _df = pd.read_csv(_fpath, header=None)
        _AM15G_ENERGY = np.array(_df[_df.columns[1]], dtype=float)
        _AM15G_FLUX   = np.array(_df[_df.columns[2]], dtype=float)
    return _AM15G_ENERGY, _AM15G_FLUX


def _compute_cumulative_jsc_am15g(x_vals, eqe_vals, jsc_total, x_col):
    """
    Compute cumulative Jsc(λ) weighted by the AM1.5G photon flux.

    The curve grows from short wavelength (UV) to long wavelength (IR),
    ending at jsc_total. Returns (x_out, cum_mA) aligned with x_vals order.
    """
    q = 1.602e-19
    energy_AM15, flux_AM15_per_eV = _get_am15g()

    x_arr  = np.array(x_vals, dtype=float)
    eqe    = np.array(eqe_vals, dtype=float)

    # Convert to wavelength (nm) for integration
    if "energy" in x_col.lower():
        wl_nm = 1239.8 / x_arr   # eV → nm
    else:
        wl_nm = x_arr.copy()     # already nm

    # Sort by ascending wavelength (UV → IR)
    sort_idx = np.argsort(wl_nm)
    wl_sorted  = wl_nm[sort_idx]
    eqe_sorted = eqe[sort_idx]

    # Convert AM1.5G flux from per-eV to per-nm:
    #   Φ(λ) [/nm] = Φ(E) [/eV] × |dE/dλ| = Φ(E) × 1239.8 / λ²
    # energy_AM15 is ascending eV → wavelength is descending nm
    wl_am15      = 1239.8 / energy_AM15             # nm, descending
    flux_per_nm  = flux_AM15_per_eV * 1239.8 / wl_am15 ** 2  # photons/cm²/s/nm
    # Sort to ascending wavelength for np.interp
    order        = np.argsort(wl_am15)
    wl_am15_asc  = wl_am15[order]
    flux_nm_asc  = flux_per_nm[order]

    # Interpolate AM1.5G to EQE wavelength grid
    flux_interp = np.interp(wl_sorted, wl_am15_asc, flux_nm_asc, left=0.0, right=0.0)

    # Cumulative trapezoid: ∫₀^λ EQE(λ') Φ(λ') dλ'  [photons/cm²/s]
    # × q [C] × 1e3 → mA/cm²
    integrand = eqe_sorted * flux_interp
    cum_raw   = sp_integrate.cumulative_trapezoid(integrand, wl_sorted, initial=0.0)
    cum_mA    = cum_raw * q * 1e3   # mA/cm²

    # Scale so the curve ends exactly at jsc_total
    if cum_mA[-1] > 0:
        cum_mA = cum_mA * (jsc_total / cum_mA[-1])

    # Restore original order (matching x_vals)
    inv_idx = np.empty_like(sort_idx)
    inv_idx[sort_idx] = np.arange(len(sort_idx))
    cum_out = cum_mA[inv_idx]

    return x_arr, cum_out


def _compute_group_stats(x_grid, curves_interp, stats_mode):
    df = pd.DataFrame(curves_interp)
    if stats_mode == "mean_std":
        center = df.mean(axis=0)
        low = center - df.std(axis=0)
        high = center + df.std(axis=0)
    else:
        center = df.median(axis=0)
        low = df.quantile(0.25, axis=0, interpolation="linear")
        high = df.quantile(0.75, axis=0, interpolation="linear")

    return pd.DataFrame({"x": x_grid, "center": center.values, "low": low.values, "high": high.values})


_ANNOTATION_FMT = {
    "bandgap_eqe":      ("{:.2f}", "eV"),
    "integrated_jsc":   ("{:.1f}", "mA/cm²"),
    "integrated_j0rad": ("{:.2e}", "mA/cm²"),
    "voc_rad":          ("{:.3f}", "V"),
    "urbach_energy":    ("{:.1f}", "meV"),
}


def _format_ann_val(col, val, unit, scale):
    if pd.isna(val):
        return None
    v = float(val) * scale
    fmt = _ANNOTATION_FMT.get(col, ("{:.3g}", ""))[0]
    return f"{fmt.format(v)}{(' ' + unit) if unit else ''}"


def _build_legend_annotation(params_rows, annotate_cols):
    """Return a legend suffix like '<br>Eg: 1.23 eV, Jsc: 20.1 mA/cm\u00b2' computed from mean column values."""
    if not annotate_cols or params_rows is None or params_rows.empty:
        return ""
    parts = []
    for col, abbr, unit, scale in annotate_cols:
        if col not in params_rows.columns:
            continue
        vals = pd.to_numeric(params_rows[col], errors="coerce").dropna()
        if vals.empty:
            continue
        s = _format_ann_val(col, vals.mean(), unit, scale)
        if s is not None:
            parts.append(f"{abbr}: {s}")
    return ("<br>" + ", ".join(parts)) if parts else ""


def create_eqe_figure(
    curves_df,
    params_df,
    x_mode="wavelength",
    group_curves=True,
    stats_mode="median_iqr",
    colors=None,
    font_size_axis=12,
    font_size_legend=10,
    line_width=2.0,
    annotate_cols=None,
    show_eg_vline=False,
    vline_width=1.5,
    show_jsc_cumulative=False,
):
    """Create an EQE plotly figure from filtered curve and parameter tables."""
    if curves_df is None or curves_df.empty:
        return None

    x_col = "wavelength_array" if x_mode == "wavelength" else "photon_energy_array"
    x_title = "Wavelength (nm)" if x_mode == "wavelength" else "Photon Energy (eV)"

    merged = curves_df.merge(
        params_df[["sample_id", "entry_idx", "measurement_idx", "plot_group"]],
        on=["sample_id", "entry_idx", "measurement_idx"],
        how="left",
    )

    fig = make_subplots(specs=[[{"secondary_y": True}]]) if show_jsc_cumulative else go.Figure()
    cum_jsc_traces = []  # (x_vals, y_vals, color, group_name) for secondary y-axis
    color_list = colors or [
        "rgba(93,164,214,0.9)",
        "rgba(255,144,14,0.9)",
        "rgba(44,160,101,0.9)",
        "rgba(255,65,54,0.9)",
        "rgba(79,90,117,0.9)",
    ]

    def pick_color(idx):
        return color_list[idx % len(color_list)]

    if group_curves:
        for idx, (group_name, gdf) in enumerate(merged.groupby("plot_group", dropna=False)):
            curve_list = []  # [(key_tuple, curve_df), ...]
            for (sid, eidx, midx), cdf in gdf.groupby(["sample_id", "entry_idx", "measurement_idx"]):
                cdf = cdf.dropna(subset=[x_col, "eqe_array"]).sort_values(x_col)
                if cdf.empty:
                    continue
                curve_list.append(((sid, eidx, midx), cdf[[x_col, "eqe_array"]]))

            if not curve_list:
                continue

            color = pick_color(idx)

            # Gather params rows for this group to build annotation string
            group_keys = pd.DataFrame(
                [{"sample_id": k[0], "entry_idx": k[1], "measurement_idx": k[2]} for k, _ in curve_list]
            )
            group_params = params_df.merge(group_keys, on=["sample_id", "entry_idx", "measurement_idx"], how="inner")

            if stats_mode == "best":
                best_key, best_curve = max(curve_list, key=lambda t: t[1]["eqe_array"].max())
                best_params = group_params[
                    (group_params["sample_id"] == best_key[0]) &
                    (group_params["entry_idx"] == best_key[1]) &
                    (group_params["measurement_idx"] == best_key[2])
                ]
                ann = _build_legend_annotation(best_params, annotate_cols)
                fig.add_scatter(
                    x=best_curve[x_col],
                    y=best_curve["eqe_array"],
                    mode="lines",
                    name=str(group_name) + ann,
                    legendgroup=str(group_name),
                    line=dict(color=color, width=float(line_width)),
                )
                # Cumulative Jsc (AM1.5G weighted)
                if show_jsc_cumulative:
                    jsc_ser = pd.to_numeric(best_params.get("integrated_jsc", pd.Series(dtype=float)), errors="coerce").dropna()
                    if not jsc_ser.empty:
                        bc = best_curve.sort_values(x_col).dropna(subset=["eqe_array"])
                        x_out, cum = _compute_cumulative_jsc_am15g(
                            bc[x_col].values, bc["eqe_array"].values,
                            float(jsc_ser.mean()), x_col
                        )
                        cum_jsc_traces.append((x_out, cum, color, str(group_name)))
                continue

            curves_only = [c for _, c in curve_list]
            min_x = max(c.iloc[:, 0].min() for c in curves_only)
            max_x = min(c.iloc[:, 0].max() for c in curves_only)
            if not np.isfinite(min_x) or not np.isfinite(max_x) or min_x >= max_x:
                continue

            x_grid = np.linspace(min_x, max_x, 500)
            interpolated = []
            for _, curve in curve_list:
                interpolated.append(np.interp(x_grid, curve.iloc[:, 0], curve.iloc[:, 1], left=np.nan, right=np.nan))

            stats_df = _compute_group_stats(x_grid, interpolated, stats_mode)
            rgba_fill = color.replace("0.9", "0.2") if "0.9" in color else "rgba(93,164,214,0.2)"
            ann = _build_legend_annotation(group_params, annotate_cols)
            legend_name = str(group_name) + ann

            fig.add_scatter(
                x=np.concatenate([stats_df["x"].values, stats_df["x"].values[::-1]]),
                y=np.concatenate([stats_df["high"].values, stats_df["low"].values[::-1]]),
                mode="lines",
                line=dict(color="rgba(255,255,255,0)", width=0),
                fill="toself",
                fillcolor=rgba_fill,
                showlegend=False,
                legendgroup=str(group_name),
                name=legend_name,
            )

            fig.add_scatter(
                x=stats_df["x"],
                y=stats_df["center"],
                mode="lines",
                name=legend_name,
                legendgroup=str(group_name),
                line=dict(color=color, width=float(line_width)),
            )
            # Cumulative Jsc (AM1.5G weighted, averaged over group curves)
            if show_jsc_cumulative:
                jsc_ser = pd.to_numeric(group_params.get("integrated_jsc", pd.Series(dtype=float)), errors="coerce").dropna()
                if not jsc_ser.empty and len(interpolated) > 0:
                    jsc_mean = float(jsc_ser.mean())
                    cum_list = []
                    for y_interp in interpolated:
                        y_v = np.where(np.isfinite(y_interp), y_interp, 0.0)
                        _, c = _compute_cumulative_jsc_am15g(x_grid, y_v, jsc_mean, x_col)
                        cum_list.append(c)
                    if cum_list:
                        mean_cum = np.mean(cum_list, axis=0)
                        cum_jsc_traces.append((x_grid, mean_cum, color, str(group_name)))
    else:
        for idx, ((sample_id, entry_idx, measurement_idx), cdf) in enumerate(
            merged.groupby(["sample_id", "entry_idx", "measurement_idx"])
        ):
            cdf = cdf.dropna(subset=[x_col, "eqe_array"]).sort_values(x_col)
            if cdf.empty:
                continue
            plot_group = cdf["plot_group"].iloc[0] if "plot_group" in cdf.columns else sample_id
            ind_params = params_df[
                (params_df["sample_id"] == sample_id) &
                (params_df["entry_idx"] == entry_idx) &
                (params_df["measurement_idx"] == measurement_idx)
            ]
            ann = _build_legend_annotation(ind_params, annotate_cols)
            fig.add_scatter(
                x=cdf[x_col],
                y=cdf["eqe_array"],
                mode="lines",
                name=str(plot_group) + ann,
                line=dict(color=pick_color(idx), width=float(line_width)),
            )
            # Cumulative Jsc (AM1.5G weighted)
            if show_jsc_cumulative:
                jsc_ser = pd.to_numeric(ind_params.get("integrated_jsc", pd.Series(dtype=float)), errors="coerce").dropna()
                if not jsc_ser.empty:
                    x_out, cum = _compute_cumulative_jsc_am15g(
                        cdf[x_col].values, cdf["eqe_array"].values,
                        float(jsc_ser.mean()), x_col
                    )
                    cum_jsc_traces.append((x_out, cum, pick_color(idx), str(plot_group)))

    # --- Cumulative Jsc traces (secondary y-axis) ---
    if show_jsc_cumulative and cum_jsc_traces:
        for x_c, y_c, col_c, _ in cum_jsc_traces:
            fig.add_trace(go.Scatter(
                x=x_c,
                y=y_c,
                mode="lines",
                line=dict(color=col_c, width=float(line_width), dash="dot"),
                showlegend=False,
                yaxis="y2",
            ))

    # --- Eg vertical lines ---
    if show_eg_vline and "bandgap_eqe" in params_df.columns:
        # Collect (group_name → color_idx) mapping from what was already plotted
        group_color_map = {
            gn: i for i, (gn, _) in enumerate(merged.groupby("plot_group", dropna=False))
        } if group_curves else {}

        if group_curves:
            for group_name, gdf in merged.groupby("plot_group", dropna=False):
                keys = gdf[["sample_id", "entry_idx", "measurement_idx"]].drop_duplicates()
                gp = params_df.merge(keys, on=["sample_id", "entry_idx", "measurement_idx"], how="inner")
                if "bandgap_eqe" not in gp.columns:
                    continue
                eg_vals = pd.to_numeric(gp["bandgap_eqe"], errors="coerce").dropna()
                if eg_vals.empty:
                    continue
                eg_ev = float(eg_vals.mean())
                x_val = eg_ev if x_mode == "photon_energy" else 1239.8 / eg_ev
                color = pick_color(group_color_map.get(group_name, 0))
                fig.add_vline(
                    x=x_val,
                    line=dict(color=color, width=float(vline_width), dash="dash"),
                    showlegend=False,
                )
        else:
            for idx, ((sample_id, entry_idx, measurement_idx), cdf) in enumerate(
                merged.groupby(["sample_id", "entry_idx", "measurement_idx"])
            ):
                ind_params = params_df[
                    (params_df["sample_id"] == sample_id) &
                    (params_df["entry_idx"] == entry_idx) &
                    (params_df["measurement_idx"] == measurement_idx)
                ]
                if "bandgap_eqe" not in ind_params.columns:
                    continue
                eg_vals = pd.to_numeric(ind_params["bandgap_eqe"], errors="coerce").dropna()
                if eg_vals.empty:
                    continue
                eg_ev = float(eg_vals.mean())
                x_val = eg_ev if x_mode == "photon_energy" else 1239.8 / eg_ev
                fig.add_vline(
                    x=x_val,
                    line=dict(color=pick_color(idx), width=float(vline_width), dash="dash"),
                    showlegend=False,
                )

    fig.update_layout(
        template="plotly_white",
        xaxis_title=x_title,
        yaxis_title="External Quantum Efficiency",
        legend=dict(
            font=dict(size=font_size_legend),
            x=0.01,
            y=0.99,
            xanchor="left",
            yanchor="top",
            bgcolor="rgba(255,255,255,0.7)",
            bordercolor="rgba(0,0,0,0.15)",
            borderwidth=1,
        ),
    )
    fig.update_xaxes(titlefont=dict(size=font_size_axis), tickfont=dict(size=font_size_axis))
    if show_jsc_cumulative:
        fig.update_yaxes(titlefont=dict(size=font_size_axis), tickfont=dict(size=font_size_axis),
                         rangemode="tozero", secondary_y=False)
    else:
        fig.update_yaxes(titlefont=dict(size=font_size_axis), tickfont=dict(size=font_size_axis))
    if show_jsc_cumulative and cum_jsc_traces:
        fig.update_layout(
            yaxis2=dict(
                title="J<sub>sc</sub> (mA/cm\u00b2)",
                overlaying="y",
                side="right",
                showgrid=False,
                titlefont=dict(size=font_size_axis),
                tickfont=dict(size=font_size_axis),
                rangemode="tozero",
            )
        )

    return fig

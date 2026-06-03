"""
Data manager for AbsPL/PLQY analysis.
"""

import os
import sys
import pandas as pd

parent_dir = os.path.dirname(os.getcwd())
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from api_calls import get_ids_in_batch, get_sample_description, get_all_eqe
from diagnostic_helper_abspl import debug_logger_abspl


class AbsPLDataManager:
    """Load, classify (PL vs sweep), and filter AbsPL data."""

    def __init__(self, auth_manager):
        self.auth_manager = auth_manager
        self.data = {
            "summary": pd.DataFrame(),
            "spectra": pd.DataFrame(),
            "filtered_summary": pd.DataFrame(),
            "filtered_spectra": pd.DataFrame(),
        }

    def _as_list(self, value):
        if value is None:
            return []
        if isinstance(value, list):
            return value
        return []

    def _safe_float(self, value):
        try:
            if value is None:
                return None
            return float(value)
        except Exception:
            return None

    def _detect_measurement_type(self, results):
        # Rule from sweep_vs_PL.md:
        # - len(results) > 1 likely sweep
        # - single result with missing luminescence_flux_density treated as sweep fallback
        if len(results) > 1:
            return "sweep"
        if len(results) == 1:
            first = results[0]
            flux = first.get("luminescence_flux_density")
            raw = first.get("raw_spectrum_counts")
            if flux is None and raw is not None:
                return "sweep"
        return "pl"

    def _extract_spot_size(self, data_dict):
        settings = data_dict.get("settings", {}) if isinstance(data_dict, dict) else {}
        candidates = [
            settings.get("laser_spot_size"),
            data_dict.get("laser_spot_size") if isinstance(data_dict, dict) else None,
            settings.get("spot_size"),
            data_dict.get("spot_size") if isinstance(data_dict, dict) else None,
        ]
        for c in candidates:
            if c not in (None, "", "nan"):
                return str(c)
        return "Unknown"

    def load_batch_data(self, batch_ids):
        self.data = {
            "summary": pd.DataFrame(),
            "spectra": pd.DataFrame(),
            "filtered_summary": pd.DataFrame(),
            "filtered_spectra": pd.DataFrame(),
        }

        if not self.auth_manager.is_authenticated():
            raise RuntimeError("Not authenticated")

        if not batch_ids:
            raise ValueError("No batch selected")

        url = self.auth_manager.url
        token = self.auth_manager.current_token

        debug_logger_abspl.add("LOAD", f"Start loading {len(batch_ids)} batch(es)", level="INFO")

        sample_ids = get_ids_in_batch(url, token, batch_ids)
        if not sample_ids:
            debug_logger_abspl.add("LOAD", "No sample IDs found in selected batches", level="WARNING")
            return False

        descriptions = get_sample_description(url, token, list(sample_ids))
        abspl_entries = get_all_eqe(url, token, sample_ids, eqe_type="peroTF_AbsPLMeasurement")

        summary_rows = []
        spectra_rows = []

        for sample_id, entries in abspl_entries.items():
            sample_desc = descriptions.get(sample_id, "")
            for entry_idx, (data_dict, metadata) in enumerate(entries):
                results = data_dict.get("results", []) if isinstance(data_dict, dict) else []
                if not isinstance(results, list):
                    continue

                measurement_type = self._detect_measurement_type(results)
                entry_name = data_dict.get("name", metadata.get("entry_name", f"entry_{entry_idx}"))
                upload_name = metadata.get("upload_name", "unknown_upload")
                spot_size = self._extract_spot_size(data_dict)

                settings = data_dict.get("settings", {}) if isinstance(data_dict, dict) else {}
                laser_intensity_default = settings.get("laser_intensity_suns", None)

                for i, result in enumerate(results):
                    cycle_number = result.get("cycle_number", i + 1)
                    wavelength = self._as_list(result.get("wavelength"))
                    lum_flux = self._as_list(result.get("luminescence_flux_density"))
                    raw_spec = self._as_list(result.get("raw_spectrum_counts"))
                    intensity = lum_flux if len(lum_flux) > 0 else raw_spec
                    y_source = "luminescence_flux_density" if len(lum_flux) > 0 else "raw_spectrum_counts"

                    if len(wavelength) == 0 or len(intensity) == 0:
                        continue

                    measurement_uid = f"{sample_id}|{metadata.get('entry_id', entry_idx)}|{cycle_number}"
                    cycle_int = int(cycle_number) if str(cycle_number).isdigit() else cycle_number

                    summary_rows.append(
                        {
                            "measurement_uid": measurement_uid,
                            "sample_id": sample_id,
                            "sample_description": sample_desc,
                            "batch": upload_name,
                            "condition": sample_desc if sample_desc else sample_id,
                            "entry_name": entry_name,
                            "measurement_type": measurement_type,
                            "cycle_number": cycle_int,
                            "laser_spot_size": spot_size,
                            "laser_intensity_suns": self._safe_float(result.get("laser_intensity_suns", laser_intensity_default)),
                            "luminescence_quantum_yield": self._safe_float(result.get("luminescence_quantum_yield")),
                            "quasi_fermi_level_splitting": self._safe_float(result.get("quasi_fermi_level_splitting")),
                            "quasi_fermi_level_splitting_het": self._safe_float(result.get("quasi_fermi_level_splitting_het")),
                            "i_voc": self._safe_float(result.get("i_voc")),
                            "bandgap": self._safe_float(result.get("bandgap")),
                            "derived_jsc": self._safe_float(result.get("derived_jsc")),
                            "spectrum_points": min(len(wavelength), len(intensity)),
                            "spectrum_source": y_source,
                        }
                    )

                    spectra_rows.append(
                        {
                            "measurement_uid": measurement_uid,
                            "sample_id": sample_id,
                            "condition": sample_desc if sample_desc else sample_id,
                            "batch": upload_name,
                            "entry_name": entry_name,
                            "measurement_type": measurement_type,
                            "cycle_number": cycle_int,
                            "laser_spot_size": spot_size,
                            "laser_intensity_suns": self._safe_float(result.get("laser_intensity_suns", laser_intensity_default)),
                            "wavelength": wavelength,
                            "luminescence_flux_density": lum_flux,
                            "raw_spectrum_counts": raw_spec,
                            "intensity": intensity,
                            "spectrum_source": y_source,
                        }
                    )

        summary_df = pd.DataFrame(summary_rows)
        spectra_df = pd.DataFrame(spectra_rows)

        if summary_df.empty or spectra_df.empty:
            debug_logger_abspl.add("LOAD", "No AbsPL results found for selected batches", level="WARNING")
            return False

        self.data["summary"] = summary_df
        self.data["spectra"] = spectra_df
        self.data["filtered_summary"] = summary_df.copy()
        self.data["filtered_spectra"] = spectra_df.copy()

        n_pl = int((summary_df["measurement_type"] == "pl").sum())
        n_sweep = int((summary_df["measurement_type"] == "sweep").sum())
        debug_logger_abspl.add(
            "LOAD",
            f"Loaded {len(summary_df)} measurements ({n_pl} PL, {n_sweep} Sweep) from {summary_df['sample_id'].nunique()} samples",
            level="SUCCESS",
        )
        return True

    def apply_filters(self, filter_config):
        summary_df = self.data.get("summary", pd.DataFrame()).copy()
        spectra_df = self.data.get("spectra", pd.DataFrame()).copy()

        if summary_df.empty:
            self.data["filtered_summary"] = pd.DataFrame()
            self.data["filtered_spectra"] = pd.DataFrame()
            return pd.DataFrame(), pd.DataFrame()

        measurement_types = filter_config.get("measurement_types", [])
        sample_ids = filter_config.get("samples", [])
        spot_sizes = filter_config.get("laser_spot_sizes", [])
        cycle_mode = filter_config.get("cycle_mode", "all")
        specific_cycles = filter_config.get("specific_cycles", [])
        numeric_filters = filter_config.get("numeric_filters", [])

        if measurement_types:
            summary_df = summary_df[summary_df["measurement_type"].isin(measurement_types)]

        if sample_ids:
            summary_df = summary_df[summary_df["sample_id"].isin(sample_ids)]

        if spot_sizes:
            summary_df = summary_df[summary_df["laser_spot_size"].isin(spot_sizes)]

        if cycle_mode == "first":
            summary_df = summary_df.sort_values(["sample_id", "cycle_number"]).groupby("sample_id").head(1)
        elif cycle_mode == "last":
            summary_df = summary_df.sort_values(["sample_id", "cycle_number"]).groupby("sample_id").tail(1)
        elif cycle_mode == "specific" and specific_cycles:
            summary_df = summary_df[summary_df["cycle_number"].isin(specific_cycles)]

        operators = {
            ">": lambda s, v: s > v,
            ">=": lambda s, v: s >= v,
            "<": lambda s, v: s < v,
            "<=": lambda s, v: s <= v,
            "==": lambda s, v: s == v,
            "!=": lambda s, v: s != v,
        }

        for column, op, raw in numeric_filters:
            if column not in summary_df.columns or op not in operators:
                continue
            series = pd.to_numeric(summary_df[column], errors="coerce")
            threshold = float(raw)
            summary_df = summary_df[operators[op](series, threshold).fillna(False)]

        allowed = set(summary_df["measurement_uid"].tolist())
        spectra_df = spectra_df[spectra_df["measurement_uid"].isin(allowed)].copy()

        self.data["filtered_summary"] = summary_df
        self.data["filtered_spectra"] = spectra_df

        debug_logger_abspl.add(
            "FILTER",
            f"Filtered to {len(summary_df)} measurements ({summary_df['sample_id'].nunique() if not summary_df.empty else 0} samples)",
            level="SUCCESS" if len(summary_df) else "WARNING",
        )
        return summary_df, spectra_df

    def get_data(self):
        return self.data

    def get_filtered_data(self):
        return self.data.get("filtered_summary", pd.DataFrame()), self.data.get("filtered_spectra", pd.DataFrame())

    def get_filter_options(self):
        summary = self.data.get("summary", pd.DataFrame())
        if summary.empty:
            return {
                "measurement_types": [],
                "samples": [],
                "laser_spot_sizes": [],
                "numeric_columns": [],
            }

        numeric_columns = [
            c
            for c in [
                "luminescence_quantum_yield",
                "quasi_fermi_level_splitting",
                "quasi_fermi_level_splitting_het",
                "i_voc",
                "bandgap",
                "derived_jsc",
                "laser_intensity_suns",
                "cycle_number",
            ]
            if c in summary.columns
        ]

        return {
            "measurement_types": sorted(summary["measurement_type"].dropna().astype(str).unique().tolist()),
            "samples": sorted(summary["sample_id"].dropna().astype(str).unique().tolist()),
            "laser_spot_sizes": sorted(summary["laser_spot_size"].dropna().astype(str).unique().tolist()),
            "numeric_columns": numeric_columns,
        }

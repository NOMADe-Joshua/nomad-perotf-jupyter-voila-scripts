"""
Diagnostic helpers for EQE loading and parsing.
"""

import ipywidgets as widgets
from IPython.display import clear_output


def diagnose_eqe_loading(data_manager):
    """Print a detailed diagnostic report for EQE loading/parsing state."""
    print("=" * 70)
    print("EQE LOADING DIAGNOSTIC")
    print("=" * 70)

    diag = getattr(data_manager, "last_diagnostics", {}) or {}
    if not diag:
        print("No diagnostic snapshot available yet. Load a batch first.")
        return

    # --- Basic counts ---
    for key in ["batch_count", "api_source", "sample_ids_total", "sample_ids_unique"]:
        if key in diag:
            print(f"{key}: {diag[key]}")

    if diag.get("sample_ids_preview"):
        print("sample_ids_preview:")
        for sid in diag["sample_ids_preview"]:
            print(f"  - {sid}")

    # --- Strategy results ---
    print("\n--- API Search Strategies ---")
    print(f"Strategy 1 (entry_references):")
    print(f"  default EQE type : {diag.get('strategy1_default_samples', '?')} samples found")
    print(f"  GammaBox EQE type: {diag.get('strategy1_gamma_samples', '?')} samples found")

    print(f"Strategy 2 (results.eln.lab_ids + entry_type):")
    for etype, status in (diag.get("strategy2_http_status") or {}).items():
        raw = (diag.get("strategy2_raw_count") or {}).get(etype, 0)
        short = etype.split("_")[-1]
        print(f"  {short}: HTTP {status}, raw entries returned: {raw}")
    print(f"  new entries added: {diag.get('strategy2_new_entries', 0)}")
    if diag.get("strategy2_parse_errors"):
        print(f"  parse errors: {diag['strategy2_parse_errors'][:3]}")

    print(f"Strategy 3 (upload_id + entry_type):")
    print(f"  batch lookup HTTP: {diag.get('strategy3_batch_http_status', '?')}")
    print(f"  upload_ids found : {diag.get('strategy3_upload_ids', [])}")
    for etype, status in (diag.get("strategy3_http_status") or {}).items():
        raw = (diag.get("strategy3_raw_count") or {}).get(etype, 0)
        short = etype.split("_")[-1]
        print(f"  {short}: HTTP {status}, raw entries returned: {raw}")
    print(f"  new entries added: {diag.get('strategy3_new_entries', 0)}")
    if diag.get("strategy3_exception"):
        print(f"  exception: {diag['strategy3_exception']}")
    if diag.get("strategy3_parse_errors"):
        print(f"  parse errors: {diag['strategy3_parse_errors'][:3]}")

    print(f"\neqe_samples_found (total after all strategies): {diag.get('eqe_samples_found', 0)}")

    # --- Entry structure inspection ---
    if diag.get("entry_structure_sample"):
        print("\n--- Entry Structure (first entries) ---")
        for s in diag["entry_structure_sample"]:
            print(f"  sample_id  : {s['sample_id']}")
            print(f"  entry_type : {s['entry_type']}")
            print(f"  mainfile   : {s['mainfile']}")
            print(f"  top keys   : {s['top_level_keys']}")
            print(f"  eqe_data   : key present={s['has_eqe_data_key']}, type={s['eqe_data_type']}, len={s['eqe_data_len']}")
            print()

    # --- Parsing results ---
    print("--- Parsing Results ---")
    for key in ["total_entries", "entries_without_eqe_data",
                "total_measurements_seen", "parsed_measurements", "dropped_measurements"]:
        if key in diag:
            print(f"{key}: {diag[key]}")

    if diag.get("entry_types_detected"):
        print("entry_types_detected:")
        for et in diag["entry_types_detected"]:
            print(f"  - {et}")

    if diag.get("entry_names_preview"):
        print("entry_names_preview:")
        for name in diag["entry_names_preview"]:
            print(f"  - {name}")

    if diag.get("inferred_sample_ids_outside_batch"):
        print("inferred_sample_ids_outside_batch:")
        for sid in diag["inferred_sample_ids_outside_batch"]:
            print(f"  - {sid}")

    if diag.get("dropped_reasons"):
        print("\nDropped measurement reasons:")
        for reason, count in diag["dropped_reasons"].items():
            print(f"  - {reason}: {count}")

    if diag.get("first_measurement_type"):
        print(f"\nFirst measurement structure:")
        print(f"  type: {diag['first_measurement_type']}")
    if diag.get("first_measurement_keys"):
        print(f"  keys: {diag['first_measurement_keys']}")
    if diag.get("first_measurement_value_types"):
        print("  value types:")
        for k, t in diag["first_measurement_value_types"].items():
            print(f"    {k}: {t}")

    # --- Final dataframes ---
    data = data_manager.get_data() if hasattr(data_manager, "get_data") else {}
    params = data.get("params")
    curves = data.get("curves")
    print("\n--- Final DataFrames ---")
    print(f"params rows: {0 if params is None else len(params)}")
    print(f"curves rows: {0 if curves is None else len(curves)}")

    if (params is None or params.empty) and diag.get("eqe_samples_found", 0) == 0:
        print("\n[!] No EQE entries found at all.")
        print("    Check Strategy results above to identify which lookup failed.")
        print("    Common fixes:")
        print("    - entry_type name may differ (check NOMAD entry type in upload)")
        print("    - EQE files not uploaded in same upload as batch entry")
        print("    - results.eln.lab_ids not populated for this entry type")
    elif (params is None or params.empty) and diag.get("entries_without_eqe_data", 0) > 0:
        print("\n[!] Entries found but all lack 'eqe_data' key.")
        print("    Check 'top keys' in Entry Structure above.")
        print("    The curve arrays may be stored under a different key name.")

    print("=" * 70)


def add_diagnostic_button_to_app(app):
    """Add a diagnostics panel for quick troubleshooting in the UI."""
    button = widgets.Button(
        description="Run EQE Diagnostics",
        button_style="warning",
        tooltip="Show EQE loading and parsing diagnostics",
        layout=widgets.Layout(width="220px"),
    )
    output = widgets.Output(layout=widgets.Layout(border="1px solid #ddd", padding="8px"))

    def _on_click(_b):
        with output:
            clear_output(wait=True)
            diagnose_eqe_loading(app.data_manager)

    button.on_click(_on_click)

    return widgets.VBox(
        [
            widgets.HTML("<h4>Data Diagnostics</h4>"),
            widgets.HTML("<p>Use this after loading to inspect EQE parsing and dropped records.</p>"),
            button,
            output,
        ],
        layout=widgets.Layout(border="1px solid #ddd", padding="10px", margin="10px 0 0 0"),
    )

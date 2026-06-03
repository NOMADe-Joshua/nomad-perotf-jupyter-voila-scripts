"""
Batch selector widget for EQE app.
"""

import re
import importlib.util
import os

import ipywidgets as widgets


def _load_local_get_batch_ids():
    workspace_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    api_calls_path = os.path.join(workspace_root, "api_calls.py")
    spec = importlib.util.spec_from_file_location("workspace_api_calls", api_calls_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load local api_calls module at {api_calls_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.get_batch_ids


get_batch_ids = _load_local_get_batch_ids()


def extract_date(value):
    match = re.search(r"20\d{6}", value or "")
    return int(match.group()) if match else None


def sort_by_date_desc(values):
    return sorted(values, key=lambda x: extract_date(x) if extract_date(x) else 0, reverse=True)


def create_batch_selection(url, token, load_data_function):
    batch_ids_list_tmp = list(get_batch_ids(url, token))
    batch_ids_list = []
    for batch in batch_ids_list_tmp:
        parent = "_".join(batch.split("_")[:-1])
        if parent in batch_ids_list_tmp:
            continue
        batch_ids_list.append(batch)
    batch_ids_list = sort_by_date_desc(batch_ids_list)

    batch_ids_selector = widgets.SelectMultiple(
        options=batch_ids_list,
        description="Batches",
        layout=widgets.Layout(width="400px", height="300px"),
    )

    search_field = widgets.Text(description="Search Batch")
    load_batch_button = widgets.Button(description="Load Data", button_style="primary")

    def on_search_change(change):
        needle = search_field.value.strip().lower()
        batch_ids_selector.options = [b for b in batch_ids_list if needle in b.lower()]

    search_field.observe(on_search_change, names="value")
    load_batch_button.on_click(lambda _b: load_data_function(batch_ids_selector))

    return widgets.VBox([search_field, batch_ids_selector, load_batch_button])

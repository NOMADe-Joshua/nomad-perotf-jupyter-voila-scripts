import ipywidgets as widgets
import importlib.util
import os
import re


def _load_local_get_batch_ids():
    api_calls_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "api_calls.py")
    spec = importlib.util.spec_from_file_location("workspace_api_calls", api_calls_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load local api_calls module at {api_calls_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.get_batch_ids


get_batch_ids = _load_local_get_batch_ids()

def extract_date(s):
    # Suche nach jedem 8-stelligen Datum, das mit "20" beginnt
    match = re.search(r'20\d{6}', s)
    return int(match.group()) if match else None

def sort_by_date_desc(data_list):
    return sorted(
        data_list,
        key=lambda x: extract_date(x) if extract_date(x) else 0,
        reverse=True
    )

def create_batch_selection(url, token, load_data_function):
    # Get batch IDs
    batch_ids_list_tmp = list(get_batch_ids(url, token))
    batch_ids_list = []
    for b in batch_ids_list_tmp:
        if "_".join(b.split("_")[:-1]) in batch_ids_list_tmp:
            continue
        batch_ids_list.append(b)
    batch_ids_list = sort_by_date_desc(batch_ids_list)

    # Create widgets
    batch_ids_selector = widgets.SelectMultiple(
        options=batch_ids_list,
        description='Batches',
        layout=widgets.Layout(width='400px', height='300px')
    )

    search_field = widgets.Text(description="Search Batch")

    load_batch_button = widgets.Button(
        description="Load Data",
        button_style='primary'
    )

    # Define search function
    def on_search_enter(change):
        batch_ids_selector.options = [
            d for d in batch_ids_list
            if search_field.value.strip().lower() in d.lower()
        ]

    # Bind events
    search_field.observe(on_search_enter, names='value')
    load_batch_button.on_click(lambda b: load_data_function(batch_ids_selector))

    # Return the widget container
    return widgets.VBox([search_field, batch_ids_selector, load_batch_button])
"""
AbsPL wrapper around the JV resizable plot utility.
Provides local symbols for static analysis and delegates at runtime.
"""

import importlib.util
import os
from functools import lru_cache


@lru_cache(maxsize=1)
def _load_jv_module():
    here = os.path.dirname(os.path.abspath(__file__))
    module_path = os.path.abspath(os.path.join(here, "..", "JV-Analysis_v6", "resizable_plot_utility_JV.py"))
    spec = importlib.util.spec_from_file_location("resizable_plot_utility_jv_runtime", module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load JV resizable plot utility from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def create_resizable_plot(fig, title="Plot", width=800, height=600, subtitle=None, filename=None):
    module = _load_jv_module()
    return module.create_resizable_plot(fig, title=title, width=width, height=height, subtitle=subtitle, filename=filename)


class ResizablePlotManager:
    """Static-analysis-friendly delegating wrapper for the JV resizable plot manager."""

    @staticmethod
    def display_plots_resizable(figs, filenames, titles=None, subtitles=None, container_widget=None, jv_legend_table=False):
        module = _load_jv_module()
        return module.ResizablePlotManager.display_plots_resizable(
            figs,
            filenames,
            titles=titles,
            subtitles=subtitles,
            container_widget=container_widget,
            jv_legend_table=jv_legend_table,
        )

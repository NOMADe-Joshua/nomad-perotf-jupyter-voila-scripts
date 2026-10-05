# Graph Report - nomad-perotf-jupyter-voila-scripts  (2026-10-05)

## Corpus Check
- 83 files · ~127,697 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 67 file(s) not represented in the graph (top: .ipynb 63, (none) 1, .csv 1)

## Summary
- 2431 nodes · 3840 edges · 149 communities (35 shown, 114 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 105 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `5ca385ba`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- MinimalistExperimentBuilder
- requests
- numpy
- ipywidgets
- AbsPLGUIComponents
- ValidationUtils
- AbsPLAppController
- DoEApplication
- ColorSchemeSelector
- app_controller_JV.py
- DataManager
- fitting_tools_MPPt.py
- sampling_algorithms.py
- EnhancedJVCurveAnalysisUI
- Variable
- GUIComponents
- DataManager
- AbsPLPlotManager
- PlotManager
- DragDropUploadWidget
- JVAnalysisApp
- FilterUI
- GUILayouts
- PLAnalysisApp
- os
- PlotUI
- PLExportUtils
- UVVisAnalysisApp
- ResultExporter
- DesignOfExperiments/utils.py
- SamplingEngine
- EQEAnalysisApp
- UVVisPlotManager
- ColorSchemeSelector
- WidgetFactory
- AuthenticationManager
- DataManagerEQE
- PLPeakDetection
- FittingEngine
- PeakDetector
- DataManager
- FittingModels
- process_handling.py
- AuthenticationUI
- CSVDataLoader
- JVCurveAnalysisUI
- plot_manager_EQE.py
- PLFittingModels
- ._create_variable_widget
- XRD_PF/data_manager.py
- APIClient
- ColorSchemeSelector
- ResizablePlotManager
- XRDAnalysisApp
- uvvis_app_controller.py
- re
- GUIComponents
- diagnostic_helper_JV.py
- FontSizeUI
- FontSizeUI
- FontSizeUI
- UVVisPlotUI
- zipfile
- MaximinDistanceSampling
- MathUtils
- PLDataLoader
- .__init__
- AuthenticationUI
- eqe_split_module.py
- AuthenticationUI
- ._create_condition_selector
- SaveUI
- PlotManager
- UVVisDiagnosticHelper
- XRD_PF/utils.py
- .display
- SimpleAuthManager
- UVVisBatchSelector
- SimpleAuthManager
- AbsPL: Sweep vs. Single PL – Unterscheidung
- SimpleAuthManager
- ErrorHandler
- generate_jv_pptx_bytes
- MPPT Analysis Tool - User Manual
- UVVisDataManager
- H5DataLoader
- io
- ._create_filtered_curves_data
- .update_variable_reorder
- PLVisualization
- process_files
- LatinHypercubeSampling
- FontSizeUI
- ._build_theresa_jv_plot
- ._create_matching_curves_from_filtered_jv
- InfoUI
- ChebyshevBackgroundModel
- SobolSampling
- SaveUI
- WidgetFactory
- DiagnosticLogger
- .get_variables_from_widgets
- ColorUtils
- How to use
- ._make_move_up_handler
- ChemicalSolutionCalculator
- .update_heatmap_colorbar
- ResizablePlotManager
- README.md
- Wetting_envelope/README.md

## God Nodes (most connected - your core abstractions)
1. `JVAnalysisApp` - 54 edges
2. `Variable` - 44 edges
3. `PLAnalysisApp` - 41 edges
4. `PlotManager` - 37 edges
5. `GUIComponents` - 36 edges
6. `EQEAnalysisApp` - 35 edges
7. `PlotUI` - 33 edges
8. `AbsPLPlotManager` - 32 edges
9. `UVVisAnalysisApp` - 29 edges
10. `DataManager` - 27 edges

## Surprising Connections (you probably didn't know these)
- `AbsPLAppController` --uses--> `AuthenticationManager`  [INFERRED]
  AbsPL_Analysis/app_controller_abspl.py → auth_manager.py
- `AbsPLAppController` --uses--> `AuthenticationUI`  [INFERRED]
  AbsPL_Analysis/app_controller_abspl.py → auth_ui.py
- `create_batch_selection()` --calls--> `get_batch_ids()`  [INFERRED]
  EQE-Curve_Analysis/batch_selection_EQE.py → api_calls.py
- `JVAnalysisApp` --uses--> `ErrorHandler`  [INFERRED]
  JV-Analysis_v6/app_controller_JV.py → error_handler.py
- `DataManager` --uses--> `ErrorHandler`  [INFERRED]
  JV-Analysis_v6/data_manager_JV.py → error_handler.py

## Import Cycles
- None detected.

## Communities (149 total, 114 thin omitted)

### Community 0 - "MinimalistExperimentBuilder"
Cohesion: 0.05
Nodes (11): ExperimentExcelBuilder, add_guide_sheet(), add_experiment_sheet(), generate_steps_for_process(), make_label(), lighten_color(), add_citation_sheet(), create_experiment_app() (+3 more)

### Community 1 - "requests"
Cohesion: 0.07
Nodes (27): get_all_batches_wth_data(), get_all_eqe(), get_all_JV(), get_all_measurements_except_JV(), get_all_mppt(), get_all_uploads(), get_all_xrd(), get_batch_ids() (+19 more)

### Community 2 - "numpy"
Cohesion: 0.06
Nodes (6): calculate_activity_coefficients_unifac(), calculate_overall_donor_number_with_unifac(), parse_smiles_to_unifac_groups(), calculate_activity_coefficients_unifac(), calculate_overall_donor_number_with_unifac(), parse_smiles_to_unifac_groups()

### Community 3 - "ipywidgets"
Cohesion: 0.08
Nodes (7): create_batch_selection(), add_diagnostic_button_to_app(), _on_click(), _on_mj_click(), diagnose_eqe_loading(), diagnose_multijunction(), test_resizable_plot()

### Community 4 - "AbsPLGUIComponents"
Cohesion: 0.06
Nodes (7): AbsPLGUIComponents, _parse_curve_bound(), remove_row(), _render_fit_curve_ranges(), _set_curve_range(), _remove(), ColorSchemeSelector

### Community 5 - "ValidationUtils"
Cohesion: 0.05
Nodes (5): DataProcessor, ExperimentalDesignUtils, FileHandler, safe_float_conversion(), ValidationUtils

### Community 6 - "AbsPLAppController"
Cohesion: 0.06
Nodes (9): AbsPLAppController, launch_abspl_app(), AbsPLDataManager, extract_cycle_info(), extract_description_notes(), create_resizable_plot(), display_resizable_plot(), ResizablePlotManager (+1 more)

### Community 8 - "ColorSchemeSelector"
Cohesion: 0.06
Nodes (5): ColorSchemeSelector, SaveUI, create_resizable_plot(), display_resizable_plot(), ResizablePlotWidget

### Community 9 - "app_controller_JV.py"
Cohesion: 0.06
Nodes (14): _load_pptxgenjs(), _flatten_multiindex_columns(), plot_list_from_voila(), plotting_string_action(), clean_filename(), create_new_results_folder(), generate_detailed_export_excel(), is_running_in_jupyter() (+6 more)

### Community 11 - "fitting_tools_MPPt.py"
Cohesion: 0.07
Nodes (24): calculate_ley(), erfc_linear(), erfc_params(), extrapolate(), find_T80(), find_tS(), find_Ts80(), fit_model (+16 more)

### Community 12 - "sampling_algorithms.py"
Cohesion: 0.07
Nodes (5): HaltonSampling, OrthogonalArraySampling, RandomSampling, SamplingAlgorithm, UniformGridSampling

### Community 20 - "DragDropUploadWidget"
Cohesion: 0.08
Nodes (3): DragDropMultiUploadWidget, DragDropUploadWidget, update_list()

### Community 25 - "os"
Cohesion: 0.11
Nodes (8): create_batch_selection(), extract_date(), sort_by_date_desc(), extract_date(), sort_by_date_desc(), _extract_xrd_arrays(), _search(), _to_1d()

### Community 30 - "DesignOfExperiments/utils.py"
Cohesion: 0.10
Nodes (10): extract_channel_from_block(), extract_metadata(), format_old_file(), parse_sample_blocks(), parse_scan(), process_single_file(), Constants, format_percentage() (+2 more)

### Community 35 - "WidgetFactory"
Cohesion: 0.10
Nodes (6): create_manual(), only_curve_name(), only_sample_name(), plot_options, sample_and_curve_name(), WidgetFactory

### Community 44 - "process_handling.py"
Cohesion: 0.16
Nodes (9): batch_process, create_step_description(), param_selection_buttons(), flatten_layers(), make_table(), manufacturing_parameter, merge_process(), merge_step_data() (+1 more)

### Community 48 - "plot_manager_EQE.py"
Cohesion: 0.17
Nodes (8): _build_legend_annotation(), _build_mj_legend_annotation(), _compute_cumulative_jsc_am15g(), _compute_group_stats(), create_eqe_figure(), _format_ann_val(), _get_am15g(), _positions_label()

### Community 52 - "XRD_PF/data_manager.py"
Cohesion: 0.14
Nodes (5): get_token(), log_notebook_usage(), get_axes_from_extent(), sanitize_array(), sanitize_float()

### Community 55 - "ResizablePlotManager"
Cohesion: 0.13
Nodes (4): create_resizable_plot(), display_resizable_plot(), ResizablePlotManager, ResizablePlotWidget

### Community 57 - "uvvis_app_controller.py"
Cohesion: 0.16
Nodes (3): extract_date(), sort_by_date_desc(), UVVisAuthenticationUI

### Community 58 - "re"
Cohesion: 0.22
Nodes (5): filter_soak_files(), process_files(), process_mpp_files(), process_zip_file(), rename_jv_files()

### Community 60 - "diagnostic_helper_JV.py"
Cohesion: 0.15
Nodes (4): add_diagnostic_button_to_app(), on_diagnose_click(), DebugLogger, diagnose_direction_values()

### Community 66 - "zipfile"
Cohesion: 0.22
Nodes (5): extract_x_y(), get_oldest_file_date(), process_files(), process_zip_file(), rename_files()

### Community 73 - "eqe_split_module.py"
Cohesion: 0.21
Nodes (5): create_download_zip(), format_eqe_output(), generate_filename(), parse_eqe_file(), process_eqe_file()

### Community 75 - "._create_condition_selector"
Cohesion: 0.23
Nodes (4): clear_all_samples(), create_sample_checkbox_handler(), handler(), select_all_samples()

### Community 80 - "XRD_PF/utils.py"
Cohesion: 0.18
Nodes (5): debug_print(), format_timestamp(), generate_output_filename(), safe_divide(), validate_time_index()

### Community 82 - ".display"
Cohesion: 0.18
Nodes (4): create_resizable_plot(), display_resizable_plot(), ResizablePlotManager, ResizablePlotWidget

### Community 86 - "AbsPL: Sweep vs. Single PL – Unterscheidung"
Cohesion: 0.20
Nodes (9): AbsPL: Sweep vs. Single PL – Unterscheidung, Dateiformat-Unterschiede, Empfohlener Check im Archiv, Kontext, Schnellster Datei-Typ-Check, Single PL (`_FD7.abspl.txt`), Sweep (`_D1.abspl.txt`), Unterschiede im gespeicherten Archiv (auf dem Server) (+1 more)

### Community 90 - "generate_jv_pptx_bytes"
Cohesion: 0.22
Nodes (3): _fig_to_png_bytes(), generate_jv_pptx_bytes(), _add_figure()

### Community 91 - "MPPT Analysis Tool - User Manual"
Cohesion: 0.20
Nodes (9): 1. Batch Selection, 2. Sample Selection, 3. Curve Fitting, 4. Plotting and Visualization, 5. Download Results, MPPT Analysis Tool - User Manual, Overview, Tips and Best Practices (+1 more)

### Community 97 - "io"
Cohesion: 0.31
Nodes (3): find_matching_pairs(), merge_uvvis_files(), process_uvvis_files()

### Community 98 - "._create_filtered_curves_data"
Cohesion: 0.28
Nodes (3): _norm_cycle(), _norm_text(), should_include_curve()

### Community 101 - "process_files"
Cohesion: 0.25
Nodes (4): parse_filename_base(), process_files(), process_pt_file(), process_zip_file()

### Community 106 - "._create_matching_curves_from_filtered_jv"
Cohesion: 0.32
Nodes (3): _norm_cycle(), _norm_text(), should_include_curve()

### Community 121 - "How to use"
Cohesion: 0.33
Nodes (5): 1. Select the batches containing the data you want to analyze., 2. Dataset Names, 3. model fitting, 4. create plots, How to use

## Knowledge Gaps
- **20 isolated node(s):** `Kontext`, `Single PL (`_FD7.abspl.txt`)`, `Sweep (`_D1.abspl.txt`)`, `Schnellster Datei-Typ-Check`, `Empfohlener Check im Archiv` (+15 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1151 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **114 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `JVAnalysisApp` connect `JVAnalysisApp` to `._create_debug_dashboard`, `._create_filtered_curves_data`, `ColorSchemeSelector`, `app_controller_JV.py`, `._build_theresa_jv_plot`, `InfoUI`, `SaveUI`, `EnhancedJVCurveAnalysisUI`, `PlotManager`, `DataManager`, `._on_create_curve_analysis_plot`, `.display`, `FilterUI`, `ResizablePlotManager`, `ErrorHandler`, `PlotUI`, `FontSizeUI`?**
  _High betweenness centrality (0.113) - this node is a cross-community bridge._
- **Are the 11 inferred relationships involving `JVAnalysisApp` (e.g. with `ErrorHandler` and `DataManager`) actually correct?**
  _`JVAnalysisApp` has 11 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Kontext`, `Single PL (`_FD7.abspl.txt`)`, `Sweep (`_D1.abspl.txt`)` to the rest of the system?**
  _20 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `MinimalistExperimentBuilder` be split into smaller, more focused modules?**
  _Cohesion score 0.05182443151771549 - nodes in this community are weakly interconnected._
- **Why does `GUIComponents` connect `GUIComponents` to `ipywidgets`, `.create_seed_configurator`, `.create_download_link`, `Widget`, `.set_current_data`, `._create_variable_widget`, `.get_variables_from_widgets`, `.update_metrics_display`?**
  _High betweenness centrality (0.093) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `PLAnalysisApp` (e.g. with `ResultExporter` and `FittingEngine`) actually correct?**
  _`PLAnalysisApp` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Should `requests` be split into smaller, more focused modules?**
  _Cohesion score 0.07012987012987013 - nodes in this community are weakly interconnected._
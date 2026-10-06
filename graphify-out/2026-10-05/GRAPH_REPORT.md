# Graph Report - nomad-perotf-jupyter-voila-scripts  (2026-10-05)

## Corpus Check
- 89 files · ~146,235 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 68 file(s) not represented in the graph (top: .ipynb 64, (none) 1, .csv 1)

## Summary
- 2670 nodes · 4265 edges · 166 communities (37 shown, 129 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 113 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `8fa013b8`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- MinimalistExperimentBuilder
- requests
- numpy
- app_controller_JV.py
- AbsPLGUIComponents
- ValidationUtils
- AbsPLAppController
- DoEApplication
- ColorSchemeSelector
- utils_JV.py
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
- os
- PlotUI
- PLExportUtils
- UVVisAnalysisApp
- ResultExporter
- io
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
- batch_process
- AuthenticationUI
- CSVDataLoader
- JVCurveAnalysisUI
- plot_manager_EQE.py
- PLFittingModels
- ._create_variable_widget
- ProcessJVOverviewApp
- APIClient
- ColorSchemeSelector
- ResizablePlotManager
- XRDAnalysisApp
- generate_detailed_export_excel
- ._load_data_from_selection
- GUIComponents
- DebugLogger
- FontSizeUI
- FontSizeUI
- FontSizeUI
- UVVisPlotUI
- ._make_boxplot
- plot_manager_JV.py
- MathUtils
- PLDataLoader
- plotting_string_action
- process_eqe_file
- AuthenticationUI
- ._create_condition_selector
- SaveUI
- PlotManager
- UVVisDiagnosticHelper
- XRD_PF/utils.py
- DataManager
- .display
- SimpleAuthManager
- UVVisBatchSelector
- SimpleAuthManager
- AbsPL: Sweep vs. Single PL – Unterscheidung
- SimpleAuthManager
- AuthenticationUI
- generate_jv_pptx_bytes
- MPPT Analysis Tool - User Manual
- UVVisDataManager
- H5DataLoader
- PLAnalysisApp
- ._create_filtered_curves_data
- .update_variable_reorder
- PLVisualization
- LatinHypercubeSampling
- FontSizeUI
- ._build_theresa_jv_plot
- PlotManager
- InfoUI
- ChebyshevBackgroundModel
- SobolSampling
- ._render_batch
- SaveUI
- WidgetFactory
- DiagnosticLogger
- .get_variables_from_widgets
- SimpleAuthManager
- How to use
- ._make_move_up_handler
- ChemicalSolutionCalculator.py
- .setup_callbacks
- ._init_batch_selection
- .display
- Plotter
- README.md
- Wetting_envelope/README.md
- _extract_xrd_arrays
- CLAUDE.md
- ._update_wavelength_range_on_spectrum
- add_diagnostic_button_to_app
- LoadingProgress
- ToggleBatchProcess
- ColorUtils
- batch_selection_EQE.py
- ._on_auth_success

## God Nodes (most connected - your core abstractions)
1. `JVAnalysisApp` - 54 edges
2. `Variable` - 44 edges
3. `PLAnalysisApp` - 41 edges
4. `PlotManager` - 37 edges
5. `GUIComponents` - 36 edges
6. `EQEAnalysisApp` - 35 edges
7. `PlotUI` - 33 edges
8. `PlotManager` - 33 edges
9. `AbsPLPlotManager` - 32 edges
10. `ProcessJVOverviewApp` - 29 edges

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

## Communities (166 total, 129 thin omitted)

### Community 0 - "MinimalistExperimentBuilder"
Cohesion: 0.05
Nodes (11): ExperimentExcelBuilder, add_guide_sheet(), add_experiment_sheet(), generate_steps_for_process(), make_label(), lighten_color(), add_citation_sheet(), create_experiment_app() (+3 more)

### Community 1 - "requests"
Cohesion: 0.05
Nodes (33): get_token(), get_all_batches_wth_data(), get_all_eqe(), get_all_JV(), get_all_measurements_except_JV(), get_all_mppt(), get_all_uploads(), get_all_xrd() (+25 more)

### Community 2 - "numpy"
Cohesion: 0.05
Nodes (14): Constants, format_percentage(), generate_experiment_id(), truncate_string(), calculate_activity_coefficients_unifac(), calculate_overall_donor_number_with_unifac(), parse_smiles_to_unifac_groups(), calculate_activity_coefficients_unifac() (+6 more)

### Community 3 - "app_controller_JV.py"
Cohesion: 0.06
Nodes (7): create_batch_selection(), extract_date(), sort_by_date_desc(), test_resizable_plot(), create_resizable_plot(), display_resizable_plot(), test_resizable_plot()

### Community 4 - "AbsPLGUIComponents"
Cohesion: 0.06
Nodes (7): AbsPLGUIComponents, _parse_curve_bound(), remove_row(), _render_fit_curve_ranges(), _set_curve_range(), _remove(), ColorSchemeSelector

### Community 5 - "ValidationUtils"
Cohesion: 0.05
Nodes (5): DataProcessor, ExperimentalDesignUtils, FileHandler, safe_float_conversion(), ValidationUtils

### Community 6 - "AbsPLAppController"
Cohesion: 0.06
Nodes (8): AbsPLAppController, launch_abspl_app(), AbsPLDataManager, extract_description_notes(), create_resizable_plot(), display_resizable_plot(), ResizablePlotManager, ResizablePlotWidget

### Community 8 - "ColorSchemeSelector"
Cohesion: 0.06
Nodes (5): ColorSchemeSelector, SaveUI, create_resizable_plot(), display_resizable_plot(), ResizablePlotWidget

### Community 9 - "utils_JV.py"
Cohesion: 0.05
Nodes (14): clean_filename(), create_new_results_folder(), is_running_in_jupyter(), save_full_data_frame(), clean_filename(), create_new_results_folder(), generate_detailed_export_excel(), is_running_in_jupyter() (+6 more)

### Community 11 - "fitting_tools_MPPt.py"
Cohesion: 0.07
Nodes (24): calculate_ley(), erfc_linear(), erfc_params(), extrapolate(), find_T80(), find_tS(), find_Ts80(), fit_model (+16 more)

### Community 12 - "sampling_algorithms.py"
Cohesion: 0.06
Nodes (5): HaltonSampling, OrthogonalArraySampling, RandomSampling, SamplingAlgorithm, UniformGridSampling

### Community 16 - "DataManager"
Cohesion: 0.05
Nodes (4): DataManager, _norm_cycle(), _norm_text(), should_include_curve()

### Community 20 - "DragDropUploadWidget"
Cohesion: 0.08
Nodes (3): DragDropMultiUploadWidget, DragDropUploadWidget, update_list()

### Community 25 - "os"
Cohesion: 0.08
Nodes (6): extract_cycle_info(), log_notebook_usage(), ResizablePlotManager, get_axes_from_extent(), sanitize_array(), sanitize_float()

### Community 28 - "UVVisAnalysisApp"
Cohesion: 0.11
Nodes (3): UVVisAnalysisApp, UVVisAuthenticationUI, UVVisSaveUI

### Community 30 - "io"
Cohesion: 0.05
Nodes (24): extract_x_y(), get_oldest_file_date(), process_files(), process_zip_file(), rename_files(), create_download_zip(), extract_channel_from_block(), extract_metadata() (+16 more)

### Community 35 - "WidgetFactory"
Cohesion: 0.10
Nodes (6): create_manual(), only_curve_name(), only_sample_name(), plot_options, sample_and_curve_name(), WidgetFactory

### Community 44 - "batch_process"
Cohesion: 0.21
Nodes (6): batch_process, create_step_description(), param_selection_buttons(), flatten_layers(), make_table(), manufacturing_parameter

### Community 48 - "plot_manager_EQE.py"
Cohesion: 0.17
Nodes (8): _build_legend_annotation(), _build_mj_legend_annotation(), _compute_cumulative_jsc_am15g(), _compute_group_stats(), create_eqe_figure(), _format_ann_val(), _get_am15g(), _positions_label()

### Community 55 - "ResizablePlotManager"
Cohesion: 0.13
Nodes (4): create_resizable_plot(), display_resizable_plot(), ResizablePlotManager, ResizablePlotWidget

### Community 67 - "plot_manager_JV.py"
Cohesion: 0.12
Nodes (4): _flatten_multiindex_columns(), plot_list_from_voila(), plotting_string_action(), save_combined_excel_data()

### Community 73 - "process_eqe_file"
Cohesion: 0.25
Nodes (4): format_eqe_output(), generate_filename(), parse_eqe_file(), process_eqe_file()

### Community 75 - "._create_condition_selector"
Cohesion: 0.23
Nodes (4): clear_all_samples(), create_sample_checkbox_handler(), handler(), select_all_samples()

### Community 80 - "XRD_PF/utils.py"
Cohesion: 0.18
Nodes (5): debug_print(), format_timestamp(), generate_output_filename(), safe_divide(), validate_time_index()

### Community 81 - "DataManager"
Cohesion: 0.05
Nodes (5): variation_from_identifier(), DataManager, _norm_cycle(), _norm_text(), should_include_curve()

### Community 82 - ".display"
Cohesion: 0.15
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

### Community 98 - "._create_filtered_curves_data"
Cohesion: 0.28
Nodes (3): _norm_cycle(), _norm_text(), should_include_curve()

### Community 113 - "._render_batch"
Cohesion: 0.24
Nodes (3): count_samples(), format_date(), format_error()

### Community 114 - "SaveUI"
Cohesion: 0.15
Nodes (4): add_diagnostic_button_to_app(), _on_mj_click(), diagnose_multijunction(), SaveUI

### Community 121 - "How to use"
Cohesion: 0.33
Nodes (5): 1. Select the batches containing the data you want to analyze., 2. Dataset Names, 3. model fitting, 4. create plots, How to use

### Community 153 - "_extract_xrd_arrays"
Cohesion: 0.67
Nodes (3): _extract_xrd_arrays(), _search(), _to_1d()

### Community 158 - "add_diagnostic_button_to_app"
Cohesion: 0.40
Nodes (3): add_diagnostic_button_to_app(), on_diagnose_click(), diagnose_direction_values()

### Community 171 - "batch_selection_EQE.py"
Cohesion: 0.32
Nodes (3): create_batch_selection(), extract_date(), sort_by_date_desc()

### Community 172 - "._on_auth_success"
Cohesion: 0.20
Nodes (3): get_batches_with_uploads(), get_upload_ids_with_entries(), parse_batch_id()

## Knowledge Gaps
- **21 isolated node(s):** `Kontext`, `Single PL (`_FD7.abspl.txt`)`, `Sweep (`_D1.abspl.txt`)`, `Schnellster Datei-Typ-Check`, `Empfohlener Check im Archiv` (+16 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1270 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **129 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `JVAnalysisApp` connect `JVAnalysisApp` to `._create_debug_dashboard`, `requests`, `app_controller_JV.py`, `EnhancedJVCurveAnalysisUI`, `DataManager`, `.display`, `FilterUI`, `PlotUI`, `ColorSchemeSelector`, `._on_create_plots`, `ResizablePlotManager`, `generate_detailed_export_excel`, `FontSizeUI`, `SaveUI`, `PlotManager`, `._create_filtered_curves_data`, `._make_variables_menu`, `._build_theresa_jv_plot`, `InfoUI`?**
  _High betweenness centrality (0.111) - this node is a cross-community bridge._
- **Are the 11 inferred relationships involving `JVAnalysisApp` (e.g. with `ErrorHandler` and `DataManager`) actually correct?**
  _`JVAnalysisApp` has 11 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Kontext`, `Single PL (`_FD7.abspl.txt`)`, `Sweep (`_D1.abspl.txt`)` to the rest of the system?**
  _21 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `MinimalistExperimentBuilder` be split into smaller, more focused modules?**
  _Cohesion score 0.053005464480874315 - nodes in this community are weakly interconnected._
- **Why does `GUIComponents` connect `GUIComponents` to `.create_seed_configurator`, `.create_download_link`, `utils_JV.py`, `Widget`, `.set_current_data`, `._create_variable_widget`, `.get_variables_from_widgets`, `.update_metrics_display`?**
  _High betweenness centrality (0.091) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `PLAnalysisApp` (e.g. with `ResultExporter` and `FittingEngine`) actually correct?**
  _`PLAnalysisApp` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Should `requests` be split into smaller, more focused modules?**
  _Cohesion score 0.045987654320987656 - nodes in this community are weakly interconnected._
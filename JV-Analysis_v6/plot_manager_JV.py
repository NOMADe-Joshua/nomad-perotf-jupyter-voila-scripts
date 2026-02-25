"""
Plot Management Module
Handles all plotting operations including JV curves, boxplots, and histograms.
Extracted from main.py for better organization.
"""

__author__ = "Edgar Nandayapa"
__institution__ = "Helmholtz-Zentrum Berlin"
__created__ = "August 2025"

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import numpy as np
import pandas as pd
import os
import sys
import math  # Add this import for ceiling calculation

# Add parent directory for shared modules
parent_dir = os.path.dirname(os.getcwd())
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

try:
    from utils_JV import save_combined_excel_data
except ImportError:
    # Fallback if utils not available
    def save_combined_excel_data(*args, **kwargs):
        return None

def _flatten_multiindex_columns(self, df):
    """Flatten MultiIndex columns if they exist"""
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = ['_'.join(col).strip() for col in df.columns.values]
    return df

def plotting_string_action(plot_list, data, supp, is_voila=False, color_scheme=None, separate_scan_dir=False, font_size_axis=None, font_size_title=None, font_size_legend=None):
    """
    Main plotting function that processes plot codes and creates figures.
    
    Parameters:
    -----------
    font_size_axis : int, optional
        Font size for axis labels and tick labels (default: 15)
    font_size_title : int, optional
        Font size for plot titles (default: 16)
    font_size_legend : int, optional
        Font size for legend text (default: 10)
    """
    filtered_jv, complete_jv, filtered_curves = data
    omitted_jv, filter_pars, is_conditions, path, samples = supp

    complete_curves = filtered_curves

    # Create plot manager
    plot_manager = PlotManager()
    plot_manager.set_output_path(path)
    
    # Set font sizes if provided
    if font_size_axis is not None or font_size_title is not None or font_size_legend is not None:
        plot_manager.set_font_sizes(font_size_axis, font_size_title, font_size_legend)

    if color_scheme is None:
        color_scheme = [
            'rgba(93, 164, 214, 0.7)', 'rgba(255, 144, 14, 0.7)', 
            'rgba(44, 160, 101, 0.7)', 'rgba(255, 65, 54, 0.7)', 
            'rgba(207, 114, 255, 0.7)', 'rgba(127, 96, 0, 0.7)',
            'rgba(255, 140, 184, 0.7)', 'rgba(79, 90, 117, 0.7)'
        ]

    # Mapping dictionaries for plot codes
    varx_dict = {"a": "sample", "b": "cell", "c": "direction", "d": "ilum", "e": "batch", "g": "condition", "s": "status"}
    vary_dict = {"v": "voc", "j": "jsc", "f": "ff", "p": "pce", "u": "vmpp", "i": "jmpp", "m": "pmpp", "r": "rser", "h": "rshu"}

    fig_list = []
    fig_names = []
    
    # Convert plot selections to codes if needed
    if isinstance(plot_list[0], tuple):
        plot_codes = plot_list_from_voila(plot_list)
    else:
        plot_codes = plot_list

    for pl in plot_codes:
        # Check if there is "condition" requirement
        if "g" in pl and not is_conditions:
            continue
            
        # CRITICAL FIX: sanitize 'all' and use PRIORITY parsing for var_x (Option 2)
        parse_code = pl
        if pl.startswith("Ball") or pl.startswith("Jall"):
            parse_code = pl.replace("all", "")

        # Priority for grouping tokens from Option 2:
        # prefer 'g' (condition), then 'e' (batch), 'a' (sample), 'b' (cell),
        # 'c' (direction), 's' (status), 'd' (ilum)
        varx_priority = ['g', 'e', 'a', 'b', 'c', 's', 'd']

        # Determine var_x using priority (instead of arbitrary substring match)
        var_x = None
        for key in varx_priority:
            if key in parse_code:
                var_x = {"a": "sample", "b": "cell", "c": "direction", "d": "ilum", "e": "batch", "g": "condition", "s": "status"}[key]
                break

        # Determine var_y normally (single-char JV param code)
        vary_dict = {"v": "voc", "j": "jsc", "f": "ff", "p": "pce", "u": "vmpp", "i": "jmpp", "m": "pmpp", "r": "rser", "h": "rshu"}
        var_y = next((vary_dict[key] for key in vary_dict if key in parse_code), None)

        # CRITICAL: Initialize fig and fig_name to None at start of each iteration
        fig = None
        fig_name = None

        try:
            # Combined grid for 'all' – now gets correct var_x from Option 2
            if "Ball" in pl and var_x:
                fig, fig_name = plot_manager.create_combined_boxplot_grid(
                    filtered_jv, var_x,
                    [omitted_jv, filter_pars],
                    "data", colors=color_scheme,
                    separate_scan_dir=separate_scan_dir
                )
            elif "Jall" in pl and var_x:
                fig, fig_name = plot_manager.create_combined_boxplot_grid(
                    omitted_jv, var_x,
                    [filtered_jv, filter_pars],
                    "junk", colors=color_scheme,
                    separate_scan_dir=separate_scan_dir
                )
            # Regular boxplots remain unchanged
            elif "B" in pl and var_x and var_y:
                fig, fig_name, wb, title_text, subtitle = plot_manager.create_boxplot(
                    filtered_jv, var_x, var_y,
                    [omitted_jv, filter_pars],
                    "data", colors=color_scheme,
                    separate_scan_dir=separate_scan_dir
                )
            elif "J" in pl and var_x and var_y:
                fig, fig_name, wb, title_text, subtitle = plot_manager.create_boxplot(
                    omitted_jv, var_x, var_y,
                    [filtered_jv, filter_pars],
                    "junk", colors=color_scheme,  # FIX: Added missing colors argument
                    separate_scan_dir=separate_scan_dir
                )
            elif "H" in pl and var_y:
                fig, fig_name = plot_manager.create_histogram(filtered_jv, var_y)
                # Don't continue - let it fall through to append at end
                   
            elif "Cb" in pl:
                fig, fig_name = plot_manager.create_jv_best_per_condition_plot(filtered_jv, filtered_curves, colors=color_scheme)
            elif "Cw" in pl:
                fig, fig_name = plot_manager.create_jv_best_device_plot(filtered_jv, filtered_curves, colors=color_scheme)
            elif "Cy" in pl:
                fig, fig_name = plot_manager.create_jv_all_cells_plot(complete_jv, filtered_curves, colors=color_scheme)
            elif "Cz" in pl:
                working_curves = plot_manager._create_matching_curves_data(filtered_jv, complete_curves)
                fig, fig_name = plot_manager.create_jv_working_cells_plot(filtered_jv, working_curves, colors=color_scheme)
            elif "Co" in pl:
                if not omitted_jv.empty:
                    rejected_pce_min = omitted_jv['PCE(%)'].min()
                    rejected_pce_max = omitted_jv['PCE(%)'].max() 
                    rejected_pce_mean = omitted_jv['PCE(%)'].mean()

                    # Show some example rejected samples
                    rejected_samples = omitted_jv[['sample', 'cell', 'PCE(%)', 'filter_reason']].head(5)
                    for _, row in rejected_samples.iterrows():
                        reason = row.get('filter_reason', 'No reason specified')
                else:
                    print(f"  No rejected data available!")
                
                # Create filtered curves that match only the omitted JV data
                rejected_curves = plot_manager._create_matching_curves_data(omitted_jv, complete_curves)
                
                print(f"  Rejected curves after filtering: {len(rejected_curves)}")
                
                if not rejected_curves.empty:
                    unique_rejected_devices = rejected_curves.groupby(['sample', 'cell']).size().reset_index()
                fig, fig_name = plot_manager.create_jv_non_working_cells_plot(omitted_jv, rejected_curves, colors=color_scheme)
            elif "Cx" in pl:
                figs, fig_names_temp = plot_manager.create_jv_separated_by_cell_plot(complete_jv, complete_curves, colors=color_scheme)  
                if isinstance(figs, list) and isinstance(fig_names_temp, list):
                    fig_list.extend(figs)
                    fig_names.extend(fig_names_temp)
                else:
                    fig_list.append(figs)
                    fig_names.append(fig_names_temp)
                continue
            elif "Cd" in pl:
                figs, fig_names_temp = plot_manager.create_jv_separated_by_substrate_plot(complete_jv, complete_curves, colors=color_scheme, plot_type="all") 
                if isinstance(figs, list) and isinstance(fig_names_temp, list):
                    fig_list.extend(figs)
                    fig_names.extend(fig_names_temp)
                else:
                    fig_list.append(figs)
                    fig_names.append(fig_names_temp)
                continue
            else:
                print(f"Plot code {pl} not fully implemented yet")
                continue

            # CRITICAL: Only append if fig was actually created
            if fig is not None and fig_name is not None:
                fig_list.append(fig)
                fig_names.append(fig_name)
            
        except Exception as e:
            print(f"❌ Error creating plot {pl}: {e}")
            import traceback
            traceback.print_exc()
            continue

    return fig_list, fig_names


def plot_list_from_voila(plot_list):
    """Convert plot selections from UI to plot codes"""
    jvc_dict = {
        'Voc': 'v', 
        'Jsc': 'j', 
        'FF': 'f', 
        'PCE': 'p', 
        'R_ser': 'r', 
        'R_shu': 'h', 
        'V_mpp': 'u', 
        'J_mpp': 'i', 
        'P_mpp': 'm', 
        'all': 'all'  # Maps to combined grid boxplot
    }
    
    box_dict = {
        'by Batch': 'e', 
        'by Variable': 'g', 
        'by Sample': 'a', 
        'by Cell': 'b', 
        'by Scan Direction': 'c',
        'by Status': 's', 
        'by Status and Variable': 'sg', 
        'by Direction and Variable': 'cg', 
        'by Cell and Variable': 'bg',
        'by Direction, Status and Variable': 'csg'
    }

    cur_dict = {
        'All cells': 'Cy', 
        'Only working cells': 'Cz', 
        'Rejected cells': 'Co', 
        'Best device only': 'Cw', 
        'Best device per condition': 'Cb',
        'Separated by cell (all)': 'Cx',
        'Separated by cell (working only)': 'Cxw',
        'Separated by substrate (all)': 'Cd',
        'Separated by substrate (working only)': 'Cdw'
    }

    new_list = []
    for plot in plot_list:
        code = ''
        plot_type, option1, option2 = plot
        
        if "omitted" in plot_type:
            code += "J"
            param_code = jvc_dict.get(option1, '')
            code += param_code
            # Only add box_dict code if NOT "all" parameter
            if param_code != 'all':
                code += box_dict.get(option2, '')
            else:
                # For "all", we need the x-axis variable
                code += box_dict.get(option2, '')
        elif "Boxplot" in plot_type:
            code += "B"
            param_code = jvc_dict.get(option1, '')
            code += param_code
            # Only add box_dict code if NOT "all" parameter
            if param_code != 'all':
                code += box_dict.get(option2, '')
            else:
                # For "all", we need the x-axis variable
                code += box_dict.get(option2, '')
        elif "Histogram" in plot_type:
            code += "H"
            code += jvc_dict.get(option1, '')
        elif "JV Curve" in plot_type:
            code += cur_dict.get(option1, '')
        
        if code:
            new_list.append(code)
            
    return new_list

class PlotManager:
    """Manages all plotting operations for JV analysis"""
    
    def __init__(self):
        self.plot_output_path = ""
        self.font_size_axis = 15  # Default font size for axis labels
        self.font_size_title = 16  # Default font size for titles
        self.font_size_legend = 10  # Default font size for legend
        # REMOVED: No more FIXED_CATEGORY_COLORS - only use selected color scheme
    
    def set_output_path(self, path):
        self.plot_output_path = path
    
    def set_font_sizes(self, axis_size=None, title_size=None, legend_size=None):
        """Set font sizes for plots"""
        if axis_size is not None:
            self.font_size_axis = axis_size
        if title_size is not None:
            self.font_size_title = title_size
        if legend_size is not None:
            self.font_size_legend = legend_size
    
    def apply_font_sizes_to_axes(self, fig):
        """Apply current font size settings to a figure's axes"""
        fig.update_xaxes(titlefont=dict(size=self.font_size_axis), tickfont=dict(size=self.font_size_axis))
        fig.update_yaxes(titlefont=dict(size=self.font_size_axis), tickfont=dict(size=self.font_size_axis))
        return fig

    def _mask_boundary_zero_point(self, voltage_values, current_values, atol=1e-12):
        """Remove only boundary (0,0) artifacts from JV arrays.

        Keeps valid inner (0,0) points untouched and only removes the first and/or
        last point if both voltage and current are approximately zero.
        """
        v = np.asarray(voltage_values, dtype=float)
        c = np.asarray(current_values, dtype=float)

        if v.size == 0 or c.size == 0:
            return [], []

        n = min(len(v), len(c))
        v = v[:n]
        c = c[:n]

        valid_mask = ~(np.isnan(v) | np.isnan(c))
        v = v[valid_mask]
        c = c[valid_mask]

        if len(v) == 0:
            return [], []

        if len(v) > 1 and np.isclose(v[0], 0.0, atol=atol) and np.isclose(c[0], 0.0, atol=atol):
            v = v[1:]
            c = c[1:]

        if len(v) > 1 and np.isclose(v[-1], 0.0, atol=atol) and np.isclose(c[-1], 0.0, atol=atol):
            v = v[:-1]
            c = c[:-1]

        return v.tolist(), c.tolist()

    def _extract_rgb_from_color(self, color_string):
        """Extract RGB values from color string"""
        if 'rgba(' in color_string:
            rgba_values = color_string.replace('rgba(', '').replace(')', '').split(',')
            return int(rgba_values[0]), int(rgba_values[1]), int(rgba_values[2]), float(rgba_values[3])
        elif color_string.startswith('#'):
            hex_color = color_string.lstrip('#')
            if len(hex_color) == 6:
                return int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16), 0.7
        return 93, 164, 214, 0.7  # Default fallback

    def _create_matching_curves_data(self, jv_data, curves_data):
        """Create curves data that matches specific JV measurements EXACTLY including status"""
        if jv_data.empty:
            return curves_data.iloc[0:0].copy()  # Return empty DataFrame with same structure
        
        # Check if status field exists in both datasets
        has_status_jv = 'status' in jv_data.columns
        has_status_curves = 'status' in curves_data.columns
        
        # Use sample_id for precise matching if available
        if 'sample_id' in jv_data.columns and 'sample_id' in curves_data.columns:
            print(f"  Using sample_id for precise matching")
            
            # Create set of exact measurement combinations from JV data
            jv_combinations = set()
            duplicate_combinations = []
        
            for _, row in jv_data.iterrows():
                if has_status_jv and has_status_curves:
                    # Use 5-field matching including status
                    combination = (row['sample_id'], row['cell'], row['direction'], row['ilum'], row['status'])
                else:
                    # Use 4-field matching without status
                    combination = (row['sample_id'], row['cell'], row['direction'], row['ilum'])
                    
                if combination in jv_combinations:
                    duplicate_combinations.append(combination)
                jv_combinations.add(combination)
        
            print(f"  JV combinations to match: {len(jv_combinations)}")
            print(f"  Total JV records: {len(jv_data)}")
            print(f"  Duplicate combinations found: {len(duplicate_combinations)}")
        
            if len(duplicate_combinations) > 0:
                print(f"  Example duplicates: {duplicate_combinations[:3]}")
                # Show what makes these records different
                example_dup = duplicate_combinations[0] if duplicate_combinations else None
                if example_dup:
                    if has_status_jv and has_status_curves:
                        sample_id, cell, direction, ilum, status = example_dup
                        matching_records = jv_data[
                            (jv_data['sample_id'] == sample_id) & 
                            (jv_data['cell'] == cell) & 
                            (jv_data['direction'] == direction) & 
                            (jv_data['ilum'] == ilum) &
                            (jv_data['status'] == status)
                        ]
                    else:
                        sample_id, cell, direction, ilum = example_dup
                        matching_records = jv_data[
                            (jv_data['sample_id'] == sample_id) & 
                            (jv_data['cell'] == cell) & 
                            (jv_data['direction'] == direction) & 
                            (jv_data['ilum'] == ilum)
                        ]
                    print(f"  Records with same combination:")
                    for _, record in matching_records.iterrows():
                        print(f"    PCE: {record['PCE(%)']:.2f}%, Status: {record.get('status', 'N/A')}")
            
            # Filter curves using exact matching
            def should_include_curve(curve_row):
                if has_status_jv and has_status_curves:
                    combination = (curve_row['sample_id'], curve_row['cell'], curve_row['direction'], curve_row['ilum'], curve_row['status'])
                else:
                    combination = (curve_row['sample_id'], curve_row['cell'], curve_row['direction'], curve_row['ilum'])
                return combination in jv_combinations
            
            matching_curves = curves_data[curves_data.apply(should_include_curve, axis=1)].copy()
            
        else:
            # Fallback to sample name matching
            print(f"  Using sample name matching (fallback)")
            
            jv_combinations = set()
            for _, row in jv_data.iterrows():
                combination = (row['sample'], row['cell'], row['direction'], row['ilum'])
                jv_combinations.add(combination)
            
            def should_include_curve(curve_row):
                combination = (curve_row['sample'], curve_row['cell'], curve_row['direction'], curve_row['ilum'])
                return combination in jv_combinations
            
            matching_curves = curves_data[curves_data.apply(should_include_curve, axis=1)].copy()
        
        print(f"  Matching curve records found: {len(matching_curves)}")
        print(f"  Expected ratio curves/JV: {len(matching_curves)/len(jv_data):.1f}x (should be ~2x)")
        
        # Additional verification: check if we're getting the right samples
        if not matching_curves.empty:
            unique_curve_devices = set()
            for _, row in matching_curves.iterrows():
                device = f"{row['sample']}_{row['cell']}"
                unique_curve_devices.add(device)
            
            unique_jv_devices = set()
            for _, row in jv_data.iterrows():
                device = f"{row['sample']}_{row['cell']}"
                unique_jv_devices.add(device)
            
            print(f"  Unique devices in curves: {len(unique_curve_devices)}")
            print(f"  Unique devices in JV: {len(unique_jv_devices)}")
            print(f"  Device overlap: {len(unique_curve_devices.intersection(unique_jv_devices))}")
            
            # Show some examples to verify correctness
            if len(unique_curve_devices) > 0:
                curve_examples = list(unique_curve_devices)[:3]
                jv_examples = list(unique_jv_devices)[:3]
                print(f"  Curve device examples: {curve_examples}")
                print(f"  JV device examples: {jv_examples}")
        
        return matching_curves
    
    def create_jv_best_per_condition_plot(self, jvc_data, curves_data, colors=None):
        """Plot JV curves for the SINGLE best measurement per condition/variable"""
        
        if jvc_data.empty:
            fig = go.Figure()
            fig.update_layout(title="No data available")
            return fig, "JV_best_per_condition.html"
        
        # Check if condition column exists
        if 'condition' not in jvc_data.columns:
            print("Warning: No 'condition' column found. Using sample grouping instead.")
            grouping_col = 'sample'
        else:
            grouping_col = 'condition'
        
        fig = go.Figure()
        
        # Calculate dynamic axis ranges based on data
        max_voc = jvc_data['Voc(V)'].max() if 'Voc(V)' in jvc_data.columns else 1.2
        x_max = (math.ceil(max_voc * 10) / 10) + 0.1
        
        # Add axis lines with dynamic range
        fig.add_shape(type="line", x0=-0.2, y0=0, x1=x_max, y1=0, line=dict(color="gray", width=2))
        fig.add_shape(type="line", x0=0, y0=-5, x1=0, y1=25, line=dict(color="gray", width=2))
        
        if colors is None:
            colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
        
        # CRITICAL CHANGE: Get only the SINGLE best measurement per condition (not per sample+condition)
        # This will automatically pick the best direction (Forward or Reverse)
        best_per_condition = jvc_data.loc[jvc_data.groupby(grouping_col)['PCE(%)'].idxmax()]
        
        # CRITICAL: Calculate legend space based on number of conditions
        num_conditions = len(best_per_condition)
        
        # Calculate how many rows the legend will need (assuming 3 items per row in horizontal mode)
        items_per_row = 3
        num_legend_rows = (num_conditions + items_per_row - 1) // items_per_row  # Ceiling division
        
        # Calculate required bottom margin: base + (rows * pixels per row)
        base_margin = 80
        pixels_per_legend_row = 30  # Each legend row needs about 30 pixels
        required_bottom_margin = base_margin + (num_legend_rows * pixels_per_legend_row)
        
        # Calculate y position for legend (further down with more items)
        # Base position + additional offset for extra rows
        base_y_position = -0.35
        additional_y_offset = -0.05 * (num_legend_rows - 1)  # Push down more for each additional row
        legend_y_position = base_y_position + additional_y_offset
        
        print(f"Found {num_conditions} conditions with best measurements:")
        print(f"   Legend will use {num_legend_rows} rows")
        print(f"   Required bottom margin: {required_bottom_margin}px")
        print(f"   Legend y position: {legend_y_position}")
        
        for i, (_, best_row) in enumerate(best_per_condition.iterrows()):
            sample = best_row['sample']
            cell = best_row['cell']
            condition = best_row.get(grouping_col, 'Unknown')
            pce = best_row['PCE(%)']
            direction = best_row['direction']
            sample_id = best_row['sample_id']
            ilum = best_row['ilum']
            
            print(f"  • {condition}: {sample}_{cell} ({direction}, PCE: {pce:.2f}%)")
            
            device_curves = curves_data[
                (curves_data['sample_id'] == sample_id) & 
                (curves_data['cell'] == cell) &
                (curves_data['direction'] == direction) &
                (curves_data['ilum'] == ilum)
            ]
            
            if device_curves.empty:
                print(f"    Warning: No curves found for {condition}")
                continue
            
            # Process voltage and current measurements
            voltage_measurements = {}
            current_measurements = {}
            
            for _, curve_row in device_curves.iterrows():
                curve_direction = curve_row['direction']
                variable_type = curve_row['variable']
                
                # Extract data values
                data_values = []
                for col in curve_row.index[8:]:
                    try:
                        val = float(curve_row[col])
                        if not pd.isna(val):
                            data_values.append(val)
                    except (ValueError, TypeError):
                        continue
                
                key = f"{curve_direction}"
                
                if variable_type == "Voltage (V)":
                    voltage_measurements[key] = data_values
                elif variable_type == "Current Density(mA/cm2)":
                    current_measurements[key] = data_values
            
            # Plot curves for this measurement
            base_color = colors[i % len(colors)]
            r, g, b, alpha = self._extract_rgb_from_color(base_color)
            
            for key in voltage_measurements.keys():
                if key in current_measurements:
                    voltage_values = voltage_measurements[key]
                    current_values = current_measurements[key]
                    curve_direction = key
                    
                    if len(voltage_values) > 0 and len(current_values) > 0:
                        voltage_values, current_values = self._mask_boundary_zero_point(voltage_values, current_values)
                        if len(voltage_values) == 0 or len(current_values) == 0:
                            continue

                        line_color = base_color
                        line_style = 'solid'
                        marker_symbol = 'circle'
                        
                        trace_name = f"{condition} ({curve_direction}, {pce:.1f}%)"
                        
                        fig.add_trace(go.Scatter(
                            x=voltage_values,
                            y=current_values,
                            mode='lines+markers',
                            line=dict(dash=line_style, color=line_color, width=2),
                            marker=dict(size=5, color=line_color, symbol=marker_symbol),
                            name=trace_name,
                            legendgroup=f"condition_{i}",
                            showlegend=True
                        ))
        
        # Update layout with DRAGGABLE legend
        fig.update_layout(
            title=f"JV Curves - Best Measurement per {grouping_col.title()}",
            xaxis_title='Voltage [V]',
            yaxis_title='Current Density [mA/cm²]',
            xaxis=dict(range=[-0.2, x_max]),
            yaxis=dict(range=[-5, 25]),
            template="plotly_white",
            legend=dict(
                x=0.02,  # Start position left inside plot
                y=0.98,  # Start position top
                xanchor="left",
                yanchor="top",
                bgcolor="rgba(255,255,255,0.85)",  # Semi-transparent background
                bordercolor="black",
                borderwidth=1,
                font=dict(size=10)  # Slightly smaller font to save space
            ),
            showlegend=True,
            margin=dict(l=80, r=50, t=80, b=80),  # Normal margins
            width=1600,  # 16:10 ratio width
            height=1000,  # 16:10 ratio height
        )
        
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
        
        return fig, "JV_best_per_condition.html"

    def create_jv_best_device_plot(self, jvc_data, curves_data, colors=None):
        """Plot JV curves for the best device (highest PCE) with all available measurements"""
        
        voltage_rows = curves_data[curves_data["variable"] == "Voltage (V)"]
        if not voltage_rows.empty:
            first_v_row = voltage_rows.iloc[0]        
        
        # Find best device (sample + cell combination with highest PCE)
        best_idx = jvc_data["PCE(%)"].idxmax()
        best_sample = jvc_data.loc[best_idx]["sample"]
        best_cell = jvc_data.loc[best_idx]["cell"]
        best_pce = jvc_data.loc[best_idx]["PCE(%)"]
        
        # Get ALL measurements for this sample+cell combination (not just best measurement)
        best_device_jv = jvc_data[(jvc_data["sample"] == best_sample) & (jvc_data["cell"] == best_cell)]
        best_device_curves = curves_data[(curves_data["sample"] == best_sample) & (curves_data["cell"] == best_cell)]

        all_matching_curves = curves_data[curves_data["sample"] == best_sample]
        
        if len(all_matching_curves) > 0:
            device_curves = all_matching_curves[all_matching_curves["cell"] == best_cell]
        
        # Get ALL measurements for this sample+cell combination (not just best measurement)
        best_device_jv = jvc_data[(jvc_data["sample"] == best_sample) & (jvc_data["cell"] == best_cell)]
        best_device_curves = curves_data[(curves_data["sample"] == best_sample) & (curves_data["cell"] == best_cell)]

        if not best_device_curves.empty:
            voltage_curves = best_device_curves[best_device_curves["variable"] == "Voltage (V)"]
            current_curves = best_device_curves[best_device_curves["variable"] == "Current Density(mA/cm2)"]
        
        if best_device_curves.empty:
            print(f"No curve data found for best device")
            return None, ""
        
        # Organize curves by status, direction
        voltage_curves = best_device_curves[best_device_curves["variable"] == "Voltage (V)"]
        current_curves = best_device_curves[best_device_curves["variable"] == "Current Density(mA/cm2)"]

        fig = go.Figure()
        
        # Calculate dynamic axis ranges based on data
        max_voc = jvc_data['Voc(V)'].max() if 'Voc(V)' in jvc_data.columns else 1.2
        x_max = (math.ceil(max_voc * 10) / 10) + 0.1
        
        # Add axis lines with dynamic range
        fig.add_shape(type="line", x0=-0.2, y0=0, x1=x_max, y1=0, line=dict(color="gray", width=2))
        fig.add_shape(type="line", x0=0, y0=-5, x1=0, y1=25, line=dict(color="gray", width=2))
        
        if colors is None:
            colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']

        voltage_measurements = {}
        current_measurements = {}
        
        for idx, curve_row in best_device_curves.iterrows():
            direction = curve_row['direction']
            variable_type = curve_row['variable']
            
            # Extract the actual data values
            data_values = []
            for col in curve_row.index[8:]:
                try:
                    val = float(curve_row[col])
                    if not pd.isna(val):
                        data_values.append(val)
                except (ValueError, TypeError):
                    continue

            # Group by direction
            key = f"{direction}"
            
            # Store voltage and current data in lists to handle multiple measurements
            if variable_type == "Voltage (V)":
                if key not in voltage_measurements:
                    voltage_measurements[key] = []
                voltage_measurements[key].append(data_values)
            elif variable_type == "Current Density(mA/cm2)":
                if key not in current_measurements:
                    current_measurements[key] = []
                current_measurements[key].append(data_values)
        
        # Create proper measurement pairs by matching voltage and current data
        measurement_pairs = []
        voltage_list = []
        current_list = []
        
        # Collect all voltage and current measurements with their metadata
        for key in voltage_measurements.keys():
            direction = key.split('_', 1)
            for i, voltage_array in enumerate(voltage_measurements[key]):
                voltage_list.append({
                    'data': voltage_array,
                    'direction': direction,
                    'measurement_id': f"{direction}_{i}"
                })
        
        for key in current_measurements.keys():
            direction = key.split('_', 1)
            for i, current_array in enumerate(current_measurements[key]):
                current_list.append({
                    'data': current_array,
                    'direction': direction,
                    'measurement_id': f"{direction}_{i}"
                })
        
        # Match voltage and current by measurement_id
        for v_item in voltage_list:
            for c_item in current_list:
                if v_item['measurement_id'] == c_item['measurement_id']:
                    measurement_pairs.append({
                        'voltage': v_item['data'],
                        'current': c_item['data'],
                        'direction': v_item['direction'],
                        'measurement_index': int(v_item['measurement_id'].split('_')[1])
                    })
                    break
        
        # Sort pairs to ensure consistent ordering
        measurement_pairs.sort(key=lambda x: (x['measurement_index'], x['direction']))
        
        # Add axis lines with extended range
        fig.add_shape(type="line", x0=-2, y0=0, x1=10, y1=0, line=dict(color="gray", width=2))
        fig.add_shape(type="line", x0=0, y0=-1000, x1=0, y1=300, line=dict(color="gray", width=2))
        
        # Group pairs: each measurement index gets one color, shared between Forward and Reverse
        unique_measurements = {}
        for pair in measurement_pairs:
            idx = pair['measurement_index']
            if idx not in unique_measurements:
                unique_measurements[idx] = []
            unique_measurements[idx].append(pair)
        
        # Plot each measurement pair with proper color pairing
        for measurement_idx, pairs in unique_measurements.items():
            # Get base color from color scheme
            color_index = measurement_idx % len(colors)
            base_color = colors[color_index]
            
            # Extract RGB values from rgba color string
            r, g, b, alpha = self._extract_rgb_from_color(base_color)
            
            # Plot both reverse and forward for this measurement
            for pair in pairs:
                voltage_values = pair['voltage']
                current_values = pair['current']
                direction = pair['direction']
                
                if len(voltage_values) > 0 and len(current_values) > 0:
                    voltage_values, current_values = self._mask_boundary_zero_point(voltage_values, current_values)
                    if len(voltage_values) == 0 or len(current_values) == 0:
                        continue

                    if direction == 'Reverse':
                        # Forward gets 50% lighter color with solid line and crosses
                        light_r = min(255, int(r + (255 - r) * 0.5))
                        light_g = min(255, int(g + (255 - g) * 0.5))
                        light_b = min(255, int(b + (255 - b) * 0.5))
                        line_color = f'rgba({light_r}, {light_g}, {light_b}, {alpha})'
                        line_style = 'dash'
                        marker_symbol = 'circle'
                    else:
                        # Reverse gets the main color with dashed line and dots
                        line_color = base_color
                        line_style = 'solid'
                        marker_symbol = 'x'
                    
                    # Create trace name
                    trace_name = f"{direction} #{measurement_idx + 1}"
                    
                    fig.add_trace(go.Scatter(
                        x=voltage_values,
                        y=current_values,
                        mode='lines+markers',
                        line=dict(dash=line_style, color=line_color, width=2),
                        marker=dict(size=6, color=line_color, symbol=marker_symbol),
                        name=trace_name,
                        # legendgroup=f"measurement_{measurement_idx}",
                        showlegend=True
                    ))
                
        # Count number of traces (measurements) for dynamic spacing - ADD THIS BEFORE fig.update_layout
        num_traces = len(unique_measurements) * 2  # Each measurement has Forward and Reverse
        
        # Calculate legend space
        items_per_row = 4  # Slightly more items per row for device plot
        num_legend_rows = (num_traces + items_per_row - 1) // items_per_row
        
        base_margin = 80
        pixels_per_legend_row = 30
        required_bottom_margin = base_margin + (num_legend_rows * pixels_per_legend_row)
        
        base_y_position = -0.35
        additional_y_offset = -0.05 * (num_legend_rows - 1)
        legend_y_position = base_y_position + additional_y_offset
        
        # Update layout
        fig.update_layout(
            title=dict(text=f"JV Curves - Best Device ({best_sample} [Cell {best_cell}])", font=dict(size=self.font_size_title)),
            xaxis_title='Voltage [V]',
            yaxis_title='Current Density [mA/cm²]',
            xaxis=dict(range=[-0.2, x_max], titlefont=dict(size=self.font_size_axis), tickfont=dict(size=self.font_size_axis)),
            yaxis=dict(range=[-5, 25], titlefont=dict(size=self.font_size_axis), tickfont=dict(size=self.font_size_axis)),
            template="plotly_white",
            legend=dict(
                x=0.02,  # Start left inside
                y=0.98,  # Start top
                xanchor="left",
                yanchor="top",
                bgcolor="rgba(255,255,255,0.85)",
                bordercolor="black",
                borderwidth=1,
                font=dict(size=self.font_size_legend)
            ),
            showlegend=True,
            margin=dict(l=80, r=50, t=80, b=80),
            width=1600,  # 16:10 ratio width
            height=1000,  # 16:10 ratio height
        )
        
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
        
        sample_name = f"JV_best_device_{best_sample} (Cell {best_cell}).html"
        return fig, sample_name

    def create_jv_best_per_condition_plot(self, jvc_data, curves_data, colors=None):
        """Plot JV curves for the SINGLE best measurement per condition/variable"""
        
        if jvc_data.empty:
            fig = go.Figure()
            fig.update_layout(title="No data available")
            return fig, "JV_best_per_condition.html"
        
        # Check if condition column exists
        if 'condition' not in jvc_data.columns:
            print("Warning: No 'condition' column found. Using sample grouping instead.")
            grouping_col = 'sample'
        else:
            grouping_col = 'condition'
        
        fig = go.Figure()
        
        # Calculate dynamic axis ranges based on data
        max_voc = jvc_data['Voc(V)'].max() if 'Voc(V)' in jvc_data.columns else 1.2
        x_max = (math.ceil(max_voc * 10) / 10) + 0.1
        
        # Add axis lines with dynamic range
        fig.add_shape(type="line", x0=-0.2, y0=0, x1=x_max, y1=0, line=dict(color="gray", width=2))
        fig.add_shape(type="line", x0=0, y0=-5, x1=0, y1=25, line=dict(color="gray", width=2))
        
        if colors is None:
            colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
        
        # CRITICAL CHANGE: Get only the SINGLE best measurement per condition (not per sample+condition)
        # This will automatically pick the best direction (Forward or Reverse)
        best_per_condition = jvc_data.loc[jvc_data.groupby(grouping_col)['PCE(%)'].idxmax()]
        
        # CRITICAL: Calculate legend space based on number of conditions
        num_conditions = len(best_per_condition)
        
        # Calculate how many rows the legend will need (assuming 3 items per row in horizontal mode)
        items_per_row = 3
        num_legend_rows = (num_conditions + items_per_row - 1) // items_per_row  # Ceiling division
        
        # Calculate required bottom margin: base + (rows * pixels per row)
        base_margin = 80
        pixels_per_legend_row = 30  # Each legend row needs about 30 pixels
        required_bottom_margin = base_margin + (num_legend_rows * pixels_per_legend_row)
        
        # Calculate y position for legend (further down with more items)
        # Base position + additional offset for extra rows
        base_y_position = -0.35
        additional_y_offset = -0.05 * (num_legend_rows - 1)  # Push down more for each additional row
        legend_y_position = base_y_position + additional_y_offset
        
        print(f"Found {num_conditions} conditions with best measurements:")
        print(f"   Legend will use {num_legend_rows} rows")
        print(f"   Required bottom margin: {required_bottom_margin}px")
        print(f"   Legend y position: {legend_y_position}")
        
        for i, (_, best_row) in enumerate(best_per_condition.iterrows()):
            sample = best_row['sample']
            cell = best_row['cell']
            condition = best_row.get(grouping_col, 'Unknown')
            pce = best_row['PCE(%)']
            direction = best_row['direction']  # ADD: Get the direction of the best measurement
            sample_id = best_row['sample_id']
            ilum = best_row['ilum']
            
            print(f"  • {condition}: {sample}_{cell} ({direction}, PCE: {pce:.2f}%)")
            
            device_curves = curves_data[
                (curves_data['sample_id'] == sample_id) & 
                (curves_data['cell'] == cell) &
                (curves_data['direction'] == direction) &  # FIX: Changed from && to &
                (curves_data['ilum'] == ilum)
            ]
            
            if device_curves.empty:
                print(f"    Warning: No curves found for {condition}")
                continue
            
            # Process voltage and current measurements
            voltage_measurements = {}
            current_measurements = {}
            
            for _, curve_row in device_curves.iterrows():
                curve_direction = curve_row['direction']
                variable_type = curve_row['variable']
                
                # Extract data values
                data_values = []
                for col in curve_row.index[8:]:
                    try:
                        val = float(curve_row[col])
                        if not pd.isna(val):
                            data_values.append(val)
                    except (ValueError, TypeError):
                        continue
                
                key = f"{curve_direction}"
                
                if variable_type == "Voltage (V)":
                    voltage_measurements[key] = data_values
                elif variable_type == "Current Density(mA/cm2)":
                    current_measurements[key] = data_values
            
            # Plot curves for this measurement (should be only one direction now)
            base_color = colors[i % len(colors)]
            r, g, b, alpha = self._extract_rgb_from_color(base_color)
            
            for key in voltage_measurements.keys():
                if key in current_measurements:
                    voltage_values = voltage_measurements[key]
                    current_values = current_measurements[key]
                    curve_direction = key
                    
                    if len(voltage_values) > 0 and len(current_values) > 0:
                        voltage_values, current_values = self._mask_boundary_zero_point(voltage_values, current_values)
                        if len(voltage_values) == 0 or len(current_values) == 0:
                            continue

                        # Use solid line with circles for the best measurement
                        line_color = base_color
                        line_style = 'solid'
                        marker_symbol = 'circle'
                        
                        # CHANGE: Updated trace name to show which direction won
                        trace_name = f"{condition} ({curve_direction}, {pce:.1f}%)"
                        
                        fig.add_trace(go.Scatter(
                            x=voltage_values,
                            y=current_values,
                            mode='lines+markers',
                            line=dict(dash=line_style, color=line_color, width=2),
                            marker=dict(size=5, color=line_color, symbol=marker_symbol),
                            name=trace_name,
                            legendgroup=f"condition_{i}",
                            showlegend=True
                        ))
        
        # Update layout with DRAGGABLE legend
        fig.update_layout(
            title=dict(text=f"JV Curves - Best Measurement per {grouping_col.title()}", font=dict(size=self.font_size_title)),
            xaxis_title='Voltage [V]',
            yaxis_title='Current Density [mA/cm²]',
            xaxis=dict(range=[-0.2, x_max], titlefont=dict(size=self.font_size_axis), tickfont=dict(size=self.font_size_axis)),
            yaxis=dict(range=[-5, 25], titlefont=dict(size=self.font_size_axis), tickfont=dict(size=self.font_size_axis)),
            template="plotly_white",
            legend=dict(
                x=0.02,  # Start position left inside plot
                y=0.98,  # Start position top
                xanchor="left",
                yanchor="top",
                bgcolor="rgba(255,255,255,0.85)",  # Semi-transparent background
                bordercolor="black",
                borderwidth=1,
                font=dict(size=self.font_size_legend)  # Slightly smaller font to save space
            ),
            showlegend=True,
            margin=dict(l=80, r=50, t=80, b=80),  # Normal margins
            width=1600,  # 16:10 ratio width
            height=1000,  # 16:10 ratio height
        )
        
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
        
        return fig, "JV_best_per_condition.html"
    
    def create_jv_separated_by_cell_plot(self, jvc_data, curves_data, colors=None, plot_type="all"):
        """Create separate plots for each sample, showing all cells together"""
        
        # Filter out empty cells
        jvc_data = jvc_data[jvc_data['cell'].notna()]
        
        if jvc_data.empty:
            fig = go.Figure()
            fig.update_layout(title="No data available")
            return fig, "JV_separated_by_cell.html"
        
        # Group by sample and cell, count measurements
        grouped_data = jvc_data.groupby(['sample', 'cell']).size().reset_index(name='measurement_count')
        
        # Sort by measurement count (descending) and then by sample, cell
        sorted_grouped_data = grouped_data.sort_values(by=['measurement_count', 'sample', 'cell'], ascending=[False, True, True])
        
        # Get top N samples with most measurements
        top_n_samples = sorted_grouped_data.head(20)
        
        # Filter original data for these samples
        filtered_jvc_data = jvc_data[jvc_data.set_index(['sample', 'cell']).index.isin(top_n_samples.set_index(['sample', 'cell']).index)]
        
        # Unique devices in the filtered data
        unique_devices = filtered_jvc_data.groupby(['sample', 'cell']).size().reset_index()
        
        if len(unique_devices) == 0:
            print(f"No matching devices found for top samples")
            return None, "JV_separated_by_cell.html"
        
        fig_list = []
        fig_names = []
        
        # Create one figure per sample
        for (sample, cell), group_data in filtered_jvc_data.groupby(['sample', 'cell']):
            fig = go.Figure()
            
            # Calculate dynamic axis ranges for this sample
            max_voc = group_data['Voc(V)'].max() if 'Voc(V)' in group_data.columns else 1.2
            x_max = (math.ceil(max_voc * 10) / 10) + 0.1
            
            # Add axis lines with dynamic range
            fig.add_shape(type="line", x0=-0.2, y0=0, x1=x_max, y1=0, line=dict(color="gray", width=2))
            fig.add_shape(type="line", x0=0, y0=-5, x1=0, y1=25, line=dict(color="gray", width=2))
            
            if colors is None:
                colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
            
            # CRITICAL CHANGE: Plot all measurements for this device, showing all cells
            voltage_data = group_data[group_data['variable'] == "Voltage (V)"]
            current_data = group_data[group_data['variable'] == "Current Density(mA/cm2)"]
            
            # Ensure we have data for both voltage and current
            if voltage_data.empty or current_data.empty:
                print(f"Missing voltage or current data for {sample}_{cell}")
                continue
            
            # Match voltage and current data by index
            for idx in voltage_data.index.intersection(current_data.index):
                voltage_values = voltage_data.loc[idx, voltage_data.columns[8:]].values
                current_values = current_data.loc[idx, current_data.columns[8:]].values
                
                # Skip if no valid data
                if np.all(pd.isna(voltage_values)) or np.all(pd.isna(current_values)):
                    continue

                voltage_values, current_values = self._mask_boundary_zero_point(voltage_values, current_values)
                if len(voltage_values) == 0 or len(current_values) == 0:
                    continue
                
                # Group by direction
                direction = voltage_data.loc[idx, 'direction']
                
                # Base color for this sample+cell
                base_color = colors[len(fig.data) % len(colors)]
                
                # Add trace for this measurement
                fig.add_trace(go.Scatter(
                    x=voltage_values,
                    y=current_values,
                    mode='lines+markers',
                    line=dict(color=base_color, width=2),
                    marker=dict(size=6, color=base_color),
                    name=f"{sample}_{cell} ({direction})",
                    legendgroup=f"{sample}_{cell}",
                    showlegend=True
                ))
            
            # FIX: Define missing variables before using them
            base_margin = 80
            pixels_per_legend_row = 30
            
            # ADD: Calculate dynamic spacing AFTER all traces are added
            num_traces = len(fig.data)
            items_per_row = 3
            num_legend_rows = (num_traces + items_per_row - 1) // items_per_row
            required_bottom_margin = base_margin + (num_legend_rows * pixels_per_legend_row)
            legend_y_position = -0.35 + (-0.05 * (num_legend_rows - 1))
            
            # Update layout for this figure
            if plot_type == "working":
                fig.update_layout(
                    title=dict(text=f"JV Curves - Sample: {sample} (Working Cells Only)", font=dict(size=self.font_size_title)),
                    xaxis_title='Voltage [V]',
                    yaxis_title='Current Density [mA/cm²]',
                    xaxis=dict(range=[-0.2, x_max], titlefont=dict(size=self.font_size_axis), tickfont=dict(size=self.font_size_axis)),
                    yaxis=dict(range=[-5, 25], titlefont=dict(size=self.font_size_axis), tickfont=dict(size=self.font_size_axis)),
                    template="plotly_white",
                    legend=dict(
                        x=0.02,
                        y=0.98,
                        xanchor="left",
                        yanchor="top",
                        bgcolor="rgba(255,255,255,0.85)",
                        bordercolor="black",
                        borderwidth=1,
                        font=dict(size=self.font_size_legend)
                    ),
                    showlegend=True,
                    margin=dict(l=80, r=50, t=80, b=80),
                    width=1600,  # 16:10 ratio width
                    height=1000,  # 16:10 ratio height
                )
            else:
                fig.update_layout(
                    title=dict(text=f"JV Curves - Sample: {sample} (All Cells)", font=dict(size=self.font_size_title)),
                    xaxis_title='Voltage [V]',
                    yaxis_title='Current Density [mA/cm²]',
                    xaxis=dict(range=[-0.2, x_max], titlefont=dict(size=self.font_size_axis), tickfont=dict(size=self.font_size_axis)),
                    yaxis=dict(range=[-5, 25], titlefont=dict(size=self.font_size_axis), tickfont=dict(size=self.font_size_axis)),
                    template="plotly_white",
                    legend=dict(
                        x=0.02,
                        y=0.98,
                        xanchor="left",
                        yanchor="top",
                        bgcolor="rgba(255,255,255,0.85)",
                        bordercolor="black",
                        borderwidth=1,
                        font=dict(size=self.font_size_legend)
                    ),
                    showlegend=True,
                    margin=dict(l=80, r=50, t=80, b=80),
                    width=1600,  # 16:10 ratio width
                    height=1000,  # 16:10 ratio height
                )
        
            fig_list.append(fig)
            fig_names.append(f"JV_separated_by_cell_{sample}.html")
        
        return fig_list, fig_names

    def create_jv_separated_by_substrate_plot(self, jvc_data, curves_data, colors=None, plot_type="all"):
        """Create separate plots for each sample"""
        
        # Filter out empty cells
        jvc_data = jvc_data[jvc_data['cell'].notna()]
        
        if jvc_data.empty:
            fig = go.Figure()
            fig.update_layout(title="No data available")
            return fig, "JV_separated_by_substrate.html"
        
        # Group by sample and cell, count measurements
        grouped_data = jvc_data.groupby(['sample', 'cell']).size().reset_index(name='measurement_count')
        
        # Sort by measurement count (descending) and then by sample, cell
        sorted_grouped_data = grouped_data.sort_values(by=['measurement_count', 'sample', 'cell'], ascending=[False, True, True])
        
        # Get top N samples with most measurements
        top_n_samples = sorted_grouped_data.head(20)
        
        # Filter original data for these samples
        filtered_jvc_data = jvc_data[jvc_data.set_index(['sample', 'cell']).index.isin(top_n_samples.set_index(['sample', 'cell']).index)]
        
        # Unique devices in the filtered data
        unique_devices = filtered_jvc_data.groupby(['sample', 'cell']).size().reset_index()
        
        if len(unique_devices) == 0:
            print(f"No matching devices found for top samples")
            return None, "JV_separated_by_substrate.html"
        
        fig_list = []
        fig_names = []
        
        # Create one figure per sample
        for (sample, cell), group_data in filtered_jvc_data.groupby(['sample', 'cell']):
            fig = go.Figure()
            
            # Calculate dynamic axis ranges for this substrate
            max_voc = group_data['Voc(V)'].max() if 'Voc(V)' in group_data.columns else 1.2
            x_max = (math.ceil(max_voc * 10) / 10) + 0.1
            
            # Add axis lines with dynamic range
            fig.add_shape(type="line", x0=-0.2, y0=0, x1=x_max, y1=0, line=dict(color="gray", width=2))
            fig.add_shape(type="line", x0=0, y0=-5, x1=0, y1=25, line=dict(color="gray", width=2))
            
            if colors is None:
                colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
            
            # CRITICAL CHANGE: Plot all measurements for this device, showing all cells
            voltage_data = group_data[group_data['variable'] == "Voltage (V)"]
            current_data = group_data[group_data['variable'] == "Current Density(mA/cm2)"]
            
            # Ensure we have data for both voltage and current
            if voltage_data.empty or current_data.empty:
                print(f"Missing voltage or current data for {sample}_{cell}")
                continue
            
            # Match voltage and current data by index
            for idx in voltage_data.index.intersection(current_data.index):
                voltage_values = voltage_data.loc[idx, voltage_data.columns[8:]].values
                current_values = current_data.loc[idx, current_data.columns[8:]].values
                
                # Skip if no valid data
                if np.all(pd.isna(voltage_values)) or np.all(pd.isna(current_values)):
                    continue

                voltage_values, current_values = self._mask_boundary_zero_point(voltage_values, current_values)
                if len(voltage_values) == 0 or len(current_values) == 0:
                    continue
                
                # Group by direction
                direction = voltage_data.loc[idx, 'direction']
                
                # Base color for this sample+cell
                base_color = colors[len(fig.data) % len(colors)]
                
                # Add trace for this measurement
                fig.add_trace(go.Scatter(
                    x=voltage_values,
                    y=current_values,
                    mode='lines+markers',
                    line=dict(color=base_color, width=2),
                    marker=dict(size=6, color=base_color),
                    name=f"{sample}_{cell} ({direction})",
                    legendgroup=f"{sample}_{cell}",
                    showlegend=True
                ))
            
            # FIX: Define missing variables before using them
            base_margin = 80
            pixels_per_legend_row = 30
            
            # ADD: Calculate dynamic spacing AFTER all traces are added
            num_traces = len(fig.data)
            items_per_row = 3
            num_legend_rows = (num_traces + items_per_row - 1) // items_per_row
            required_bottom_margin = base_margin + (num_legend_rows * pixels_per_legend_row)
            legend_y_position = -0.35 + (-0.05 * (num_legend_rows - 1))
            
            # Update layout for this figure
            if plot_type == "working":
                fig.update_layout(
                    title=dict(text=f"JV Curves - Sample: {sample} (Working Cells Only)", font=dict(size=self.font_size_title)),
                    xaxis_title='Voltage [V]',
                    yaxis_title='Current Density [mA/cm²]',
                    xaxis=dict(range=[-0.2, x_max], titlefont=dict(size=self.font_size_axis), tickfont=dict(size=self.font_size_axis)),
                    yaxis=dict(range=[-5, 25], titlefont=dict(size=self.font_size_axis), tickfont=dict(size=self.font_size_axis)),
                    template="plotly_white",
                    legend=dict(
                        x=0.02,
                        y=0.98,
                        xanchor="left",
                        yanchor="top",
                        bgcolor="rgba(255,255,255,0.85)",
                        bordercolor="black",
                        borderwidth=1,
                        font=dict(size=self.font_size_legend)
                    ),
                    showlegend=True,
                    margin=dict(l=80, r=50, t=80, b=80),
                    width=1600,  # 16:10 ratio width
                    height=1000,  # 16:10 ratio height
                )
            else:
                fig.update_layout(
                    title=dict(text=f"JV Curves - Sample: {sample} (All Cells)", font=dict(size=self.font_size_title)),
                    xaxis_title='Voltage [V]',
                    yaxis_title='Current Density [mA/cm²]',
                    xaxis=dict(range=[-0.2, x_max], titlefont=dict(size=self.font_size_axis), tickfont=dict(size=self.font_size_axis)),
                    yaxis=dict(range=[-5, 25], titlefont=dict(size=self.font_size_axis), tickfont=dict(size=self.font_size_axis)),
                    template="plotly_white",
                    legend=dict(
                        x=0.02,
                        y=0.98,
                        xanchor="left",
                        yanchor="top",
                        bgcolor="rgba(255,255,255,0.85)",
                        bordercolor="black",
                        borderwidth=1,
                        font=dict(size=self.font_size_legend)
                    ),
                    showlegend=True,
                    margin=dict(l=80, r=50, t=80, b=80),
                    width=1600,  # 16:10 ratio width
                    height=1000,  # 16:10 ratio height
                )
        
            fig_list.append(fig)
            fig_names.append(f"JV_separated_by_substrate_{sample}.html")
        
        return fig_list, fig_names

    def create_combined_boxplot_grid(self, data, var_x, other_data, data_type="data", colors=None, separate_scan_dir=False):
        """
        Create a 2x2 grid of boxplots showing PCE, FF, Jsc, and Voc together.
        var_x should be the GROUPING variable (e.g., 'condition' for "by Variable")
        """
        from plotly.subplots import make_subplots

        def _jsc_positive(value):
            return abs(value) if pd.notna(value) else value
        
        var_x_map = {
            'sample': 'sample', 'cell': 'cell', 'direction': 'direction',
            'ilum': 'ilum', 'batch': 'batch_for_plotting', 'condition': 'condition',
            'status': 'status'
        }
        
        name_x = var_x_map.get(var_x, var_x)
        if name_x not in data.columns:
            print(f"⚠️ Warning: Column {name_x} not found in data")
            return None, ""

        parameters = [
            {'name': 'PCE(%)', 'title': 'PCE', 'unit': '%'},
            {'name': 'FF(%)', 'title': 'Fill Factor', 'unit': '%'},
            {'name': 'Jsc(mA/cm2)', 'title': 'J<sub>sc</sub>', 'unit': 'mA/cm²'},
            {'name': 'Voc(V)', 'title': 'V<sub>oc</sub>', 'unit': 'V'}
        ]

        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=None,
            # SPACING CONTROLS:
            vertical_spacing=0.07,    # 👈 Distance between rows (0-1, default ~0.2)
            horizontal_spacing=0.06,  # 👈 Distance between columns (0-1, default ~0.2)
            specs=[[{"type": "box"}, {"type": "box"}],
                   [{"type": "box"}, {"type": "box"}]]
        )

        group_keys = sorted(data[name_x].unique())
        num_categories = len(group_keys)

        if separate_scan_dir and 'direction' in data.columns and name_x != 'direction':
            # Use one base color per category
            distributed_colors = self._get_intelligent_colors(group_keys, num_categories, color_scheme=colors)
        else:
            distributed_colors = self._get_intelligent_colors(group_keys, num_categories, color_scheme=colors)

        positions_map = [(1, 1), (1, 2), (2, 1), (2, 2)]

        for param_idx, param in enumerate(parameters):
            row, col = positions_map[param_idx]
            param_name = param['name']
            if param_name not in data.columns:
                print(f"⚠️ Warning: Parameter {param_name} not found in data")
                continue

            if separate_scan_dir and 'direction' in data.columns and name_x != 'direction':
                for i, key in enumerate(group_keys):
                    group_data = data[data[name_x] == key]
                    base_color = distributed_colors[i]
                    rev_color = self._darken_rgba(base_color, factor=0.25)
                    fwd_color = self._lighten_rgba(base_color, factor=0.25)
                    x_center = i
                    x_left = x_center - 0.2
                    x_right = x_center + 0.2

                    rev_data = group_data[group_data['direction'] == 'Reverse']
                    if not rev_data.empty:
                        # Prepare hover data for reverse
                        hover_data = []
                        for idx, row_data in rev_data.iterrows():
                            condition_val = row_data.get('condition', row_data.get(name_x, 'N/A'))
                            jsc_value = _jsc_positive(row_data.get('Jsc(mA/cm2)', 'N/A'))
                            hover_data.append([
                                condition_val,
                                row_data.get('direction', 'N/A'),
                                row_data.get('PCE(%)', 'N/A'),
                                row_data.get('FF(%)', 'N/A'),
                                jsc_value,
                                row_data.get('Voc(V)', 'N/A')
                            ])

                        y_values = rev_data[param_name].abs() if param_name == 'Jsc(mA/cm2)' else rev_data[param_name]
                        
                        fig.add_trace(go.Box(
                            y=y_values,
                            name=f"{key} [R]" if param_idx == 0 else "",
                            x=[x_left] * len(rev_data),
                            boxpoints='all',
                            pointpos=0,
                            jitter=0.5,
                            whiskerwidth=0.4,
                            marker=dict(size=4, opacity=0.7, color='rgba(0,0,0,0.7)'),
                            line=dict(width=1.5, color='black'),
                            fillcolor=rev_color,
                            boxmean=True,
                            width=0.3,
                            legendgroup=f"{key}_R",
                            showlegend=(param_idx == 0),
                            customdata=hover_data,
                            hovertemplate='<b>%{customdata[0]}</b><br>' +
                                        'Direction: %{customdata[1]}<br>' +
                                        'PCE: %{customdata[2]:.2f}%<br>' +
                                        'FF: %{customdata[3]:.2f}%<br>' +
                                        'Jsc: %{customdata[4]:.2f} mA/cm²<br>' +
                                        'Voc: %{customdata[5]:.3f} V<br>' +
                                        '<extra></extra>'
                        ), row=row, col=col)

                    fwd_data = group_data[group_data['direction'] == 'Forward']
                    if not fwd_data.empty:
                        # Prepare hover data for forward
                        hover_data = []
                        for idx, row_data in fwd_data.iterrows():
                            condition_val = row_data.get('condition', row_data.get(name_x, 'N/A'))
                            jsc_value = _jsc_positive(row_data.get('Jsc(mA/cm2)', 'N/A'))
                            hover_data.append([
                                condition_val,
                                row_data.get('direction', 'N/A'),
                                row_data.get('PCE(%)', 'N/A'),
                                row_data.get('FF(%)', 'N/A'),
                                jsc_value,
                                row_data.get('Voc(V)', 'N/A')
                            ])

                        y_values = fwd_data[param_name].abs() if param_name == 'Jsc(mA/cm2)' else fwd_data[param_name]
                        
                        fig.add_trace(go.Box(
                            y=y_values,
                            name=f"{key} [F]" if param_idx == 0 else "",
                            x=[x_right] * len(fwd_data),
                            boxpoints='all',
                            pointpos=0,
                            jitter=0.5,
                            whiskerwidth=0.4,
                            marker=dict(size=4, opacity=0.7, color='rgba(0,0,0,0.7)'),
                            line=dict(width=1.5, color='black'),
                            fillcolor=fwd_color,
                            boxmean=True,
                            width=0.3,
                            legendgroup=f"{key}_F",
                            showlegend=(param_idx == 0),
                            customdata=hover_data,
                            hovertemplate='<b>%{customdata[0]}</b><br>' +
                                        'Direction: %{customdata[1]}<br>' +
                                        'PCE: %{customdata[2]:.2f}%<br>' +
                                        'FF: %{customdata[3]:.2f}%<br>' +
                                        'Jsc: %{customdata[4]:.2f} mA/cm²<br>' +
                                        'Voc: %{customdata[5]:.3f} V<br>' +
                                        '<extra></extra>'
                        ), row=row, col=col)

                fig.update_xaxes(
                    tickmode='array',
                    tickvals=list(range(len(group_keys))),
                    ticktext=list(group_keys) if row == 2 else [""] * len(group_keys),
                    showgrid=True,
                    gridwidth=1,
                    gridcolor='lightgray',
                    row=row, col=col
                )
            else:
                if name_x == 'direction' and set(data[name_x].unique()) == {'Forward', 'Reverse'}:
                    group_keys_param = ['Reverse', 'Forward']
                else:
                    group_keys_param = group_keys

                for i, key in enumerate(group_keys_param):
                    group_data = data[data[name_x] == key]
                    if group_data.empty:
                        continue
                    
                    # Prepare hover data
                    hover_data = []
                    for idx, row_data in group_data.iterrows():
                        condition_val = row_data.get('condition', row_data.get(name_x, 'N/A'))
                        jsc_value = _jsc_positive(row_data.get('Jsc(mA/cm2)', 'N/A'))
                        hover_data.append([
                            condition_val,
                            row_data.get('direction', 'N/A'),
                            row_data.get('PCE(%)', 'N/A'),
                            row_data.get('FF(%)', 'N/A'),
                            jsc_value,
                            row_data.get('Voc(V)', 'N/A')
                        ])

                    y_values = group_data[param_name].abs() if param_name == 'Jsc(mA/cm2)' else group_data[param_name]
                    
                    color = distributed_colors[i]
                    fig.add_trace(go.Box(
                        y=y_values,
                        name=str(key) if param_idx == 0 else "",
                        x=[str(key)] * len(group_data),
                        boxpoints='all',
                        pointpos=0,
                        jitter=0.5,
                        whiskerwidth=0.4,
                        marker=dict(size=4, opacity=0.7, color='rgba(0,0,0,0.7)'),
                        line=dict(width=1.5, color='black'),
                        fillcolor=color,
                        boxmean=True,
                        width=0.8,
                        legendgroup=str(key),
                        showlegend=(param_idx == 0),
                        customdata=hover_data,
                        hovertemplate='<b>%{customdata[0]}</b><br>' +
                                    'Direction: %{customdata[1]}<br>' +
                                    'PCE: %{customdata[2]:.2f}%<br>' +
                                    'FF: %{customdata[3]:.2f}%<br>' +
                                    'Jsc: %{customdata[4]:.2f} mA/cm²<br>' +
                                    'Voc: %{customdata[5]:.3f} V<br>' +
                                    '<extra></extra>'
                    ), row=row, col=col)

                fig.update_xaxes(
                    ticktext=list(group_keys_param) if row == 2 else [""] * len(group_keys_param),
                    tickfont=dict(size=self.font_size_axis),
                    showgrid=True,
                    gridwidth=1,
                    gridcolor='lightgray',
                    row=row, col=col
                )

            # Per-subplot y-axis label with units
            y_axis_label = f"{param['title']} ({param['unit']})"
            fig.update_yaxes(
                title_text=y_axis_label,
                title_standoff=5,
                titlefont=dict(size=self.font_size_axis),
                tickfont=dict(size=self.font_size_axis),
                showgrid=True,
                gridwidth=1,
                gridcolor='lightgray',
                row=row, col=col
            )

        # Title and layout
        x_axis_display = name_x.replace('_', ' ').title()
        if name_x == 'condition':
            x_axis_display = 'Variable'
        elif name_x == 'batch_for_plotting':
            x_axis_display = 'Batch'

        title_text = f"Combined Performance Metrics by {x_axis_display}"
        if separate_scan_dir and 'direction' in data.columns and name_x != 'direction':
            title_text += " (Reverse/Forward split)"
        if data_type == "junk":
            title_text += " (Filtered Out Data)"

        fig.update_layout(
            title=dict(text=title_text, x=0.5, xanchor='center', font=dict(size=self.font_size_title, color='black')),
            template="plotly_white",
            showlegend=False,
            width=1600,   # 👈 CHANGED: 16:10 aspect ratio width
            height=1000,  # 👈 CHANGED: 16:10 aspect ratio height
            margin=dict(l=80, r=200, t=130, b=80),
            plot_bgcolor='white',
            paper_bgcolor='white',
            hovermode='closest'
        )
        
        # Apply font sizes to all axes
        fig.update_xaxes(titlefont=dict(size=self.font_size_axis), tickfont=dict(size=self.font_size_axis))
        fig.update_yaxes(titlefont=dict(size=self.font_size_axis), tickfont=dict(size=self.font_size_axis))

        # Tilt x-axis tick labels for many categories (bottom row only)
        if not separate_scan_dir and len(group_keys) > 4:
            fig.update_xaxes(tickangle=-45, row=2, col=1)
            fig.update_xaxes(tickangle=-45, row=2, col=2)

        fig_name = f"Boxplot_Combined_by_{name_x}"
        if separate_scan_dir:
            fig_name += "_separated"
        if data_type == "junk":
            fig_name += "_filtered_out"
        fig_name += ".html"

        return fig, fig_name

    def create_boxplot(self, data, var_x, var_y, other_data, data_type="data", colors=None, separate_scan_dir=False):
        """Create normal single-parameter boxplot"""
        def _jsc_positive(value):
            return abs(value) if pd.notna(value) else value

        var_y_map = {
            'voc': 'Voc(V)', 'jsc': 'Jsc(mA/cm2)', 'ff': 'FF(%)', 'pce': 'PCE(%)',
            'vmpp': 'V_mpp(V)', 'jmpp': 'J_mpp(mA/cm2)', 'pmpp': 'P_mpp(mW/cm2)',
            'rser': 'R_series(Ohmcm2)', 'rshu': 'R_shunt(Ohmcm2)'
        }
        var_x_map = {
            'sample': 'sample', 'cell': 'cell', 'direction': 'direction',
            'ilum': 'ilum', 'batch': 'batch_for_plotting', 'condition': 'condition',
            'status': 'status'
        }
        
        name_y = var_y_map.get(var_y, var_y)
        name_x = var_x_map.get(var_x, var_x)
        
        if name_y not in data.columns or name_x not in data.columns:
            print(f"⚠️ Warning: Column {name_y} or {name_x} not found")
            return None, "", None, "", ""

        fig = go.Figure()
        
        group_keys = sorted(data[name_x].unique())
        num_categories = len(group_keys)
        
        if separate_scan_dir and 'direction' in data.columns and name_x != 'direction':
            distributed_colors = self._get_intelligent_colors(group_keys, num_categories, color_scheme=colors)
        else:
            distributed_colors = self._get_intelligent_colors(group_keys, num_categories, color_scheme=colors)

        if separate_scan_dir and 'direction' in data.columns and name_x != 'direction':
            for i, key in enumerate(group_keys):
                group_data = data[data[name_x] == key]
                base_color = distributed_colors[i]
                rev_color = self._darken_rgba(base_color, factor=0.25)
                fwd_color = self._lighten_rgba(base_color, factor=0.25)
                x_center = i
                x_left = x_center - 0.2
                x_right = x_center + 0.2

                rev_data = group_data[group_data['direction'] == 'Reverse']
                if not rev_data.empty:
                    # Prepare hover data for reverse
                    hover_data = []
                    for idx, row_data in rev_data.iterrows():
                        condition_val = row_data.get('condition', row_data.get(name_x, 'N/A'))
                        jsc_value = _jsc_positive(row_data.get('Jsc(mA/cm2)', 'N/A'))
                        hover_data.append([
                            condition_val,
                            row_data.get('direction', 'N/A'),
                            row_data.get('PCE(%)', 'N/A'),
                            row_data.get('FF(%)', 'N/A'),
                            jsc_value,
                            row_data.get('Voc(V)', 'N/A')
                        ])

                    y_values = rev_data[name_y].abs() if name_y == 'Jsc(mA/cm2)' else rev_data[name_y]
                    
                    fig.add_trace(go.Box(
                        y=y_values,
                        name=f"{key} [R]",
                        x=[x_left] * len(rev_data),
                        boxpoints='all',
                        pointpos=0,
                        jitter=0.5,
                        whiskerwidth=0.4,
                        marker=dict(size=4, opacity=0.7, color='rgba(0,0,0,0.7)'),
                        line=dict(width=1.5, color='black'),
                        fillcolor=rev_color,
                        boxmean=True,
                        width=0.3,
                        legendgroup=f"{key}_R",
                        customdata=hover_data,
                        hovertemplate='<b>%{customdata[0]}</b><br>' +
                                    'Direction: %{customdata[1]}<br>' +
                                    'PCE: %{customdata[2]:.2f}%<br>' +
                                    'FF: %{customdata[3]:.2f}%<br>' +
                                    'Jsc: %{customdata[4]:.2f} mA/cm²<br>' +
                                    'Voc: %{customdata[5]:.3f} V<br>' +
                                    '<extra></extra>'
                    ))

                fwd_data = group_data[group_data['direction'] == 'Forward']
                if not fwd_data.empty:
                    # Prepare hover data for forward
                    hover_data = []
                    for idx, row_data in fwd_data.iterrows():
                        condition_val = row_data.get('condition', row_data.get(name_x, 'N/A'))
                        jsc_value = _jsc_positive(row_data.get('Jsc(mA/cm2)', 'N/A'))
                        hover_data.append([
                            condition_val,
                            row_data.get('direction', 'N/A'),
                            row_data.get('PCE(%)', 'N/A'),
                            row_data.get('FF(%)', 'N/A'),
                            jsc_value,
                            row_data.get('Voc(V)', 'N/A')
                        ])

                    y_values = fwd_data[name_y].abs() if name_y == 'Jsc(mA/cm2)' else fwd_data[name_y]
                    
                    fig.add_trace(go.Box(
                        y=y_values,
                        name=f"{key} [F]",
                        x=[x_right] * len(fwd_data),
                        boxpoints='all',
                        pointpos=0,
                        jitter=0.5,
                        whiskerwidth=0.4,
                        marker=dict(size=4, opacity=0.7, color='rgba(0,0,0,0.7)'),
                        line=dict(width=1.5, color='black'),
                        fillcolor=fwd_color,
                        boxmean=True,
                        width=0.3,
                        legendgroup=f"{key}_F",
                        customdata=hover_data,
                        hovertemplate='<b>%{customdata[0]}</b><br>' +
                                    'Direction: %{customdata[1]}<br>' +
                                    'PCE: %{customdata[2]:.2f}%<br>' +
                                    'FF: %{customdata[3]:.2f}%<br>' +
                                    'Jsc: %{customdata[4]:.2f} mA/cm²<br>' +
                                    'Voc: %{customdata[5]:.3f} V<br>' +
                                    '<extra></extra>'
                    ))

            fig.update_xaxes(
                tickmode='array',
                tickvals=list(range(len(group_keys))),
                ticktext=list(group_keys),
                showgrid=True,
                gridwidth=1,
                gridcolor='lightgray'
            )
        else:
            if name_x == 'direction' and set(data[name_x].unique()) == {'Forward', 'Reverse'}:
                group_keys = ['Reverse', 'Forward']

            for i, key in enumerate(group_keys):
                group_data = data[data[name_x] == key]
                if group_data.empty:
                    continue
                
                # Prepare hover data
                hover_data = []
                for idx, row_data in group_data.iterrows():
                    condition_val = row_data.get('condition', row_data.get(name_x, 'N/A'))
                    jsc_value = _jsc_positive(row_data.get('Jsc(mA/cm2)', 'N/A'))
                    hover_data.append([
                        condition_val,
                        row_data.get('direction', 'N/A'),
                        row_data.get('PCE(%)', 'N/A'),
                        row_data.get('FF(%)', 'N/A'),
                        jsc_value,
                        row_data.get('Voc(V)', 'N/A')
                    ])

                y_values = group_data[name_y].abs() if name_y == 'Jsc(mA/cm2)' else group_data[name_y]
                
                color = distributed_colors[i]
                fig.add_trace(go.Box(
                    y=y_values,
                    name=str(key),
                    x=[str(key)] * len(group_data),
                    boxpoints='all',
                    pointpos=0,
                    jitter=0.5,
                    whiskerwidth=0.4,
                    marker=dict(size=4, opacity=0.7, color='rgba(0,0,0,0.7)'),
                    line=dict(width=1.5, color='black'),
                    fillcolor=color,
                    boxmean=True,
                    width=0.8,
                    legendgroup=str(key),
                    customdata=hover_data,
                    hovertemplate='<b>%{customdata[0]}</b><br>' +
                                'Direction: %{customdata[1]}<br>' +
                                'PCE: %{customdata[2]:.2f}%<br>' +
                                'FF: %{customdata[3]:.2f}%<br>' +
                                'Jsc: %{customdata[4]:.2f} mA/cm²<br>' +
                                'Voc: %{customdata[5]:.3f} V<br>' +
                                '<extra></extra>'
                ))

            fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')

        # Title and layout
        x_axis_display = name_x.replace('_', ' ').title()
        if name_x == 'condition':
            x_axis_display = 'Variable'
        elif name_x == 'batch_for_plotting':
            x_axis_display = 'Batch'

        title_text = f"Boxplot of {x_axis_display} by {name_y}"
        if separate_scan_dir and 'direction' in data.columns and name_x != 'direction':
            title_text += " (Reverse/Forward split)"
        if data_type == "junk":
            title_text += " (Filtered Out Data)"

        fig.update_layout(
            title=dict(text=title_text, x=0.5, xanchor='center', font=dict(size=self.font_size_title, color='black')),
            template="plotly_white",
            showlegend=False,
            width=1600,   # 👈 CHANGED: 16:10 aspect ratio width  
            height=1000,  # 👈 CHANGED: 16:10 aspect ratio height
            margin=dict(l=80, r=200, t=130, b=80),
            plot_bgcolor='white',
            paper_bgcolor='white',
            hovermode='closest',
            xaxis=dict(titlefont=dict(size=self.font_size_axis), tickfont=dict(size=self.font_size_axis)),
            yaxis=dict(titlefont=dict(size=self.font_size_axis), tickfont=dict(size=self.font_size_axis))
        )

        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')

        fig_name = f"Boxplot_{name_y}_by_{name_x}"
        if separate_scan_dir:
            fig_name += "_separated"
        if data_type == "junk":
            fig_name += "_filtered_out"
        fig_name += ".html"

        return fig, fig_name, None, title_text, ""
    
    def _lighten_rgba(self, rgba_str, factor=0.3):
        r, g, b, a = self._extract_rgb_from_color(rgba_str)
        r = min(255, int(r + (255 - r) * factor))
        g = min(255, int(g + (255 - g) * factor))
        b = min(255, int(b + (255 - b) * factor))
        return f'rgba({r}, {g}, {b}, {a})'

    def _darken_rgba(self, rgba_str, factor=0.3):
        r, g, b, a = self._extract_rgb_from_color(rgba_str)
        r = max(0, int(r * (1 - factor)))
        g = max(0, int(g * (1 - factor)))
        b = max(0, int(b * (1 - factor)))
        return f'rgba({r}, {g}, {b}, {a})'

    def _get_intelligent_colors(self, categories, num_needed, color_scheme=None):
        """Distribute colors intelligently"""
        if color_scheme is None:
            color_scheme = ['rgba(93, 164, 214, 0.7)', 'rgba(255, 144, 14, 0.7)']
        if num_needed <= len(color_scheme):
            return color_scheme[:num_needed]
        colors = []
        for i in range(num_needed):
            colors.append(color_scheme[i % len(color_scheme)])
        return colors

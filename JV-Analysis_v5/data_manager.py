"""
Data Management Module
Handles all data loading, processing, filtering, and basic analysis operations.
"""

__author__ = "Edgar Nandayapa"
__institution__ = "Helmholtz-Zentrum Berlin"
__created__ = "August 2025"

import pandas as pd
import numpy as np
import os
import operator
import sys 

# Add parent directory for shared modules
parent_dir = os.path.dirname(os.getcwd())
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from api_calls import get_ids_in_batch, get_sample_description, get_all_JV
from error_handler import ErrorHandler


def extract_status_from_metadata(data, metadata):
    """
    Extract status from API metadata containing filename
    """
    import re
    
    # Look for filename in metadata
    filename_candidates = [
        metadata.get('mainfile', ''),
        metadata.get('upload_name', ''),
        metadata.get('entry_name', ''),
        metadata.get('filename', ''),
        # Also check in data if filename is stored there
        data.get('data_file', '') if isinstance(data, dict) else '',
    ]
    
    for candidate in filename_candidates:
        if candidate:
            # Extract status from filename like "HZB_JJ_1_B_C-8.JJ_1_B_8_L1_jv.jv.txt"
            status_match = re.search(r'_([LD]\d+)(?:_3min)?_', candidate)
            if not status_match:
                status_match = re.search(r'([LD]\d+)', candidate)
            
            if status_match:
                return status_match.group(1)
    
    return 'N/A'


class DataManager:
    """Main data management class for JV analysis application"""
    
    def __init__(self, auth_manager):
        self.auth_manager = auth_manager
        self.data = {}
        self.unique_vals = []
        self.filtered_data = None
        self.omitted_data = None
        self.filter_parameters = []
        # Store export data
        self.export_jvc_data = None
        self.export_curves_data = None
        # ADD: Cycle tracking
        self.has_cycle_data = False
        self.cycle_info = {}
    
    def load_batch_data(self, batch_ids, output_widget=None):
        """Load data from selected batch IDs"""
        self.data = {}
        
        if not self.auth_manager.is_authenticated():
            ErrorHandler.log_error("Authentication required", output_widget=output_widget)
            return False
        
        if not batch_ids:
            ErrorHandler.log_error("Please select at least one batch to load", output_widget=output_widget)
            return False
        
        try:
            if output_widget:
                with output_widget:
                    print("Loading Data")
                    print(f"Loading data for batch IDs: {batch_ids}")
            
            url = self.auth_manager.url
            token = self.auth_manager.current_token
            
            # Get sample IDs and descriptions
            sample_ids = get_ids_in_batch(url, token, batch_ids)  # <-- Holt Sample-IDs für Batch
            identifiers = get_sample_description(url, token, sample_ids)  # <-- Holt Variation/Description für Samples
            
            df_jvc, df_cur = self._process_jv_data_for_analysis(sample_ids, output_widget, batch_ids)
            
            # Store data
            self.data["jvc"] = pd.concat([self.data.get("jvc", pd.DataFrame()), df_jvc], ignore_index=True)
            self.data["curves"] = pd.concat([self.data.get("curves", pd.DataFrame()), df_cur], ignore_index=True)
            
            # Verify data was loaded successfully before processing
            if self.data["jvc"].empty:
                if output_widget:
                    with output_widget:
                        print("Error: No JV data was loaded successfully")
                return False
            
            # Process sample information
            self._process_sample_info(identifiers)

            if output_widget:
                with output_widget:
                    if not self.data['jvc'].empty:
                        best_main = self.data['jvc'].loc[self.data['jvc']["PCE(%)"].idxmax()]
            
            # Export data
            self._export_data(df_jvc, df_cur)

            # DIAGNOSTIC: Check data before and after processing
            if output_widget:
                with output_widget:
                    if not df_jvc.empty:
                        best_export = df_jvc.loc[df_jvc["PCE(%)"].idxmax()]
            
            # Find unique values
            self.unique_vals = self._find_unique_values()
            
            if output_widget:
                with output_widget:
                    print("Data Loaded Successfully!")
            
            return True
            
        except Exception as e:
            ErrorHandler.handle_data_loading_error(e, output_widget)
            return False
    
    def _process_jv_data_for_analysis(self, sample_ids, output_widget=None, batch_ids=None):
        """Process JV data for analysis from sample IDs with Cycle support"""
        columns_jvc = ['Voc(V)', 'Jsc(mA/cm2)', 'FF(%)', 'PCE(%)', 'V_mpp(V)', 'J_mpp(mA/cm2)',
                      'P_mpp(mW/cm2)', 'R_series(Ohmcm2)', 'R_shunt(Ohmcm2)', 'sample', 'batch',
                      'condition', 'cell', 'direction', 'ilum', 'status', 'sample_id',
                      'px_number', 'cycle_number']
        
        columns_cur = ['index', 'sample', 'batch', 'condition', 'variable', 'cell', 'direction', 
                      'ilum', 'sample_id', 'status', 'px_number', 'cycle_number']
        rows_jvc = []
        rows_cur = []
        
        # CRITICAL FIX: Initialize cycle tracking variables
        has_any_cycle_data = False
        cycle_counts = {}
        
        try:
            url = self.auth_manager.url
            token = self.auth_manager.current_token
            
            if output_widget:
                with output_widget:
                    print("Fetching JV data...")
            
            # Process each batch individually
            all_jvs = {}
            successful_batches = []
            failed_batches = []
            
            from api_calls import get_ids_in_batch
            
            for batch_id in batch_ids:
                try:
                    if output_widget:
                        with output_widget:
                            print(f"Processing batch: {batch_id}")
                    
                    batch_sample_ids = get_ids_in_batch(url, token, [batch_id])
                    batch_jvs = get_all_JV(url, token, batch_sample_ids)
                    
                    all_jvs.update(batch_jvs)
                    successful_batches.append(batch_id)
                    
                except KeyError as e:
                    if output_widget:
                        with output_widget:
                            print(f"⚠️ Skipping corrupted batch '{batch_id}' - missing field '{e.args[0]}'")
                    failed_batches.append(batch_id)
                    continue
                except Exception as e:
                    if output_widget:
                        with output_widget:
                            print(f"⚠️ Skipping problematic batch '{batch_id}' - {str(e)}")
                    failed_batches.append(batch_id)
                    continue
            
            if output_widget:
                with output_widget:
                    print(f"✅ Successfully processed {len(successful_batches)} batches")
                    if failed_batches:
                        print(f"⚠️ Skipped {len(failed_batches)} corrupted batches: {failed_batches}")
            
            if not all_jvs:
                if output_widget:
                    with output_widget:
                        print("❌ No valid JV data could be loaded from any batch")
                return pd.DataFrame(columns=columns_jvc), pd.DataFrame(columns=columns_cur)
            
            # Calculate max data points
            max_data_points = 0
            for sid in sample_ids:
                jv_res = all_jvs.get(sid, [])
                for jv_data, jv_md in jv_res:
                    if not jv_data or "jv_curve" not in jv_data or not jv_data["jv_curve"]:
                        continue
                    for c in jv_data["jv_curve"]:
                        max_data_points = max(max_data_points, len(c.get("voltage", [])), len(c.get("current_density", [])))
            
            for i in range(max_data_points):
                columns_cur.append(i)
            
            # DIAGNOSTIC: Print first few descriptions to see format
            if output_widget:
                with output_widget:
                    print(f"\n🔍 Checking JV data structure for cycle information...")
                    sample_count = 0
                    for sid in list(all_jvs.keys())[:3]:  # Check first 3 samples
                        jv_res = all_jvs.get(sid, [])
                        for jv_data, jv_md in jv_res[:2]:  # Check first 2 measurements per sample
                            if jv_data:
                                desc = jv_data.get("description", "")
                                print(f"   Sample {sid}: description = '{desc}'")
                                sample_count += 1
                                if sample_count >= 5:
                                    break
                        if sample_count >= 5:
                            break
            
            # Process data with ENHANCED cycle extraction
            for sid in sample_ids:
                jv_res = all_jvs.get(sid, [])
                
                for jv_data, jv_md in jv_res:
                    if not jv_data or "jv_curve" not in jv_data or not jv_data["jv_curve"]:
                        continue
                    
                    status = extract_status_from_metadata(jv_data, jv_md)
                    
                    # CRITICAL FIX: Extract from BOTH filename AND description
                    # Example description: "Notes from file name: px3Cycle_0"
                    # Example filename: "KIT_HaGu_20251113_K16_0_K16.px3Cycle_0.jv.csv"
                    filename = jv_data.get("data_file", "")
                    description = jv_data.get("description", "")
                    
                    import re
                    
                    # Strategy 1: Extract pixel number (px#)
                    px_number = None
                    
                    # Pattern 1: From description "Notes from file name: px3Cycle_0"
                    desc_match = re.search(r'px(\d+)Cycle', description, re.IGNORECASE)
                    if desc_match:
                        px_number = f"px{desc_match.group(1)}"
                    
                    # Pattern 2: From filename ".px3Cycle_0"
                    if not px_number:
                        file_match = re.search(r'\.px(\d+)Cycle', filename, re.IGNORECASE)
                        if file_match:
                            px_number = f"px{file_match.group(1)}"
                    
                    # Strategy 2: Extract cycle number (Cycle_#)
                    cycle_number = None
                    
                    # Pattern 1: From description "Notes from file name: px3Cycle_0"
                    desc_cycle_match = re.search(r'Cycle_(\d+)', description, re.IGNORECASE)
                    if desc_cycle_match:
                        cycle_number = int(desc_cycle_match.group(1))
                        has_any_cycle_data = True
                        
                        cycle_key = f"{sid}_{px_number}"
                        if cycle_key not in cycle_counts:
                            cycle_counts[cycle_key] = set()
                        cycle_counts[cycle_key].add(cycle_number)
                    
                    # Pattern 2: From filename "Cycle_0"
                    if cycle_number is None:
                        file_cycle_match = re.search(r'Cycle_(\d+)', filename, re.IGNORECASE)
                        if file_cycle_match:
                            cycle_number = int(file_cycle_match.group(1))
                            has_any_cycle_data = True
                            
                            cycle_key = f"{sid}_{px_number}"
                            if cycle_key not in cycle_counts:
                                cycle_counts[cycle_key] = set()
                            cycle_counts[cycle_key].add(cycle_number)
                    
                    # Process each JV curve
                    for c in jv_data["jv_curve"]:
                        file_name = os.path.join("../", jv_md["upload_id"], jv_data.get("data_file", "unknown"))
                        illum = "Dark" if "dark" in c.get("cell_name", "").lower() else "Light"
                        cell = c.get("cell_name", [""])[0] if c.get("cell_name") else ""
                        
                        # Direction detection
                        cell_name = c.get("cell_name", "")
                        curve_name = c.get("name", "")
                        
                        if "Current density [1]" in cell_name or "[1]" in cell_name:
                            direction = "Reverse"
                        elif "Current density [2]" in cell_name or "[2]" in cell_name:
                            direction = "Forward"
                        elif "forward scan" in curve_name.lower() or "forward" in curve_name.lower():
                            direction = "Forward"
                        elif "reverse scan" in curve_name.lower() or "reverse" in curve_name.lower():
                            direction = "Reverse"
                        elif "for" in cell_name.lower() or "fwd" in cell_name.lower():
                            direction = "Forward"
                        elif "rev" in cell_name.lower() or "back" in cell_name.lower():
                            direction = "Reverse"
                        else:
                            direction = "Reverse"  # Default

                        sample_clean = file_name.split('/')[-1].split('.')[0] if '/' in file_name else file_name
                        batch_id = file_name.split("/")[1] if "/" in file_name and len(file_name.split("/")) > 1 else "unknown"
                        
                        # Build JV row
                        row = [
                            c.get("open_circuit_voltage", 0),
                            -c.get("short_circuit_current_density", 0),
                            100 * c.get("fill_factor", 0),
                            c.get("efficiency", 0),
                            c.get("potential_at_maximum_power_point", 0),
                            -c.get("current_density_at_maximun_power_point", 0),
                            -c.get("potential_at_maximum_power_point", 0) * c.get("current_density_at_maximun_power_point", 0),
                            c.get("series_resistance", 0),
                            c.get("shunt_resistance", 0),
                            sample_clean,
                            batch_id,
                            "w",
                            cell,
                            direction,
                            illum,
                            status,
                            sid,
                            px_number,
                            cycle_number
                        ]
                        rows_jvc.append(row)
                        
                        # Build voltage row
                        row_v = [
                            "_".join(["Voltage (V)", cell, direction, illum]),
                            sample_clean,
                            batch_id,
                            "w",
                            "Voltage (V)",
                            cell,
                            direction,
                            illum,
                            sid,
                            status,
                            px_number,
                            cycle_number
                        ]
                        voltage_data = c.get("voltage", []) + [None] * (max_data_points - len(c.get("voltage", [])))
                        row_v.extend(voltage_data)
                        
                        # Build current row
                        row_j = [
                            "_".join(["Current Density(mA/cm2)", cell, direction, illum]),
                            sample_clean,
                            batch_id,
                            "w",
                            "Current Density(mA/cm2)",
                            cell,
                            direction,
                            illum,
                            sid,
                            status,
                            px_number,
                            cycle_number
                        ]
                        current_data = c.get("current_density", []) + [None] * (max_data_points - len(c.get("current_density", [])))
                        row_j.extend(current_data)
                        
                        rows_cur.append(row_v)
                        rows_cur.append(row_j)
        
        except Exception as e:
            if output_widget:
                with output_widget:
                    print(f"❌ Error processing JV data: {e}")
                    import traceback
                    traceback.print_exc()
            return pd.DataFrame(columns=columns_jvc), pd.DataFrame(columns=columns_cur)
        
        # Create DataFrames
        df_jvc = pd.DataFrame(rows_jvc, columns=columns_jvc)
        df_cur = pd.DataFrame(rows_cur, columns=columns_cur)
        
        # Store cycle information
        self.has_cycle_data = has_any_cycle_data
        self.cycle_info = cycle_counts
        
        # ENHANCED DIAGNOSTICS
        if output_widget:
            with output_widget:
                print(f"\n📊 Cycle Data Extraction Results:")
                print(f"   Total JV records created: {len(df_jvc)}")
                print(f"   Has cycle data flag: {has_any_cycle_data}")
                print(f"   Cycle combinations found: {len(cycle_counts)}")
                
                if 'cycle_number' in df_jvc.columns:
                    non_null_cycles = df_jvc['cycle_number'].notna().sum()
                    print(f"   Records with cycle_number: {non_null_cycles}")
                    
                    if non_null_cycles > 0:
                        unique_cycles = df_jvc['cycle_number'].dropna().unique()
                        print(f"   Unique cycle numbers: {sorted(unique_cycles.tolist())}")
                        print(f"   Sample values:")
                        sample_df = df_jvc[df_jvc['cycle_number'].notna()][['sample', 'px_number', 'cycle_number', 'PCE(%)']].head(3)
                        for _, row in sample_df.iterrows():
                            print(f"      {row['sample']} / {row['px_number']} / Cycle {int(row['cycle_number'])} / PCE: {row['PCE(%)']:.2f}%")
                    else:
                        print(f"   ⚠️ No cycle numbers were extracted!")
                        print(f"   This means either:")
                        print(f"      • No 'Cycle_' pattern found in descriptions")
                        print(f"      • Description format is different than expected")
        
        # Report detailed cycle statistics if found
        if output_widget and has_any_cycle_data and len(cycle_counts) > 0:
            with output_widget:
                print(f"\n✅ Cycle Information Successfully Detected:")
                print(f"   Found cycles in {len(cycle_counts)} sample-pixel combinations")
                
                total_measurements = sum(len(cycles) for cycles in cycle_counts.values())
                max_cycles_per_pixel = max(len(cycles) for cycles in cycle_counts.values())
                
                print(f"   Total unique cycle measurements: {total_measurements}")
                print(f"   Maximum cycles per pixel: {max_cycles_per_pixel}")
                
                print(f"\n   Cycle distribution examples:")
                for i, (key, cycles) in enumerate(list(cycle_counts.items())[:5]):
                    print(f"      {key}: {len(cycles)} cycles → {sorted(cycles)}")
        
        return df_jvc, df_cur
    
    def _create_matching_curves_from_filtered_jv(self, filtered_jv_df):
        """Create curves data that exactly matches filtered JV data using sample_id"""
        if not hasattr(self, 'data') or 'curves' not in self.data or filtered_jv_df.empty:
            return pd.DataFrame()
        
        # Get unique sample_id + cell + direction + ilum combinations from filtered JV
        filtered_combinations = set()
        for _, row in filtered_jv_df.iterrows():
            combination = (row['sample_id'], row['cell'], row['direction'], row['ilum'])
            filtered_combinations.add(combination)
        
        # Filter curves data to match exactly
        def should_include_curve(curve_row):
            if 'sample_id' not in curve_row:
                return False
            combination = (curve_row['sample_id'], curve_row['cell'], curve_row['direction'], curve_row['ilum'])
            return combination in filtered_combinations
        
        curves_data = self.data['curves']
        matching_curves = curves_data[curves_data.apply(should_include_curve, axis=1)].copy()
        
        return matching_curves
    
    def _process_sample_info(self, identifiers):
        """Process sample information and create identifiers with enhanced deduplication"""
        if "jvc" not in self.data or self.data["jvc"].empty:
            print("Warning: No JV data available for processing sample info")
            return
        
        if "sample" not in self.data["jvc"].columns:
            print("Warning: 'sample' column missing from JV data")
            print(f"Available columns: {list(self.data['jvc'].columns)}")
            return
        
        # Store original sample paths before cleaning - but now sample is already clean
        self.data["jvc"]["original_sample"] = self.data["jvc"]["sample"].copy()
        
        # Extract subbatch using rsplit to get the second-to-last part
        self.data["jvc"]["subbatch"] = self.data["jvc"]["sample"].apply(
            lambda x: x.split('_')[-2] if len(x.split('_')) >= 2 else x
        )
        
        # Extract human-readable batch name for display using original paths
        def extract_display_batch(sample_path):
            filename = sample_path.split('/')[-1].split('.')[0]
            
            # Use rsplit to remove the last 2 parts, regardless of how many underscores are in the name
            if '_' in filename:
                # Split from the right and keep everything except the last 2 parts
                parts = filename.rsplit('_', 2)  # Split into max 3 parts from the right
                result = parts[0]  # Take everything before the last 2 underscores
            else:
                result = filename
            
            return result
        
        # Keep the original batch ID from the file path for actual grouping
        self.data["jvc"]["batch"] = self.data["jvc"]["sample"].apply(
            lambda x: x.split("/")[1] if "/" in x else "unknown"
        )
        
        # Add display batch name for UI purposes using original paths
        self.data["jvc"]["display_batch"] = self.data["jvc"]["original_sample"].apply(extract_display_batch)
        
        self.data["jvc"]["identifier"] = self.data["jvc"]["sample"].apply(
            lambda x: x.split('/')[-1].split(".")[0]
        )
        
        if identifiers:
            self.data["jvc"]["identifier"] = self.data["jvc"]["identifier"].apply(
                lambda x: f'{"_".join(x.split("_")[:-1])}&{identifiers.get(x, "No variation specified")}'
            )
        else:
            self.data["jvc"]["identifier"] = self.data["jvc"]["sample"].apply(
                lambda x: "_".join(x.split('/')[-1].split(".")[0].split("_")[:-1])
            )
    
    def _export_data(self, df_jvc, df_cur):
        """Store data for potential export"""
        self.export_jvc_data = df_jvc
        self.export_curves_data = df_cur
    
    def _find_unique_values(self):
        """Find unique values in the dataset"""
        try:
            unique_values = self.data["jvc"]["identifier"].unique()
        except:
            unique_values = self.data["jvc"]["sample"].unique()
        
        return unique_values
    
    def apply_conditions(self, conditions_dict):
        """Apply conditions mapping to the data"""
        if "jvc" in self.data:
            # Apply the mapping
            self.data['jvc']['condition'] = self.data['jvc']['identifier'].map(conditions_dict)
            
            # Fill any NaN values with a default
            nan_conditions = self.data['jvc']['condition'].isna().sum()
            if nan_conditions > 0:
                self.data['jvc']['condition'] = self.data['jvc']['condition'].fillna('Unknown')
            
            # Verify that each sample_cell has only one condition
            condition_check = self.data['jvc'].groupby(['sample', 'cell'])['condition'].nunique()
            multiple_conditions = condition_check[condition_check > 1]
            
            if len(multiple_conditions) > 0:
                return False
            
            return True
        return False
    
    def apply_filters(self, filter_list, direction_filter='Both', selected_items=None, verbose=True):
        """Apply filters to the dataframe with improved two-step process"""
        if not self.data or "jvc" not in self.data:
            return None, None, []
        
        # Default filters if none provided
        if not filter_list:
            filter_list = [("PCE(%)", "<", "40"), ("FF(%)", "<", "89"), ("FF(%)", ">", "24"), 
                          ("Voc(V)", "<", "2"), ("Jsc(mA/cm2)", ">", "-30")]
        
        # Operator mapping
        operat = {"<": operator.lt, ">": operator.gt, "==": operator.eq,
                  "<=": operator.le, ">=": operator.ge, "!=": operator.ne}
        
        data = self.data["jvc"].copy()
        
        # Initialize filter reason column
        data['filter_reason'] = ''
        filtering_options = []
        
        # Apply sample/cell selection filter if provided
        sample_selection_filtered_count = 0
        if selected_items:
            original_count = len(data)
            
            def is_selected(row):
                cell_key = f"{row['sample']}_{row['cell']}"
                return cell_key in selected_items
            
            selection_mask = data.apply(is_selected, axis=1)
            data.loc[~selection_mask, 'filter_reason'] += 'sample/cell not selected, '
            
            sample_selection_filtered_count = len(data[~selection_mask])
            filtering_options.append(f'sample/cell selection ({sample_selection_filtered_count} filtered)')
        
        # Apply numeric filters
        for col, op, val in filter_list:
            try:
                mask = operat[op](data[col], float(val))
                before_count = len(data[data['filter_reason'] == ''])
                data.loc[~mask, 'filter_reason'] += f'{col} {op} {val}, '
                after_count = len(data[data['filter_reason'] == ''])
                filtered_by_this_condition = before_count - after_count
                
                if filtered_by_this_condition > 0:
                    filtering_options.append(f'{col} {op} {val} ({filtered_by_this_condition} filtered)')
                
            except (ValueError, KeyError) as e:
                if verbose:
                    print(f"Warning: Could not apply filter {col} {op} {val}: {e}")
        
        # Apply direction filter
        if direction_filter != 'Both' and 'direction' in data.columns:
            before_count = len(data[data['filter_reason'] == ''])
            direction_mask = data['direction'] != direction_filter
            data.loc[direction_mask, 'filter_reason'] += f'direction != {direction_filter}, '
            after_count = len(data[data['filter_reason'] == ''])
            direction_filtered_count = before_count - after_count
            
            if direction_filtered_count > 0:
                filtering_options.append(f'direction == {direction_filter} ({direction_filtered_count} filtered)')
        
        # Separate filtered and omitted data
        omitted = data[data['filter_reason'] != ''].copy()
        filtered = data[data['filter_reason'] == ''].copy()
        
        # Clean up filter reason string
        omitted['filter_reason'] = omitted['filter_reason'].str.rstrip(', ')
        
        if 'display_batch' in filtered.columns:
            filtered['batch_for_plotting'] = filtered['display_batch']
        else:
            filtered['batch_for_plotting'] = filtered['batch']
        
        if 'display_batch' in omitted.columns:
            omitted['batch_for_plotting'] = omitted['display_batch']
        else:
            omitted['batch_for_plotting'] = omitted['batch']
        
        # Store results
        self.filtered_data = filtered
        self.omitted_data = omitted
        self.filter_parameters = filtering_options
        
        # Update main data dict
        self.data['filtered'] = filtered
        self.data['junk'] = omitted
        
        # CREATE MATCHING CURVES DATA - ADD THIS BLOCK:
        if not filtered.empty and 'sample_id' in filtered.columns:
            # Create curves data that exactly matches filtered JV data
            matching_curves = self._create_matching_curves_from_filtered_jv(filtered)
            self.data['filtered_curves'] = matching_curves
            
            if verbose:
                print(f"Created {len(matching_curves)} matching curve records for filtered data")
        else:
            self.data['filtered_curves'] = pd.DataFrame()
        
        return filtered, omitted, filtering_options
    
    def generate_summary_statistics(self, df=None):
        """Generate comprehensive summary statistics"""
        if df is None:
            df = self.data.get("jvc", pd.DataFrame())
        
        if df.empty:
            return "No data available for summary."
        
        try:
            # Basic statistics
            global_mean_PCE = df['PCE(%)'].mean()
            global_std_PCE = df['PCE(%)'].std()
            max_PCE_row = df.loc[df['PCE(%)'].idxmax()]
            
            # Group statistics by sample and batch
            mean_std_PCE_per_sample = df.groupby(['batch', 'sample'])['PCE(%)'].agg(['mean', 'std'])
            highest_mean_PCE_sample = mean_std_PCE_per_sample.idxmax()['mean']
            lowest_mean_PCE_sample = mean_std_PCE_per_sample.idxmin()['mean']
            
            # Highest PCE per sample (including batch info)
            if 'display_batch' in df.columns:
                highest_PCE_per_sample = df.loc[df.groupby(['sample'])['PCE(%)'].idxmax(), ['batch', 'sample', 'cell', 'PCE(%)', 'display_batch']]
                highest_PCE_per_sample = highest_PCE_per_sample.copy()
                highest_PCE_per_sample['display_name'] = highest_PCE_per_sample['sample']  # Use consistent sample naming
                max_PCE_display_name = max_PCE_row['sample']  # Use consistent naming
            else:
                highest_PCE_per_sample = df.loc[df.groupby(['sample'])['PCE(%)'].idxmax(), ['batch', 'sample', 'cell', 'PCE(%)']]
                highest_PCE_per_sample = highest_PCE_per_sample.copy()
                highest_PCE_per_sample['display_name'] = highest_PCE_per_sample['batch'] + '_' + highest_PCE_per_sample['sample']
                max_PCE_display_name = max_PCE_row.get('batch', '') + '_' + max_PCE_row['sample']
            
            # Create detailed markdown table
            markdown_output = f"""
### Summary Statistics

**Global mean PCE(%)**: {global_mean_PCE:.2f} ± {global_std_PCE:.2f}%
**Total measurements**: {len(df)}

#### Best and Worst Samples by Average PCE

| | Sample | Mean PCE(%) | Std PCE(%) |
|---|--------|-------------|------------|
| Best sample | {highest_mean_PCE_sample[1]} | {mean_std_PCE_per_sample.loc[highest_mean_PCE_sample, 'mean']:.2f}% | {mean_std_PCE_per_sample.loc[highest_mean_PCE_sample, 'std']:.2f}% |
| Worst sample | {lowest_mean_PCE_sample[1]} | {mean_std_PCE_per_sample.loc[lowest_mean_PCE_sample, 'mean']:.2f}% | {mean_std_PCE_per_sample.loc[lowest_mean_PCE_sample, 'std']:.2f}% |

#### Top Performing Samples

| Sample | Cell | PCE(%) |
|--------|------|--------|
| **{max_PCE_display_name}** | **{max_PCE_row['cell']}** | **{max_PCE_row['PCE(%)']:.2f}%** |
"""
            
            # Add all samples (sorted by PCE descending)
            all_top_samples = highest_PCE_per_sample.sort_values('PCE(%)', ascending=False)
            for _, row in all_top_samples.iterrows():
                if row['sample'] != max_PCE_row['sample'] or row['batch'] != max_PCE_row['batch']:
                    display_name = row.get('display_name', f"{row.get('batch', '')}_{row['sample']}")
                    markdown_output += f"| {display_name} | {row['cell']} | {row['PCE(%)']:.2f}% |\n"
            
            # Add scan direction comparison if available
            if 'direction' in df.columns:
                forward_pce = df[df['direction'] == 'Forward']['PCE(%)'].mean()
                reverse_pce = df[df['direction'] == 'Reverse']['PCE(%)'].mean()
                
                markdown_output += f"""

#### Performance by Scan Direction

| Direction | Average PCE(%) | Count |
|-----------|----------------|-------|
| Forward | {forward_pce:.2f}% | {len(df[df['direction'] == 'Forward'])} |
| Reverse | {reverse_pce:.2f}% | {len(df[df['direction'] == 'Reverse'])} |
"""
            
            # Add distribution statistics
            markdown_output += f"""

#### Distribution Statistics

| Metric | Value |
|--------|-------|
| Median PCE | {df['PCE(%)'].median():.2f}% |
| Min PCE | {df['PCE(%)'].min():.2f}% |
| Max PCE | {df['PCE(%)'].max():.2f}% |
| 25th Percentile | {df['PCE(%)'].quantile(0.25):.2f}% |
| 75th Percentile | {df['PCE(%)'].quantile(0.75):.2f}% |
"""
            
            return markdown_output
            
        except Exception as e:
            return f"""
### Summary Statistics

**Error generating detailed statistics**: {str(e)}

**Basic Info**:
- Total measurements: {len(df)}
- Best Overall PCE: {df['PCE(%)'].max():.2f}% (Sample: {df.loc[df['PCE(%)'].idxmax(), 'sample']})
- Average PCE: {df['PCE(%)'].mean():.2f}%
"""
    
    # Getter methods
    def get_data(self):
        """Get the loaded data"""
        return self.data
    
    def get_unique_values(self):
        """Get unique values"""
        return self.unique_vals
    
    def get_filtered_data(self):
        """Get filtered data"""
        return self.filtered_data
    
    def get_omitted_data(self):
        """Get omitted data"""
        return self.omitted_data
    
    def get_filter_parameters(self):
        """Get filter parameters"""
        return self.filter_parameters
    
    def has_data(self):
        """Check if data is loaded"""
        return bool(self.data and "jvc" in self.data and not self.data["jvc"].empty)
    
    def get_export_data(self):
        """Get the export data for CSV download"""
        return self.export_jvc_data, self.export_curves_data
    
    def has_export_data(self):
        """Check if export data is available"""
        return self.export_jvc_data is not None and self.export_curves_data is not None
    
    def apply_best_cycle_filter(self, data=None, verbose=True):
        """
        Filter data to keep only the best cycle (highest PCE) per sample-pixel combination.
        
        Args:
            data: DataFrame to filter (default: self.data['jvc'])
            verbose: Print filter statistics
        
        Returns:
            Filtered DataFrame with only best cycles
        """
        if data is None:
            data = self.data.get('jvc')
        
        if data is None or data.empty:
            return data
        
        # Check if cycle data exists
        if 'cycle_number' not in data.columns or data['cycle_number'].isna().all():
            if verbose:
                print("ℹ️ No cycle information found in data - no filtering applied")
            return data
        
        # Group by sample, px_number, cell, direction, ilum
        # Keep only the row with maximum PCE for each group
        grouping_cols = ['sample', 'px_number', 'cell', 'direction', 'ilum']
        
        # Filter out rows without valid grouping information
        valid_data = data.dropna(subset=grouping_cols)
        
        if valid_data.empty:
            if verbose:
                print("⚠️ No valid data for cycle filtering")
            return data
        
        # Find best cycle per group
        best_cycles = valid_data.loc[valid_data.groupby(grouping_cols)['PCE(%)'].idxmax()]
        
        if verbose:
            original_count = len(data)
            filtered_count = len(best_cycles)
            removed_count = original_count - filtered_count
            
            print(f"\n🔄 Best Cycle Filter Applied:")
            print(f"   Original measurements: {original_count}")
            print(f"   After filtering: {filtered_count}")
            print(f"   Removed (non-best cycles): {removed_count}")
            
            # Show cycle distribution
            if 'cycle_number' in best_cycles.columns:
                cycle_dist = best_cycles['cycle_number'].value_counts().sort_index()
                print(f"\n   Best cycles selected:")
                for cycle, count in cycle_dist.items():
                    if pd.notna(cycle):
                        print(f"      Cycle {int(cycle)}: {count} pixels")
        
        return best_cycles
    
    def apply_specific_cycle_filter(self, data=None, selected_cycles=None, verbose=True):
        """
        Filter data to keep only specific cycle numbers.
        
        Args:
            data: DataFrame to filter (default: self.data['jvc'])
            selected_cycles: List of cycle numbers to keep (e.g., [0, 1])
            verbose: Print filter statistics
        
        Returns:
            Filtered DataFrame with only selected cycles
        """
        if data is None:
            data = self.data.get('jvc')
        
        if data is None or data.empty:
            return data
        
        if not selected_cycles:
            if verbose:
                print("ℹ️ No specific cycles selected - keeping all data")
            return data
        
        # Check if cycle data exists
        if 'cycle_number' not in data.columns or data['cycle_number'].isna().all():
            if verbose:
                print("ℹ️ No cycle information found in data - no filtering applied")
            return data
        
        # Filter for selected cycles
        mask = data['cycle_number'].isin(selected_cycles)
        filtered_data = data[mask].copy()
        
        if verbose:
            original_count = len(data)
            filtered_count = len(filtered_data)
            removed_count = original_count - filtered_count
            
            print(f"\n🔢 Specific Cycle Filter Applied:")
            print(f"   Selected cycles: {sorted(selected_cycles)}")
            print(f"   Original measurements: {original_count}")
            print(f"   After filtering: {filtered_count}")
            print(f"   Removed (other cycles): {removed_count}")
            
            # Show distribution of kept cycles
            if 'cycle_number' in filtered_data.columns and not filtered_data.empty:
                cycle_dist = filtered_data['cycle_number'].value_counts().sort_index()
                print(f"\n   Kept measurements per cycle:")
                for cycle, count in cycle_dist.items():
                    if pd.notna(cycle):
                        print(f"      Cycle {int(cycle)}: {count} measurements")
        
        return filtered_data
"""
UVVis Data Management Module
Handles data loading, processing, and filtering for UVVis measurements.
"""

__author__ = "Joshua Damm"
__institution__ = "KIT"
__created__ = "December 2025"

import pandas as pd
import numpy as np
import requests
import sys
import os

# Add parent directory for shared modules
parent_dir = os.path.dirname(os.path.dirname(os.getcwd()))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

try:
    from api_calls import get_ids_in_batch, get_entryid
except ImportError:
    print("⚠️ Warning: API modules not available")


def get_specific_data_of_sample(sample_id, entry_type, nomad_url, token, with_meta=False):
    """Get specific measurement data for a sample"""
    entry_id = get_entryid([sample_id], nomad_url, token)['entry_id'][0]

    query = {
        'required': {
            'metadata': '*',
            'data': '*',
        },
        'owner': 'visible',
        'query': {'entry_references.target_entry_id': entry_id},
        'pagination': {
            'page_size': 100
        }
    }
    response = requests.post(f'{nomad_url}/entries/archive/query',
                             headers={'Authorization': f'Bearer {token}'}, json=query)
    linked_data = response.json()["data"]
    res = []

    for ldata in linked_data:
        if entry_type not in ldata["archive"]["metadata"]["entry_type"]:
            continue
        if with_meta:
            res.append((ldata["archive"]["data"], ldata["archive"]["metadata"]))
        else:
            res.append(ldata["archive"]["data"])
    return res


class UVVisDataManager:
    """Main data management class for UVVis analysis"""
    
    def __init__(self, auth_manager):
        self.auth_manager = auth_manager
        self.data = {}
        self.samples = []
        self.measurements_df = None
    
    def load_batch_data(self, batch_ids, output_widget=None):
        """Load UVVis data from selected batch IDs (upload_ids)"""
        self.data = {}
        self.samples = []
        
        if not self.auth_manager.is_authenticated():
            if output_widget:
                with output_widget:
                    print("❌ Authentication required")
            return False
        
        if not batch_ids:
            if output_widget:
                with output_widget:
                    print("❌ Please select at least one batch")
            return False
        
        try:
            url = self.auth_manager.url
            token = self.auth_manager.current_token
            
            if output_widget:
                with output_widget:
                    print("🔍 Loading UVVis data...")
                    print(f"   Batches: {batch_ids}")
            
            # Query samples directly by upload_id instead of using get_ids_in_batch
            # which expects batch lab_ids
            query = {
                'required': {
                    'metadata': '*',
                    'data': '*'
                },
                'owner': 'visible',
                'query': {
                    'upload_id:any': batch_ids,
                    'entry_type': 'peroTF_UVvisMeasurement'
                },
                'pagination': {
                    'page_size': 1000
                }
            }
            
            response = requests.post(
                f'{url}/entries/archive/query',
                headers={'Authorization': f'Bearer {token}'},
                json=query
            )
            response.raise_for_status()
            uvvis_entries = response.json()["data"]
            
            if output_widget:
                with output_widget:
                    print(f"   Found {len(uvvis_entries)} UVVis measurements")
            
            # Load UVVis data from each entry
            all_measurements = []
            successful_samples = 0
            failed_samples = 0
            
            for i, entry in enumerate(uvvis_entries):
                try:
                    uvvis_data = entry["archive"]["data"]
                    metadata = entry["archive"]["metadata"]
                    
                    # Extract sample information
                    sample_name = metadata.get('entry_name', f'Sample_{i}')
                    batch_id = metadata.get('upload_id', 'unknown')
                    entry_id = metadata.get('entry_id', 'unknown')
                    
                    # Get sample lab_id if available
                    sample_id = entry_id
                    if 'samples' in uvvis_data and uvvis_data['samples']:
                        sample_id = uvvis_data['samples'][0].get('lab_id', entry_id)
                    
                    for measurement in uvvis_data.get("measurements", []):
                        measurement_data = {
                            'sample_id': sample_id,
                            'sample_name': sample_name,
                            'batch_id': batch_id,
                            'measurement_name': measurement.get('name', 'unnamed'),
                            'wavelength': np.array(measurement.get('wavelength', [])),
                            'intensity': np.array(measurement.get('intensity', [])),
                            'reflection': np.array(measurement.get('reflection', [])) if 'reflection' in measurement else None,
                            'transmission': np.array(measurement.get('transmission', [])) if 'transmission' in measurement else None,
                            'metadata': metadata
                        }
                        all_measurements.append(measurement_data)
                    
                    successful_samples += 1
                    
                except Exception as e:
                    failed_samples += 1
                    if output_widget:
                        with output_widget:
                            print(f"   ⚠️ Skipped entry {i}: {e}")
            
            # Store data
            self.samples = all_measurements
            self.data['samples'] = all_measurements
            self.data['batch_ids'] = batch_ids
            
            # Create summary DataFrame
            self._create_summary_dataframe()
            
            if output_widget:
                with output_widget:
                    print(f"\n✅ Data loaded successfully!")
                    print(f"   • Successful entries: {successful_samples}")
                    if failed_samples > 0:
                        print(f"   • Failed entries: {failed_samples}")
                    print(f"   • Total measurements: {len(all_measurements)}")
            
            return True
            
        except Exception as e:
            if output_widget:
                with output_widget:
                    print(f"❌ Error loading data: {e}")
                    import traceback
                    traceback.print_exc()
            return False
    
    def _create_summary_dataframe(self):
        """Create summary DataFrame for easier filtering"""
        summary_data = []
        
        for measurement in self.samples:
            summary_data.append({
                'sample_id': measurement['sample_id'],
                'sample_name': measurement['sample_name'],
                'batch_id': measurement['batch_id'],
                'measurement_name': measurement['measurement_name'],
                'num_wavelengths': len(measurement['wavelength']),
                'wavelength_min': measurement['wavelength'].min() if len(measurement['wavelength']) > 0 else 0,
                'wavelength_max': measurement['wavelength'].max() if len(measurement['wavelength']) > 0 else 0,
                'intensity_min': measurement['intensity'].min() if len(measurement['intensity']) > 0 else 0,
                'intensity_max': measurement['intensity'].max() if len(measurement['intensity']) > 0 else 0,
            })
        
        self.measurements_df = pd.DataFrame(summary_data)
    
    def get_data(self):
        """Get loaded data"""
        return self.data
    
    def has_data(self):
        """Check if data is loaded"""
        return bool(self.samples)
    
    def get_summary_statistics(self):
        """Generate summary statistics"""
        if not self.has_data():
            return "No data available"
        
        total_measurements = len(self.samples)
        unique_samples = len(set(m['sample_id'] for m in self.samples))
        unique_batches = len(set(m['batch_id'] for m in self.samples))
        
        markdown = f"""
### UVVis Data Summary

**Total measurements**: {total_measurements}
**Unique samples**: {unique_samples}
**Batches**: {unique_batches}

#### Wavelength Range
"""
        
        if self.measurements_df is not None:
            markdown += f"""
| Metric | Value |
|--------|-------|
| Min wavelength | {self.measurements_df['wavelength_min'].min():.1f} nm |
| Max wavelength | {self.measurements_df['wavelength_max'].max():.1f} nm |
| Min intensity | {self.measurements_df['intensity_min'].min():.4f} |
| Max intensity | {self.measurements_df['intensity_max'].max():.4f} |
"""
        
        return markdown

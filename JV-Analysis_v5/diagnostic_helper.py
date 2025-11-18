"""
Diagnostic Helper
Quick checks for data structure and values
"""

def diagnose_direction_values(data_manager):
    """Diagnose what direction values are actually in the loaded data"""
    if not data_manager.has_data():
        print("❌ No data loaded yet")
        return
    
    data = data_manager.get_data()
    jvc = data.get('jvc')
    curves = data.get('curves')
    
    if jvc is None or jvc.empty:
        print("❌ No JV data available")
        return
    
    print("=" * 70)
    print("DIRECTION VALUES DIAGNOSTIC")
    print("=" * 70)
    
    if 'direction' not in jvc.columns:
        print("❌ 'direction' column not found in data!")
        print(f"Available columns: {list(jvc.columns)}")
        return
    
    # Show unique direction values
    unique_directions = jvc['direction'].unique()
    direction_counts = jvc['direction'].value_counts()
    
    print(f"\n✅ Found 'direction' column")
    print(f"\n📊 Unique direction values: {list(unique_directions)}")
    print(f"\n📈 Direction counts:")
    for direction, count in direction_counts.items():
        print(f"   • {direction}: {count} measurements")
    
    # NEW: Check curves data for cell_name patterns
    if curves is not None and not curves.empty:
        print(f"\n🔍 Analyzing curves data patterns:")
        print(f"   Total curve records: {len(curves)}")
        
        # Look for cell_name patterns
        if 'variable' in curves.columns:
            current_density_curves = curves[curves['variable'] == 'Current Density(mA/cm2)']
            if not current_density_curves.empty:
                print(f"   Current density curves: {len(current_density_curves)}")
                
                # Check for [1] and [2] patterns in index names
                sample_curves = current_density_curves.head(10)
                print(f"\n   Sample curve index patterns (first 10):")
                for idx, row in sample_curves.iterrows():
                    index_name = row.get('index', 'N/A')
                    direction = row.get('direction', 'N/A')
                    print(f"      {index_name} -> {direction}")
    
    # Check a few sample records with all relevant info
    print(f"\n🔍 Sample records (first 5 with all metadata):")
    sample_data = jvc[['sample', 'cell', 'direction', 'status']].head(5)
    
    for idx, row in sample_data.iterrows():
        print(f"   Sample: {row['sample']}, Cell: {row['cell']}, Direction: {row['direction']}, Status: {row.get('status', 'N/A')}")
    
    # Check if there are any unexpected values
    expected_directions = {'Forward', 'Reverse'}
    unexpected = set(unique_directions) - expected_directions
    
    if unexpected:
        print(f"\n⚠️ WARNING: Unexpected direction values found: {unexpected}")
        print(f"   Expected only: {expected_directions}")
    else:
        print(f"\n✅ All direction values are as expected: {expected_directions}")
    
    # Check for any None or NaN values
    null_count = jvc['direction'].isna().sum()
    if null_count > 0:
        print(f"\n⚠️ WARNING: Found {null_count} records with missing direction values")
    
    # NEW: Statistical breakdown by direction
    if len(unique_directions) == 2 and 'Forward' in unique_directions and 'Reverse' in unique_directions:
        print(f"\n📊 Direction Balance:")
        forward_pct = (direction_counts.get('Forward', 0) / len(jvc)) * 100
        reverse_pct = (direction_counts.get('Reverse', 0) / len(jvc)) * 100
        print(f"   Forward: {forward_pct:.1f}%")
        print(f"   Reverse: {reverse_pct:.1f}%")
        
        if abs(forward_pct - 50) > 10:
            print(f"\n⚠️ NOTE: Unbalanced direction distribution (expected ~50/50)")
    
    print("=" * 70)


def add_diagnostic_button_to_app(app):
    """Add a diagnostic button to the app for testing"""
    import ipywidgets as widgets
    
    diagnose_button = widgets.Button(
        description='🔍 Diagnose Directions',
        button_style='warning',
        tooltip='Check what direction values are in the data',
        layout=widgets.Layout(width='200px')
    )
    
    output = widgets.Output()
    
    def on_diagnose_click(b):
        with output:
            from IPython.display import clear_output
            clear_output(wait=True)
            diagnose_direction_values(app.data_manager)
    
    diagnose_button.on_click(on_diagnose_click)
    
    return widgets.VBox([
        widgets.HTML("<h3>🔧 Data Diagnostics</h3>"),
        widgets.HTML("<p>After loading data, click the button below to check direction detection:</p>"),
        diagnose_button,
        output
    ], layout=widgets.Layout(
        border='1px solid #ddd',
        padding='15px',
        margin='20px 0',
        border_radius='5px'
    ))

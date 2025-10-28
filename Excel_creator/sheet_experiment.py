from openpyxl.styles import Alignment, PatternFill
from openpyxl.utils import get_column_letter

TABLEAU_COLORS = {
    'tab:blue': '1F77B4',
    'tab:orange': 'FF7F0E',
    'tab:green': '2CA02C',
    'tab:red': 'D62728',
    'tab:purple': '9467BD',
    'tab:brown': '8C564B',
    'tab:pink': 'E377C2',
    'tab:gray': '7F7F7F',
    'tab:olive': 'BCBD22',
    'tab:cyan': '17BECF',
}
colors = list(TABLEAU_COLORS.values())


def lighten_color(hex_color, factor=0.50):
    hex_color = hex_color.lstrip('#')
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    r = int(r + (255 - r) * factor)
    g = int(g + (255 - g) * factor)
    b = int(b + (255 - b) * factor)
    return f'{r:02x}{g:02x}{b:02x}'.upper()


def add_experiment_sheet(workbook, process_sequence, is_testing=False):
    ws = workbook.active
    ws.title = 'Experiment Data'
    start_col = 1
    incremental_number = 0

    def make_label(label, test_val=None):
        if is_testing:
            if test_val is not None:
                return (label, test_val)
            else:
                return (label, '')
        else:
            return label

    def generate_steps_for_process(process_name, config):
        """
        This method constructs steps for each process. If is_testing=True,
        call make_label("Step Name", <test_value>) to pass a custom test value.
        Otherwise, just pass "Step Name".
        """

        if process_name == 'Experiment Info':
            return [
                make_label('Date', 'beispielwert'),
                make_label('Project_Name', 'beispielwert'),
                make_label('Batch', 'beispielwert'),
                make_label('Subbatch', 'beispielwert'),
                make_label('Sample', 'beispielwert'),
                make_label('Nomad ID', ''),
                make_label('Variation', 'beispielwert'),
                make_label('Sample dimension', 'beispielwert'),
                make_label('Sample area [cm^2]', 'beispielwert'),
                make_label('Number of pixels', 'beispielwert'),
                make_label('Pixel area', 'beispielwert'),
                make_label('Number of junctions', 'beispielwert'),
                make_label('Substrate material', 'beispielwert'),
                make_label('Substrate conductive layer', 'beispielwert'),
                make_label('Bottom Cell Name', 'beispielwert'),
                make_label('Notes', 'beispielwert'),
            ]

        if process_name == 'Multijunction Info':
            return [
                make_label('Recombination Layer', 'beispielwert'),
                make_label('Notes', 'beispielwert'),
            ]

        if process_name == 'Cleaning O2-Plasma' or process_name == 'Cleaning UV-Ozone':
            steps = []
            for i in range(1, config.get('solvents', 1) + 1):
                steps.extend([
                    make_label(f'Solvent {i}', 'beispielwert'),
                    make_label(f'Time {i} [s]', 'beispielwert'),
                    make_label(f'Temperature {i} [°C]', 'beispielwert'),
                ])

            if process_name == 'Cleaning O2-Plasma':
                steps.extend([
                    make_label('Gas-Plasma Gas', 'beispielwert'),
                    make_label('Gas-Plasma Time [s]', 'beispielwert'),
                    make_label('Gas-Plasma Power [W]', 'beispielwert'),
                ])
            if process_name == 'Cleaning UV-Ozone':
                steps.append(make_label('UV-Ozone Time [s]', 'beispielwert'))
            return steps

        if process_name in ['Spin Coating', 'Dip Coating', 'Slot Die Coating', 'Inkjet Printing']:
            steps = [
                make_label('Material name', 'beispielwert'),
                make_label('Layer type', 'beispielwert'),
                make_label('Tool/GB name', 'beispielwert'),
            ]

            # Add solvent steps
            for i in range(1, config.get('solvents', 1) + 1):
                steps.extend([
                    make_label(f'Solvent {i} name', 'beispielwert'),
                    make_label(f'Solvent {i} volume [uL]', 'beispielwert'),
                ])

            # Add solute steps
            for i in range(1, config.get('solutes', 1) + 1):
                steps.extend([
                    make_label(f'Solute {i} type', 'beispielwert'),
                    make_label(f'Solute {i} Concentration [mM]', 'beispielwert'),
                ])

            # Add process-specific steps
            if process_name == 'Spin Coating':
                steps.extend([
                    make_label('Solution volume [uL]', 'beispielwert'),
                    make_label('Spin Delay [s]', 'beispielwert')
                ])

                if config.get('spinsteps', 1) == 1:
                    steps.extend([
                        make_label('Rotation speed [rpm]', 'beispielwert'),
                        make_label('Rotation time [s]', 'beispielwert'),
                        make_label('Acceleration [rpm/s]', 'beispielwert'),
                    ])
                else:
                    for i in range(1, config.get('spinsteps', 1) + 1):
                        steps.extend([
                            make_label(f'Rotation speed {i} [rpm]', 'beispielwert'),
                            make_label(f'Rotation time {i} [s]', 'beispielwert'),
                            make_label(f'Acceleration {i} [rpm/s]', 'beispielwert'),
                        ])

                if config.get('antisolvent', False):
                    steps.extend([
                        make_label('Anti solvent name', 'beispielwert'),
                        make_label('Anti solvent volume [ml]', 'beispielwert'),
                        make_label('Anti solvent dropping time [s]', 'beispielwert'),
                        make_label('Anti solvent dropping speed [uL/s]', 'beispielwert'),
                        make_label('Anti solvent dropping heigt [mm]', 'beispielwert'),
                    ])

                if config.get('gasquenching', False):
                    steps.extend([
                        make_label('Gas', 'beispielwert'),
                        make_label('Gas quenching start time [s]', 'beispielwert'),
                        make_label('Gas quenching duration [s]', 'beispielwert'),
                        make_label('Gas quenching flow rate [ml/s]', 'beispielwert'),
                        make_label('Gas quenching pressure [bar]', 'beispielwert'),
                        make_label('Gas quenching velocity [m/s]', 'beispielwert'),
                        make_label('Gas quenching height [mm]', 'beispielwert'),
                        make_label('Nozzle shape', 'beispielwert'),
                        make_label('Nozzle size [mm²]', 'beispielwert'),
                    ])

                if config.get('vacuumquenching', False):
                    steps.extend([
                        make_label('Vacuum quenching start time [s]', 'beispielwert'),
                        make_label('Vacuum quenching duration [s]', 'beispielwert'),
                        make_label('Vacuum quenching pressure [bar]', 'beispielwert'),
                    ])

            elif process_name == 'Slot Die Coating':
                steps.extend([
                    make_label('Coating run', 'beispielwert'),
                    make_label('Solution volume [um]', 'beispielwert'),
                    make_label('Flow rate [uL/min]', 'beispielwert'),
                    make_label('Head gap [mm]', 'beispielwert'),
                    make_label('Speed [mm/s]', 'beispielwert'),
                    make_label('Air knife angle [°]', 'beispielwert'),
                    make_label('Air knife gap [cm]', 'beispielwert'),
                    make_label('Bead volume [mm/s]', 'beispielwert'),
                    make_label('Drying speed [cm/min]', 'beispielwert'),
                    make_label('Drying gas temperature [°]', 'beispielwert'),
                    make_label('Heat transfer coefficient [W m^-2 K^-1]', 'beispielwert'),
                    make_label('Coated area [mm²]', 'beispielwert'),
                ])

            elif process_name == 'Dip Coating':
                steps.append(make_label('Dipping duration [s]', 'beispielwert'))

            elif process_name == 'Inkjet Printing':
                steps.extend([
                    make_label('Printhead name', 'beispielwert'),
                    make_label('Printing run', 'beispielwert'),
                    make_label('Number of active nozzles', 'beispielwert'),
                    make_label('Droplet density [dpi]', 'beispielwert'),
                    make_label('Quality factor', 'beispielwert'),
                    make_label('Step size', 'beispielwert'),
                    make_label('Printing direction', 'beispielwert'),
                    make_label('Printed area [mm²]', 'beispielwert'),
                    make_label('Droplet per second [1/s]', 'beispielwert'),
                    make_label('Droplet volume [pL]', 'beispielwert'),
                    make_label('Dropping Height [mm]', 'beispielwert'),
                    make_label('Ink reservoir pressure [mbar]', 'beispielwert'),
                    make_label('Table temperature [°C]', 'beispielwert'),
                    make_label('Nozzle temperature [°C]', 'beispielwert'),
                    make_label('Room temperature [°C]', 'beispielwert'),
                    make_label('rel. humidity [%]', 'beispielwert'),
                ])

                pixORnotion = config.get('pixORnotion', 'Pixdro')
                if pixORnotion == 'Pixdro':
                    steps.append(make_label('Wf Number of Pulses', 'beispielwert'))
                    for N_Pulse in range(1, config.get('Wf Number of Pulses', 1) + 1):
                        steps.extend([
                            make_label(f'Wf Level {N_Pulse}[V]', 'beispielwert'),
                            make_label(f'Wf Rise {N_Pulse}[V/us]', 'beispielwert'),
                            make_label(f'Wf Width {N_Pulse}[us]', 'beispielwert'),
                            make_label(f'Wf Fall {N_Pulse}[V/us]', 'beispielwert'),
                            make_label(f'Wf Space {N_Pulse}[us]', 'beispielwert'),
                        ])

                if pixORnotion == 'Notion':
                    steps.extend([
                        make_label('Wf Number of Pulses', 'beispielwert'),
                        make_label('Wf Delay Time [us]', 'beispielwert'),
                        make_label('Wf Rise Time [us]', 'beispielwert'),
                        make_label('Wf Hold Time [us]', 'beispielwert'),
                        make_label('Wf Fall Time [us]', 'beispielwert'),
                        make_label('Wf Relax Time [us]', 'beispielwert'),
                        make_label('Wf Voltage [V]', 'beispielwert'),
                        make_label('Wf Number Greylevels', 'beispielwert'),
                        make_label('Wf Grey Level 0 Use Pulse [1/0]', 'beispielwert'),
                        make_label('Wf Grey Level 1 Use Pulse [1/0]', 'beispielwert'),
                    ])

                if config.get('gasquenching', False):
                    steps.extend([
                        make_label('Gas', 'beispielwert'),
                        make_label('Gas quenching start time [s]', 'beispielwert'),
                        make_label('Gas quenching duration [s]', 'beispielwert'),
                        make_label('Gas quenching flow rate [ml/s]', 'beispielwert'),
                        make_label('Gas quenching pressure [bar]', 'beispielwert'),
                        make_label('Gas quenching velocity [m/s]', 'beispielwert'),
                        make_label('Gas quenching height [mm]', 'beispielwert'),
                        make_label('Nozzle shape', 'beispielwert'),
                        make_label('Nozzle size [mm²]', 'beispielwert'),
                    ])

                if config.get('vacuumquenching', False):
                    steps.extend([
                        make_label('Vacuum quenching start time [s]', 'beispielwert'),
                        make_label('Vacuum quenching duration [s]', 'beispielwert'),
                        make_label('Vacuum quenching pressure [bar]', 'beispielwert'),
                    ])

            # Add annealing steps for all coating processes
            steps.extend([
                make_label('Annealing time [min]', 'beispielwert'),
                make_label('Annealing temperature [°C]', 'beispielwert'),
                make_label('Annealing athmosphere', 'beispielwert'),
                make_label('Notes', 'beispielwert'),
            ])

            return steps

        # PVD Processes
        if process_name == 'Evaporation':
            steps = [
                make_label('Material name', 'beispielwert'),
                make_label('Layer type', 'beispielwert'),
                make_label('Tool/GB name', 'beispielwert'),
                make_label('Organic', 'beispielwert'),
                make_label('Base pressure [bar]', 'beispielwert'),
                make_label('Pressure start [bar]', 'beispielwert'),
                make_label('Pressure end [bar]', 'beispielwert'),
                make_label('Source temperature start[°C]', 'beispielwert'),
                make_label('Source temperature end[°C]', 'beispielwert'),
                make_label('Substrate temperature [°C]', 'beispielwert'),
                make_label('Thickness [nm]', 'beispielwert'),
                make_label('Rate [angstrom/s]', 'beispielwert'),
                make_label('Power [%]', 'beispielwert'),
                make_label('Tooling factor', 'beispielwert'),
                make_label('Notes', 'beispielwert'),
            ]
            return steps

        if process_name == 'Co-Evaporation' or process_name == 'Seq-Evaporation':
            steps = [
                make_label('Material name', 'beispielwert'),
                make_label('Layer type', 'beispielwert'),
                make_label('Tool/GB name', 'beispielwert'),
            ]
            for i in range(1, config.get('materials', 2) + 1):
                steps.extend([
                    make_label(f'Material name {i}', 'beispielwert'),
                    make_label(f'Base pressure {i} [bar]', 'beispielwert'),
                    make_label(f'Pressure start {i} [bar]', 'beispielwert'),
                    make_label(f'Pressure end {i} [bar]', 'beispielwert'),
                    make_label(f'Source temperature start {i}[°C]', 'beispielwert'),
                    make_label(f'Source temperature end {i}[°C]', 'beispielwert'),
                    make_label(f'Substrate temperature {i} [°C]', 'beispielwert'),
                    make_label(f'Thickness {i} [nm]', 'beispielwert'),
                    make_label(f'Rate {i} [angstrom/s]', 'beispielwert'),
                    make_label(f'Tooling factor {i}', 'beispielwert')
                ])
            return steps

        if process_name == 'Close Space Sublimation':
            steps = [
                make_label('Material name', 'beispielwert'),
                make_label('Layer type', 'beispielwert'),
                make_label('Tool/GB name', 'beispielwert'),
                make_label('Organic', 'beispielwert'),
                make_label('Process pressure [bar]', 'beispielwert'),
                make_label('Source temperature [°C]', 'beispielwert'),
                make_label('Substrate temperature [°C]', 'beispielwert'),
                make_label('Material state', 'beispielwert'),
                make_label('Substrate source distance [mm]', 'beispielwert'),
                make_label('Thickness [nm]', 'beispielwert'),
                make_label('Deposition Time [s]', 'beispielwert'),
                make_label('Carrier gas', 'beispielwert'),
                make_label('Notes', 'beispielwert'),
            ]
            return steps

        if process_name == 'Lamination':
            steps = [
                make_label('Interface', 'beispielwert'),
                make_label('Tool/GB name', 'beispielwert'),
                make_label('Temperature during process[°C]', 'beispielwert'),
                make_label('Temperature at pressure relief [°C]', 'beispielwert'),
                make_label('Pressure [MPa]', 'beispielwert'),
                make_label('Force [N]', 'beispielwert'),
                make_label('Time lamination [s]', 'beispielwert'),
                make_label('Heat up time [s]', 'beispielwert'),
                make_label('Cool down time [s]', 'beispielwert'),
                make_label('Total time [s]', 'beispielwert'),
                make_label('Athmosphere in chamber', 'beispielwert'),
                make_label('Humidity [%%rel]', 'beispielwert'),
                make_label('Stamp 1 Material', 'beispielwert'),
                make_label('Stamp 1 Thickness [mm]', 'beispielwert'),
                make_label('Stamp 1 Area [mm^2]', 'beispielwert'),
                make_label('Stamp 2 Material', 'beispielwert'),
                make_label('Stamp 2 Thickness [mm]', 'beispielwert'),
                make_label('Stamp 2 Area [mm^2]', 'beispielwert'),
                make_label('Homogeniously pressed [1/0]', 'beispielwert'),
                make_label('Sucessful adhesion [1/0]', 'beispielwert'),
                make_label('Notes', 'beispielwert'),
            ]
            return steps

        if process_name == 'Sputtering':
            steps = [
                make_label('Material name', 'beispielwert'),
                make_label('Layer type', 'beispielwert'),
                make_label('Tool/GB name', 'beispielwert'),
                make_label('Gas', 'beispielwert'),
                make_label('Temperature [°C]', 'beispielwert'),
                make_label('Pressure [mbar]', 'beispielwert'),
                make_label('Deposition time [s]', 'beispielwert'),
                make_label('Burn in time [s]', 'beispielwert'),
                make_label('Power [W]', 'beispielwert'),
                make_label('Rotation rate [rpm]', 'beispielwert'),
                make_label('Thickness [nm]', 'beispielwert'),
                make_label('Gas flow rate [cm^3/min]', 'beispielwert'),
                make_label('Notes', 'beispielwert'),
            ]
            return steps

        if process_name == 'Laser Scribing':
            steps = [
                make_label('Laser wavelength [nm]', 'beispielwert'),
                make_label('Laser pulse time [ps]', 'beispielwert'),
                make_label('Laser pulse frequency [kHz]', 'beispielwert'),
                make_label('Speed [mm/s]', 'beispielwert'),
                make_label('Fluence [J/cm2]', 'beispielwert'),
                make_label('Power [%]', 'beispielwert'),
                make_label('Recipe file', 'beispielwert'),
            ]
            return steps

        if process_name == 'ALD':
            steps = [
                make_label('Material name', 'beispielwert'),
                make_label('Layer type', 'beispielwert'),
                make_label('Tool/GB name', 'beispielwert'),
                make_label('Source', 'beispielwert'),
                make_label('Thickness [nm]', 'beispielwert'),
                make_label('Temperature [°C]', 'beispielwert'),
                make_label('Rate [A/s]', 'beispielwert'),
                make_label('Time [s]', 'beispielwert'),
                make_label('Number of cycles', 'beispielwert'),
                make_label('Precursor 1', 'beispielwert'),
                make_label('Pulse duration 1 [s]', 'beispielwert'),
                make_label('Manifold temperature 1 [°C]', 'beispielwert'),
                make_label('Bottle temperature 1 [°C]', 'beispielwert'),
                make_label('Precursor 2 (Oxidizer/Reducer)', 'beispielwert'),
                make_label('Pulse duration 2 [s]', 'beispielwert'),
                make_label('Manifold temperature 2 [°C]', 'beispielwert'),
            ]
            return steps

        if process_name == 'Annealing':
            steps = [
                make_label('Annealing time [min]', 'beispielwert'),
                make_label('Annealing temperature [°C]', 'beispielwert'),
                make_label('Annealing athmosphere', 'beispielwert'),
                make_label('Relative humidity [%]', 'beispielwert'),
                make_label('Notes', 'beispielwert'),
            ]
            return steps

        if process_name == 'Generic Process':
            steps = [
                make_label('Name', 'beispielwert'),
                make_label('Notes', 'beispielwert'),
            ]
            return steps

        else:
            print(f"Warning: Process '{process_name}' not defined in generate_steps_for_process. Using default steps.")
            return [make_label('Undefined Process', 'beispielwert')]

    for process_data in process_sequence:
        process_name = process_data['process']
        custom_config = process_data.get('config', {})
        color_index = incremental_number % len(colors)
        cell_color = colors[color_index]
        steps = generate_steps_for_process(process_name, custom_config)
        step_count = len(steps)
        end_col = start_col + step_count - 1

        if process_name != 'Experiment Info':
            process_label = f'{incremental_number}: {process_name}'
        else:
            process_label = process_name

        ws.merge_cells(start_row=1, start_column=start_col,
                       end_row=1, end_column=end_col)
        cell = ws.cell(row=1, column=start_col)
        cell.value = process_label
        cell.alignment = Alignment(horizontal='center', vertical='center')
        cell.fill = PatternFill(start_color=cell_color,
                                end_color=cell_color, fill_type='solid')

        row2_color = lighten_color(cell_color)
        for i, step_item in enumerate(steps):
            col_index = start_col + i
            if isinstance(step_item, tuple):
                step_label, test_val = step_item
                cell = ws.cell(row=2, column=col_index)
                cell.value = step_label
                cell.fill = PatternFill(start_color=row2_color,
                                        end_color=row2_color, fill_type='solid')
                if is_testing:
                    ws.cell(row=3, column=col_index, value=test_val)
        start_col = end_col + 1
        incremental_number += 1

    # Example: Apply a custom formula for the "Nomad ID" column (example only)
    for row in range(3, 4):
        nomad_id_formula = f'=CONCATENATE("HZB_",B{row},"_",C{row},"_",D{row},"_C-",E{row})'
        ws[f'F{row}'].value = nomad_id_formula

    # Adjust column widths
    for col in ws.columns:
        max_length = 0
        column_letter = get_column_letter(col[0].column)
        for cell in col:
            if cell.value and isinstance(cell.value, str):
                max_length = max(max_length, len(cell.value))
        ws.column_dimensions[column_letter].width = max_length + 2

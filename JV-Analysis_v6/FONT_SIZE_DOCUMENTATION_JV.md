# Schriftgrößen-Anpassung für JV-Plots - Dokumentation

## Übersicht
Die JV-Analysis v6 wurde um die Möglichkeit erweitert, die Schriftgrößen der Plots dynamisch anzupassen. Dies ermöglicht es Benutzern, die Lesbarkeit von Achsenbeschriftungen, Titeln und Legenden zu verbessern.

## Neue Features

### 1. **FontSizeUI-Komponente** (`font_size_ui.py`)
Eine neue UI-Klasse zur Kontrolle der Schriftgrößen:

```python
from font_size_ui import FontSizeUI

# Initialisierung
font_ui = FontSizeUI(callback=my_callback_function)

# Widget anzeigen
display(font_ui.get_widget())

# Aktuelle Einstellungen abrufen
settings = font_ui.get_font_sizes()
# Gibt zurück: {'font_size_axis': 12, 'font_size_title': 16, 'font_size_legend': 10}
```

### 2. **PlotManager Updates** (`plot_manager.py`)
Der `PlotManager` wurde mit Schriftgrößen-Eigenschaften erweitert:

```python
# Neue Eigenschaften
plot_manager.font_size_axis = 12    # Größe der Achsenbeschriftungen
plot_manager.font_size_title = 16   # Größe der Plot-Titel
plot_manager.font_size_legend = 10  # Größe der Legendentext

# Neue Methoden
plot_manager.set_font_sizes(axis_size=14, title_size=18, legend_size=11)
plot_manager.apply_font_sizes_to_axes(fig)
```

### 3. **plotting_string_action Parameter** (`plot_manager.py`)
Die Hauptplot-Funktion akzeptiert jetzt optionale Schriftgrößen-Parameter:

```python
figs, names = plotting_string_action(
    plot_list,
    data,
    supp,
    is_voila=True,
    color_scheme=colors,
    separate_scan_dir=False,
    font_size_axis=12,      # Neu!
    font_size_title=16,     # Neu!
    font_size_legend=10     # Neu!
)
```

### 4. **Integration in die App** (`app_controller.py`)
Die FontSizeUI ist in den "Select Plots" Tab integriert:

- **Position**: Unter dem Color Scheme Selector
- **Beschreibung**: 
  - Schieberegler für Achsenbeschriftungen (8-24 pt)
  - Schieberegler für Titel (10-32 pt)
  - Schieberegler für Legenden (6-20 pt)
  - "Reset to Default" Button zur Rückstellung

## Verwendung

### Im Notebook (direkt)
```python
from plot_manager import plotting_string_action

# Plots mit benutzerdefinierten Schriftgrößen erstellen
figs, names = plotting_string_action(
    ['Bpa'],  # Boxplot PCE by Variable
    jv_data,
    support_data,
    font_size_axis=14,
    font_size_title=18,
    font_size_legend=11
)
```

### In der GUI-Anwendung
1. Öffnen Sie den "Select Plots" Tab
2. Scrollen Sie zu "📝 Plot Font Sizes"
3. Passen Sie die Schieberegler nach Bedarf an
4. Wählen Sie Ihre Plot-Typen und klicken Sie auf "Plot Selection"
5. Die neuen Plots verwenden die eingestellten Schriftgrößen

## Standard-Werte

| Element | Standard | Min | Max |
|---------|----------|-----|-----|
| Achsenbeschriftungen | 12 pt | 8 pt | 24 pt |
| Titel | 16 pt | 10 pt | 32 pt |
| Legenden | 10 pt | 6 pt | 20 pt |

## Technische Details

### Betroffene Plot-Typen
- ✅ Boxplots (einzeln und kombiniert)
- ✅ Histogramme
- ✅ JV-Kurven (alle Varianten)
- ✅ Kombinierte Grid-Plots

### Implementierte Änderungen

**1. PlotManager.__init__**
```python
def __init__(self):
    self.plot_output_path = ""
    self.font_size_axis = 12    # Neue Eigenschaft
    self.font_size_title = 16   # Neue Eigenschaft
    self.font_size_legend = 10  # Neue Eigenschaft
```

**2. PlotManager.set_font_sizes()**
```python
def set_font_sizes(self, axis_size=None, title_size=None, legend_size=None):
    """Schriftgrößen dynamisch setzen"""
    if axis_size is not None:
        self.font_size_axis = axis_size
    # ... weitere Parameter ...
```

**3. PlotManager.apply_font_sizes_to_axes()**
```python
def apply_font_sizes_to_axes(self, fig):
    """Schriftgrößen auf Figure-Achsen anwenden"""
    fig.update_xaxes(titlefont=dict(size=self.font_size_axis), ...)
    fig.update_yaxes(titlefont=dict(size=self.font_size_axis), ...)
    return fig
```

### Plotly-Integration
Alle Plots verwenden Plotly's `update_layout` Parameter:
- `title=dict(..., font=dict(size=self.font_size_title))`
- `xaxis=dict(titlefont=dict(size=...), tickfont=dict(size=...))`
- `yaxis=dict(titlefont=dict(size=...), tickfont=dict(size=...))`
- `legend=dict(..., font=dict(size=self.font_size_legend))`

## Beispiel-Workflow

```python
# 1. Font-UI erstellen
font_ui = FontSizeUI()

# 2. Callback für Änderungen
def on_font_change(axis_size, title_size, legend_size):
    print(f"Neue Schriftgrößen: Achse={axis_size}, Titel={title_size}, Legende={legend_size}")

font_ui = FontSizeUI(callback=on_font_change)

# 3. Schieberegler anpassen
font_ui.axis_size_slider.value = 14

# 4. Einstellungen abrufen
settings = font_ui.get_font_sizes()
# {'font_size_axis': 14, 'font_size_title': 16, 'font_size_legend': 10}

# 5. Plots mit diesen Einstellungen erstellen
figs, names = plotting_string_action(..., **settings)
```

## Fehlerbehebung

### Problem: Schriftgrößen werden nicht angewendet
**Lösung**: Stellen Sie sicher, dass Sie die Parameter an `plotting_string_action()` übergeben:
```python
figs, names = plotting_string_action(
    plot_list, data, supp,
    font_size_axis=14,      # ← Nicht vergessen!
    font_size_title=18,
    font_size_legend=11
)
```

### Problem: Text ist zu klein/groß
**Lösung**: Verwenden Sie die GUI-Schieberegler oder passen Sie direkt die Werte an:
```python
plot_manager.set_font_sizes(axis_size=16, title_size=20, legend_size=12)
```

## Zukünftige Erweiterungen
- [ ] Speicherung von Font-Profilen (kleine/mittlere/große Einstellungen)
- [ ] Separate Kontrolle für x/y-Achsen
- [ ] Schriftart-Auswahl (Arial, Helvetica, etc.)
- [ ] Exportable Preset-Konfigurationen

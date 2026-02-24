# JV-Analysis v6 - Schriftgrößen-Anpassung

## Was ist neu? ✨

Die JV-Analysis wurde um eine **interaktive Schriftgrößen-Kontrolle** erweitert, mit der Sie die Lesbarkeit Ihrer Plots direkt in der GUI anpassen können!

## Wo finden Sie die Funktion?

Im **"Select Plots"** Tab des Dashboards, unter dem Color Scheme Selector:

```
📝 Plot Font Sizes
├─ Axis Labels: [========●===] (8-24 pt)
├─ Title: [========●===] (10-32 pt)
├─ Legend: [========●===] (6-20 pt)
└─ Reset to Default [Button]
```

## Wie wird es verwendet?

### Schneller Start
1. Öffnen Sie die JV-Analysis App
2. Gehen Sie zu Tab **"Select Plots"**
3. Scrollen Sie zu **"📝 Plot Font Sizes"**
4. Passen Sie die Schieberegler an (z.B. Achsenbeschriftungen auf 14pt)
5. Wählen Sie Ihre Plot-Typen und klicken Sie **"Plot Selection"**
6. Die neuen Plots verwenden sofort die angepassten Schriftgrößen!

### Standard-Werte
- **Achsenbeschriftungen**: 12 pt (einstellbar 8-24 pt)
- **Titel**: 16 pt (einstellbar 10-32 pt)
- **Legenden**: 10 pt (einstellbar 6-20 pt)

## Beispiele

### Kleine Schriftgrößen (kompakt, viele Daten)
- Achsenbeschriftungen: 10 pt
- Titel: 14 pt
- Legenden: 8 pt

### Große Schriftgrößen (Präsentationen)
- Achsenbeschriftungen: 16 pt
- Titel: 22 pt
- Legenden: 13 pt

## Neue Dateien

| Datei | Beschreibung |
|-------|-------------|
| `font_size_ui.py` | UI-Komponente für Schriftgrößen-Kontrolle |
| `FONT_SIZE_DOCUMENTATION.md` | Ausführliche technische Dokumentation |

## Modifizierte Dateien

| Datei | Änderungen |
|-------|-----------|
| `plot_manager.py` | PlotManager mit font_size Eigenschaften + neue Methoden |
| `app_controller.py` | FontSizeUI Integration in die Haupt-App |

## Technische Details

### PlotManager

```python
plot_manager = PlotManager()
plot_manager.set_font_sizes(axis_size=14, title_size=18, legend_size=11)
```

### plotting_string_action Funktion

```python
figs, names = plotting_string_action(
    plot_list,
    data,
    support_data,
    font_size_axis=14,      # Neu
    font_size_title=18,     # Neu
    font_size_legend=11     # Neu
)
```

## Betroffene Plot-Typen ✅

- Boxplots (einzeln und kombiniert)
- Histogramme
- JV-Kurven (alle Varianten)
- Best Device Plots
- Separated by Cell/Substrate Plots

## Häufig gestellte Fragen

**F: Warum sind meine Plots immer noch klein?**
A: Stellen Sie sicher, dass Sie die Schieberegler *vor* dem Klick auf "Plot Selection" anpassen.

**F: Kann ich die Schriftgrößen speichern?**
A: Derzeit nicht, aber Sie können sie jedes Mal neu einstellen. Zukünftige Versionen werden Profile speichern können.

**F: Funktioniert das auch offline?**
A: Ja, die Schriftgrößen-Anpassung funktioniert komplett lokal ohne externe Abhängigkeiten.

## Zusammenfassung der Code-Änderungen

### Neue Property im PlotManager
```python
self.font_size_axis = 12
self.font_size_title = 16
self.font_size_legend = 10
```

### Neue Methoden
```python
set_font_sizes(axis_size, title_size, legend_size)
apply_font_sizes_to_axes(fig)
```

### Plotly Integration
Alle Plots verwenden jetzt `self.font_size_*` Variablen statt hartcodierter Werte in:
- `title=dict(font=dict(size=self.font_size_title))`
- `xaxis/yaxis=dict(titlefont=dict(size=self.font_size_axis), tickfont=dict(size=...))`
- `legend=dict(font=dict(size=self.font_size_legend))`

## Support

Bei Fragen oder Problemen:
1. Lesen Sie die `FONT_SIZE_DOCUMENTATION.md`
2. Prüfen Sie, dass Sie die aktuellste Version nutzen
3. Versuchen Sie den "Reset to Default" Button

---

**Version**: JV-Analysis v6.1  
**Datum**: Januar 2026  
**Status**: ✅ Produktiv

"""
Resizable Plot Utility for JV Analysis Application
Adds resizable containers to Plotly figures in Jupyter notebooks
"""

__author__ = "Edgar Nandayapa"
__institution__ = "Helmholtz-Zentrum Berlin"
__created__ = "August 2025"

import plotly.graph_objects as go
import plotly.utils
from IPython.display import HTML, display
import json
import uuid
import ipywidgets as widgets


class ResizablePlotWidget:
    """Creates resizable Plotly plots for Jupyter notebooks"""
    
    def __init__(self, fig, title="Plot", initial_width=800, initial_height=600, subtitle=None):  # ADD subtitle parameter
        self.fig = fig
        self.title = title
        self.subtitle = subtitle  # ADD this line
        self.initial_width = initial_width
        self.initial_height = initial_height
        self.plot_id = f"plot_{uuid.uuid4().hex[:8]}"
        
    def display(self):
        """Display the resizable plot with external title"""
        # CRITICAL FIX: Update figure layout AND make legend draggable
        self.fig.update_layout(
            autosize=True,
            margin=dict(l=80, r=50, t=80, b=80, autoexpand=False),
            xaxis=dict(
                autorange=False if self.fig.layout.xaxis.range else True,
                constrain='domain',
                automargin=False
            ),
            yaxis=dict(
                automargin=False
            ),
            legend=dict(
                # ENABLE DRAGGABLE LEGEND - User can move it with mouse
                # Plotly automatically makes legends draggable in interactive mode!
            )
        )
        
        # Convert figure to JSON
        fig_json = json.dumps(self.fig, cls=plotly.utils.PlotlyJSONEncoder)
        
        # CRITICAL: Create title HTML OUTSIDE the plot container
        title_html = f'<h3 style="margin: 20px 0 5px 0; color: #2c3e50;">{self.title}</h3>'
        if self.subtitle:
            title_html += f'<p style="margin: 0 0 10px 0; color: #666; font-size: 12px;">{self.subtitle}</p>'
        
        resize_hint = '<p style="color: #666; font-size: 12px; margin: 5px 0;">💡 Drag the bottom-right corner to resize the plot</p>'
        
        # CRITICAL FIX: Title is now OUTSIDE the resizable container
        resizable_html = f'''
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        
        <div style="margin: 20px 0;">
            {title_html}
            <p style="color: #666; font-size: 12px; margin: 5px 0;">
                💡 Drag the bottom-right corner to resize | 
                🖱️ <strong>Drag the legend</strong> to reposition it
            </p>
            
            <div id="container-{self.plot_id}" style="
                width: {self.initial_width}px; 
                height: {self.initial_height}px; 
                border: 2px solid #ddd; 
                border-radius: 8px;
                resize: both; 
                overflow: hidden;
                min-width: 400px;
                min-height: 300px;
                max-width: 1400px;
                max-height: 1000px;
                background-color: white;
                position: relative;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                transition: border-color 0.2s;
            ">
                <div id="{self.plot_id}" style="
                    width: 100% !important; 
                    height: 100% !important;
                    position: absolute !important;
                    top: 0 !important;
                    left: 0 !important;
                    right: 0 !important;
                    bottom: 0 !important;
                "></div>
                
                <!-- Resize indicator -->
                <div style="
                    position: absolute;
                    bottom: 2px;
                    right: 2px;
                    width: 16px;
                    height: 16px;
                    background: linear-gradient(-45deg, transparent 30%, #999 30%, #999 40%, transparent 40%, transparent 60%, #999 60%, #999 70%, transparent 70%);
                    cursor: se-resize;
                    z-index: 1000;
                    pointer-events: none;
                "></div>
            </div>
        </div>
        
        <style>
        #container-{self.plot_id}:hover {{
            border-color: #007bff;
        }}
        /* CRITICAL: Prevent plot from shifting */
        #container-{self.plot_id} .plotly {{
            width: 100% !important;
            height: 100% !important;
        }}
        #container-{self.plot_id} .main-svg {{
            position: absolute !important;
            top: 0 !important;
            left: 0 !important;
        }}
        </style>
        
        <script>
        (function() {{
            const figureData = {fig_json};
            
            const config = {{
                responsive: true,
                displayModeBar: true,
                displaylogo: false,
                modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d', 'toImage'],
                autosizable: false,
                edits: {{
                    legendPosition: true  // ENABLE: Allow user to drag legend
                }}
            }};
            
            // CRITICAL FIX: Ensure margins are fixed in layout
            if (figureData.layout) {{
                figureData.layout.autosize = true;
                if (!figureData.layout.margin) {{
                    figureData.layout.margin = {{}};
                }}
                figureData.layout.margin.autoexpand = false;
                
                // Disable automargin for all axes
                if (figureData.layout.xaxis) {{
                    figureData.layout.xaxis.automargin = false;
                }}
                if (figureData.layout.yaxis) {{
                    figureData.layout.yaxis.automargin = false;
                }}
            }}
            
            // Store original x-axis range
            let originalXRange = null;
            if (figureData.layout && figureData.layout.xaxis && figureData.layout.xaxis.range) {{
                originalXRange = [...figureData.layout.xaxis.range];
                console.log('Stored original x-axis range:', originalXRange);
            }}
            
            function initPlot() {{
                const plotDiv = document.getElementById('{self.plot_id}');
                const container = document.getElementById('container-{self.plot_id}');

                function triggerBlobDownload(blob, filename) {{
                    const objectUrl = URL.createObjectURL(blob);
                    const link = document.createElement('a');
                    link.href = objectUrl;
                    link.download = filename;
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                    setTimeout(function() {{
                        URL.revokeObjectURL(objectUrl);
                    }}, 1000);
                }}

                // Download SVG: use Plotly.toImage to get a pure SVG data URI,
                // decode it to a raw SVG string, and save as a clean blob.
                // No DOM serialization, no HTML context.
                function downloadSvgViaPlotly(gd, filename) {{
                    const width = gd.clientWidth || gd.offsetWidth || 1200;
                    const height = gd.clientHeight || gd.offsetHeight || 800;

                    return Plotly.toImage(gd, {{
                        format: 'svg',
                        width: width,
                        height: height
                    }}).then(function(dataUri) {{
                        let svgText;

                        const base64Prefix = 'data:image/svg+xml;base64,';
                        const plainPrefix  = 'data:image/svg+xml,';

                        if (dataUri.startsWith(base64Prefix)) {{
                            svgText = atob(dataUri.slice(base64Prefix.length));
                        }} else if (dataUri.startsWith(plainPrefix)) {{
                            svgText = decodeURIComponent(dataUri.slice(plainPrefix.length));
                        }} else {{
                            throw new Error('Unexpected data URI format: ' + dataUri.slice(0, 40));
                        }}

                        const blob = new Blob([svgText], {{ type: 'image/svg+xml;charset=utf-8' }});
                        triggerBlobDownload(blob, filename);
                    }});
                }}

                // Download PNG via Plotly.toImage, decode base64, save as proper blob
                function downloadPngViaPlotly(gd, filename, scale) {{
                    const width = gd.clientWidth || gd.offsetWidth || 1200;
                    const height = gd.clientHeight || gd.offsetHeight || 800;

                    return Plotly.toImage(gd, {{
                        format: 'png',
                        width: width,
                        height: height,
                        scale: scale || 6
                    }}).then(function(dataUri) {{
                        const base64Prefix = 'data:image/png;base64,';
                        if (!dataUri.startsWith(base64Prefix)) {{
                            throw new Error('Unexpected PNG data URI format');
                        }}
                        const byteString = atob(dataUri.slice(base64Prefix.length));
                        const buf = new Uint8Array(byteString.length);
                        for (let i = 0; i < byteString.length; i++) {{
                            buf[i] = byteString.charCodeAt(i);
                        }}
                        const blob = new Blob([buf], {{ type: 'image/png' }});
                        triggerBlobDownload(blob, filename);
                    }});
                }}

                const svgDownloadButton = {{
                    name: 'Download SVG',
                    icon: Plotly.Icons.camera,
                    click: function(gd) {{
                        downloadSvgViaPlotly(gd, 'jv_plot_export.svg').catch(function(err) {{
                            console.error('❌ SVG download failed:', err);
                        }});
                    }}
                }};

                const pngDownloadButton = {{
                    name: 'Download PNG (~600dpi)',
                    icon: Plotly.Icons.camera,
                    click: function(gd) {{
                        downloadPngViaPlotly(gd, 'jv_plot_export_600dpi.png', 6).catch(function(err) {{
                            console.error('❌ PNG download failed:', err);
                        }});
                    }}
                }};

                config.modeBarButtonsToAdd = [svgDownloadButton, pngDownloadButton];
                
                if (!plotDiv || !container) {{
                    setTimeout(initPlot, 100);
                    return;
                }}
                
                const containerRect = container.getBoundingClientRect();
                
                // CRITICAL: Set initial size in layout
                figureData.layout.width = containerRect.width;
                figureData.layout.height = containerRect.height;
                
                Plotly.newPlot(plotDiv, figureData.data, figureData.layout, config).then(function() {{
                    console.log('✅ Resizable plot created: {self.title}');
                    
                    // Preserve x-axis range on relayout events
                    plotDiv.on('plotly_relayout', function(eventData) {{
                        console.log('plotly_relayout event:', eventData);
                        
                        // Restore range if autorange was triggered
                        if (eventData['xaxis.autorange'] === true && originalXRange) {{
                            console.log('Restoring x-axis range after autorange');
                            Plotly.relayout(plotDiv, {{
                                'xaxis.range': originalXRange,
                                'xaxis.autorange': false,
                                'xaxis.automargin': false
                            }});
                        }}
                    }});
                    
                    if (window.ResizeObserver) {{
                        let resizeTimeout;
                        const observer = new ResizeObserver(function(entries) {{
                            clearTimeout(resizeTimeout);
                            resizeTimeout = setTimeout(function() {{
                                const rect = container.getBoundingClientRect();
                                
                                const updateLayout = {{
                                    width: rect.width,
                                    height: rect.height,
                                    'margin.autoexpand': false
                                }};
                                
                                if (originalXRange) {{
                                    updateLayout['xaxis.range'] = originalXRange;
                                    updateLayout['xaxis.autorange'] = false;
                                    updateLayout['xaxis.automargin'] = false;
                                }}
                                
                                console.log('Resizing to:', updateLayout);
                                Plotly.relayout(plotDiv, updateLayout);
                            }}, 100);  // Increased debounce to reduce redraws
                        }});
                        observer.observe(container);
                    }}
                }}).catch(function(err) {{
                    console.error('❌ Plot creation failed:', err);
                }});
            }}
            
            if (typeof Plotly !== 'undefined') {{
                initPlot();
            }} else {{
                let checkCount = 0;
                const checkPlotly = setInterval(function() {{
                    if (typeof Plotly !== 'undefined' || checkCount > 50) {{
                        clearInterval(checkPlotly);
                        if (typeof Plotly !== 'undefined') {{
                            initPlot();
                        }} else {{
                            console.error('❌ Plotly failed to load');
                        }}
                    }}
                    checkCount++;
                }}, 100);
            }}
        }})();
        </script>
        '''
        
        display(HTML(resizable_html))


def create_resizable_plot(fig, title="Plot", width=800, height=600, subtitle=None):  # ADD subtitle
    """
    Create a resizable plot from a Plotly figure.
    
    Args:
        fig: Plotly figure object
        title: Plot title to display ABOVE the plot
        width: Initial width in pixels
        height: Initial height in pixels
        subtitle: Optional subtitle text
    
    Returns:
        ResizablePlotWidget instance
    """
    return ResizablePlotWidget(fig, title, width, height, subtitle)  # PASS subtitle


def display_resizable_plot(fig, title="Plot", width=800, height=600, subtitle=None):  # ADD subtitle
    """
    Convenience function to create and immediately display a resizable plot.
    
    Args:
        fig: Plotly figure object
        title: Plot title to display
        width: Initial width in pixels
        height: Initial height in pixels
        subtitle: Optional subtitle text
    """
    resizable_plot = create_resizable_plot(fig, title, width, height, subtitle)  # PASS subtitle
    resizable_plot.display()


# Integration helper for your existing PlotManager
class ResizablePlotManager:
    """Enhanced plot manager that creates resizable plots"""
    
    @staticmethod
    def display_plots_resizable(figs, names, titles=None, subtitles=None, container_widget=None):  # ADD titles and subtitles
        """
        Display multiple plots as resizable widgets.
        
        Args:
            figs: List of Plotly figures
            names: List of plot filenames
            titles: Optional list of display titles (if None, uses names)
            subtitles: Optional list of subtitles
            container_widget: Optional widget container for output
        """
        if container_widget:
            with container_widget:
                ResizablePlotManager._display_plots_internal(figs, names, titles, subtitles)
        else:
            ResizablePlotManager._display_plots_internal(figs, names, titles, subtitles)
    
    @staticmethod
    def _display_plots_internal(figs, names, titles=None, subtitles=None):  # ADD parameters
        """Internal method to display plots"""
        from IPython.display import clear_output
        clear_output(wait=True)
        
        print(f"✅ Successfully created {len(figs)} resizable plots")
        print("💡 Drag the bottom-right corner of each plot to resize")
        print()
        
        for i, (fig, name) in enumerate(zip(figs, names)):
            try:
                # Use provided title or fall back to name
                display_title = titles[i] if titles and i < len(titles) else name
                subtitle = subtitles[i] if subtitles and i < len(subtitles) else None
                
                # Determine appropriate size based on plot type
                if "histogram" in name.lower():
                    width, height = 700, 500
                elif "jv_curve" in name.lower() or "jv curve" in name.lower():
                    width, height = 800, 600
                elif "boxplot" in name.lower():
                    width, height = 900, 600
                else:
                    width, height = 800, 600
                
                # Create and display resizable plot WITH TITLE AND SUBTITLE
                display_resizable_plot(fig, display_title, width, height, subtitle)
                
            except Exception as e:
                print(f"❌ Error displaying plot {i+1} ({name}): {e}")
                # Fallback to regular display
                try:
                    display(widgets.HTML(f"<h4>{name} (Fallback Display)</h4>"))
                    if hasattr(fig, 'show'):
                        fig.show()
                    else:
                        display(fig)
                except Exception as e2:
                    print(f"❌ Could not display plot {name}: {e2}")


# Example usage and test function
def test_resizable_plot():
    """Test function to demonstrate resizable plots"""
    import numpy as np
    
    # Create sample data
    x = np.linspace(0, 10, 100)
    y1 = np.sin(x) + np.random.normal(0, 0.1, 100)
    y2 = np.cos(x) + np.random.normal(0, 0.1, 100)
    
    # Create test figure
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=y1, mode='lines+markers', name='Sin Wave'))
    fig.add_trace(go.Scatter(x=x, y=y2, mode='lines+markers', name='Cos Wave'))
    
    fig.update_layout(
        title='Test Resizable Plot',
        xaxis_title='X Values',
        yaxis_title='Y Values',
        template="plotly_white"
    )
    
    # Display as resizable plot
    display_resizable_plot(fig, "Test Resizable Plot - Drag corner to resize!", 800, 500)
    
    print("🎯 Test plot created! Try dragging the bottom-right corner to resize.")


if __name__ == "__main__":
    test_resizable_plot()
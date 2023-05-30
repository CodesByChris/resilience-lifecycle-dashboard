"""Interactive bokeh dashboard of the robustness/adaptivity equation system.

This script uses bokeh to generate the HTML code for a dashboard to visualize
the differential equations behind adaptivity and robustness and their dependence
on the parameters.

Plotted graphics are:
1. Adaptivity vs. robustness (Figure 4)
2. Adaptivity and Robustness vs. time (Figure 5)

The dashboard is standalone, which means that it performs all computations for
slider changes in the user's browser. This has the advantage that no server from
our side is required to perform the computations in the background.
"""

from bokeh.colors import Color
from bokeh.embed import file_html
from bokeh.io import curdoc
from bokeh.io.util import default_filename
from bokeh.layouts import column, layout
from bokeh.models import ColumnDataSource, CustomJS, HoverTool, Slider
from bokeh.plotting import figure
from bokeh.resources import CDN
from math import log

# Initial values and constants
T_MAX = 100  # (0, T_MAX) is time interval in which to solve and visualize the differential equations
INITIAL_VALUES = {"robustness": log(0.5), "adaptivity": log(0.5), "time": 0}
INITIAL_PARAMS = {"t_max": T_MAX, "time_step": 0.1,
                  "q": 0.29, "alpha_r": 0.29, "gamma_r0": 1.27, "gamma_r2": 1.41,
                  "beta_a": 0.68, "alpha_a": 0.07, "gamma_a": 0.25, "beta_r": 0.34}
SLIDER_PARAMETERS = [{"start": 0, "end": 1, "value": 0.29, "step": 0.01, "title": "q"},
                     {"start": 0, "end": 1.5, "value": 0.11, "step": 0.01, "title": "alpha_r"},
                     {"start": 0, "end": 1.5, "value": 1.27, "step": 0.01, "title": "gamma_r0"},
                     {"start": 0, "end": 1.5, "value": 1.41, "step": 0.01, "title": "gamma_r2"},
                     {"start": 0, "end": 1.5, "value": 0.68, "step": 0.01, "title": "beta_a"},
                     {"start": 0, "end": 1.5, "value": 0.07, "step": 0.01, "title": "alpha_a"},
                     {"start": 0, "end": 1.5, "value": 0.25, "step": 0.01, "title": "gamma_a"},
                     {"start": 0, "end": 1.5, "value": 0.34, "step": 0.01, "title": "beta_r"},]

COLOR_ADAPTIVITY = "#FBB13C"  # Yellow
COLOR_ROBUSTNESS = "#2E5EAA"  # Blue
COLOR_SG = "#A8322D"  # Red


def make_trajectory_plot(data_source: ColumnDataSource, color: Color | str,
                         line_width: int, width: int, height: int, title: str,
                         font_size_axes: str):
    """Constructs a plot to visualize the 2D-trajectory of the ODE.

    The plot is an xy-plot whose x-axis is robustness and y-axis is adaptivity,
    which are read from (and automatically updated to) data_source.

    The plot's purpose is to show cycles in the dynamics. Whether or not cycles
    exist depends on the values of the ODE's parameters chosen with the sliders,
    which in turn update the parameters of the ODE.

    Args:
        data_source: The data source containing the x and y values for the plot.
            It has columns "robustness" and "adaptivity". Its values are the
            solution of the ODE for a specific set of parameters.
        color: The color of the plotted line.
        line_width: The width of the plotted line.
        width: The width of the plot in pixels.
        height: The height of the plot in pixels.
        title: The plot title.
        font_size_axes: The font size of the axis labels.

    Returns:
        The constructed plot.
    """

    # Plot trajectory
    plot = figure(width=width, height=height, title=title, tooltips=[("Rob.", "$x"), ("Ada.", "$y")])
    plot.line("robustness", "adaptivity", source=data_source, line_width=line_width, color=color)

    # Set visuals
    plot.xaxis.axis_label = "Robustness"
    plot.yaxis.axis_label = "Adaptivity"
    plot.xaxis.axis_label_text_font_size = font_size_axes
    plot.yaxis.axis_label_text_font_size = font_size_axes
    #plot.xaxis.major_label_text_color = COLOR_ROBUSTNESS
    #plot.yaxis.major_label_text_color = COLOR_ADAPTIVITY

    return plot


def make_timeseries_plot(data_source: ColumnDataSource, color_robustness: Color | str,
                         color_adaptivity: Color | str, fill_alpha: int,
                         line_width: int, width: int, height: int, title: str,
                         font_size_axes: str):
    """Constructs a plot to visualize robustness and adaptivity over time.

    The plotted values are read from (and automatically updated to) data_source.

    Args:
        data_source: The data source containing the values for the plot. It has
            columns "robustness", "adaptivity", and "time. Its values are the
            solution of the ODE for a specific set of parameters.
        color_robustness: The color of the plotted robustness line.
        color_adaptivity: The color of the plotted robustness line.
        fill_alpha: The transparency of the shaded areas below the lines.
        line_width: The width of the plotted lines.
        width: The width of the plot in pixels.
        height: The height of the plot in pixels.
        title: The plot title.
        font_size_axes: The font size of the axis labels.

    Returns:
        The constructed plot.
    """
    plot = figure(width=width, height=height, title=title)

    # Plot robustness
    robustness_line = plot.line("time", "robustness", source=data_source, line_width=line_width, color=color_robustness)
    plot.varea("time", 0, "robustness", source=data_source, fill_color=color_robustness, fill_alpha=fill_alpha)

    # Plot adaptivity
    adaptivity_line = plot.line("time", "adaptivity", source=data_source, line_width=line_width, color=color_adaptivity)
    plot.varea("time", 0, "adaptivity", source=data_source, fill_color=color_adaptivity, fill_alpha=fill_alpha)

    # Set tooltips
    #     Hint for showing tooltips only on some glyphs: https://stackoverflow.com/a/37558475
    robustness_hover = HoverTool(tooltips=[("Time", "$x"), ("Rob.", "$y")])
    robustness_hover.renderers = [robustness_line]
    adaptivity_hover = HoverTool(tooltips=[("Time", "$x"), ("Ada.", "$y")])
    adaptivity_hover.renderers = [adaptivity_line]
    plot.add_tools(robustness_hover, adaptivity_hover)

    # Set visuals
    plot.xaxis.axis_label = "Time"
    plot.yaxis.axis_label = "Value"
    plot.xaxis.axis_label_text_font_size = font_size_axes
    plot.yaxis.axis_label_text_font_size = font_size_axes

    return plot


def make_slider(param_dict: dict, data_source: ColumnDataSource) -> Slider:
    """Constructs a slider to change the ODE's parameters.

    Args:
        param_dict: A dict specifying the named arguments of the Slider
            constructor. The arguments are "start", "end", "value", "step", and
            "title". Typically, you will pass an entry from PARAMS_DEFAULT.
        data_source: The ColumnDataSource holding the "robustness",
            "adaptivity", and "time" values displayed in the plots. This
            data_source is updated with the solver's solution.

    Returns:
        The constructed slider.
    """
    slider = Slider(**param_dict)

    # Trigger solver for parameter updates
    slider.js_on_change("value", CustomJS(args={"data_source": data_source}, code="""
        solver.params[cb_obj.title] = cb_obj.value;
        data_source.data = solver.solution;
    """))
    return slider


def main():
    """Create dashboard layout and save HTML page."""

    # Initialize data with placeholder value (will be computed from within JavaScript)
    data_source = ColumnDataSource(data={"robustness": [0], "adaptivity": [0], "time": [0]})

    curdoc().js_on_event('document_ready', CustomJS(args={"data_source": data_source}, code="""
        data_source.data = solver.solution;
    """))

    # Initialize figure widgets
    trajectory_plot = make_trajectory_plot(data_source, "black", line_width=5,
                                           width=500, height=500, title="Plane",
                                           font_size_axes="15pt")
    time_plot = make_timeseries_plot(data_source, color_robustness=COLOR_ROBUSTNESS,
                                     color_adaptivity=COLOR_ADAPTIVITY, fill_alpha=0.15,
                                     line_width=5, width=500, height=500, title="Dynamics",
                                     font_size_axes="15pt")

    # Initialize input widgets (sliders, toggles, etc.)
    sliders = [make_slider(params, data_source) for params in SLIDER_PARAMETERS]

    # Arrange widgets
    dashboard = layout(
        [trajectory_plot, time_plot],
        column(sliders)
    )

    # Initialize solver (extending bokeh.core.templates.FILE)
    load_solver_template = """
        {% block postamble %}
        <script src="dashboard.js"></script>
        <script>
            // Initialize solver object shared between all widgets
            var solver = new Solver({{ params }}, {{ initial_values }});
        </script>
        {% endblock %}
    """

    # Save HTML
    html = file_html(dashboard,
                     resources=CDN,
                     template=load_solver_template,
                     template_variables={"params": INITIAL_PARAMS,
                                         "initial_values": INITIAL_VALUES,})
    with open(default_filename("html"), "w") as file:
        file.write(html)
        # Note: bokeh.plotting.save does not support template_variables, and
        #     thus it cannot initialize the global solver object. This is why
        #     the detour via file_html is used.


if __name__ == "__main__":
    main()

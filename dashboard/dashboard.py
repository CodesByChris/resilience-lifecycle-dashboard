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
from bokeh.layouts import column, layout, row, Spacer
from bokeh.models import Button, ColumnDataSource, CustomJS, Div, HoverTool, Slider
from bokeh.plotting import figure
from bokeh.resources import CDN
from math import log

# Initial values and constants
T_MAX = 100  # (0, T_MAX) is time interval in which to solve and visualize the differential equations
INITIAL_VALUES = {"robustness": log(0.5), "adaptivity": log(0.5), "time": 0}
PRESETS = {"Scenario I": {"t_max": T_MAX, "step_size": 0.1,
                          "q": 0.29, "alpha_r": 0.12, "gamma_r0": 1.27, "gamma_r2": 2.07,
                          "beta_a": 0.68, "alpha_a": 0.07, "gamma_a": 0.24, "beta_r": 0.34},
           "Scenario II": {"t_max": T_MAX, "step_size": 0.1,
                           "q": 0.29, "alpha_r": 0.02, "gamma_r0": 0.7, "gamma_r2": 1.41,
                           "beta_a": 0.33, "alpha_a": 0.01, "gamma_a": 0.01, "beta_r": 0.34}}
INITIAL_PARAMS = PRESETS["Scenario I"].copy()

COLOR_ADAPTIVITY = "#FBB13C"  # Yellow
COLOR_ROBUSTNESS = "#2E5EAA"  # Blue
COLOR_SG = "#A8322D"  # Red


def make_trajectory_plot(data_source: ColumnDataSource, color: Color | str,
                         line_width: int, width: int, height: int, title: str | None,
                         font_size_axes: str, autohide_toolbar: bool):
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
        autohide_toolbar: Whether the bokeh toolbar shall be displayed only when
            the user's mouse is on the plot (True) or permanently (False).

    Returns:
        The constructed plot.
    """

    # Plot trajectory
    plot = figure(width=width, height=height, title=title, tooltips=[("Ada.", "$y"), ("Rob.", "$x")])
    plot.line("robustness", "adaptivity", source=data_source, line_width=line_width, color=color)

    # Set visuals
    plot.xaxis.axis_label = "Robustness"
    plot.yaxis.axis_label = "Adaptivity"
    plot.xaxis.axis_label_text_font_size = font_size_axes
    plot.yaxis.axis_label_text_font_size = font_size_axes
    plot.toolbar.autohide = autohide_toolbar

    return plot


def make_timeseries_plot(data_source: ColumnDataSource, color_robustness: Color | str,
                         color_adaptivity: Color | str, fill_alpha: int,
                         line_width: int, width: int, height: int, title: str | None,
                         font_size_axes: str, autohide_toolbar: bool):
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
        autohide_toolbar: Whether the bokeh toolbar shall be displayed only when
            the user's mouse is on the plot (True) or permanently (False).

    Returns:
        The constructed plot.
    """
    plot = figure(width=width, height=height, title=title)

    # Plot adaptivity
    adaptivity_line = plot.line("time", "adaptivity", source=data_source, line_width=line_width, color=color_adaptivity, legend_label="Adaptivity")
    plot.varea("time", 0, "adaptivity", source=data_source, fill_color=color_adaptivity, fill_alpha=fill_alpha)

    # Plot robustness
    robustness_line = plot.line("time", "robustness", source=data_source, line_width=line_width, color=color_robustness, legend_label="Robustness")
    plot.varea("time", 0, "robustness", source=data_source, fill_color=color_robustness, fill_alpha=fill_alpha)

    # Set tooltips
    #     Hint for showing tooltips only on some glyphs: https://stackoverflow.com/a/37558475
    robustness_hover = HoverTool(tooltips=[("Rob.", "$y"), ("Time", "$x")])
    robustness_hover.renderers = [robustness_line]
    adaptivity_hover = HoverTool(tooltips=[("Ada.", "$y"), ("Time", "$x")])
    adaptivity_hover.renderers = [adaptivity_line]
    plot.add_tools(robustness_hover, adaptivity_hover)

    # Set visuals
    plot.xaxis.axis_label = "Time"
    plot.yaxis.axis_label = "Value"
    plot.xaxis.axis_label_text_font_size = font_size_axes
    plot.yaxis.axis_label_text_font_size = font_size_axes
    plot.toolbar.autohide = autohide_toolbar
    plot.legend.label_text_font_style = "italic"
    plot.legend.background_fill_alpha = 0.8

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
        solver.params[cb_obj.name] = cb_obj.value;
        data_source.data = solver.solution;
    """))
    return slider


def make_preset_button(presets: dict[str, float],
                       data_source: ColumnDataSource,
                       sliders: list[Slider],
                       **kwargs) -> Button:
    """Constructs a button to set all parameters to the given values.

    Args:
        presets: A dictionary containing the parameter names as keys and the
            corresponding values to be set when the button is clicked.
        data_source: The ColumnDataSource holding the "robustness",
            "adaptivity", and "time" values displayed in the plots. This
            data_source is updated with the solver's solution for the new
            parameter values.
        sliders: The parameter sliders. Their values are refreshed with the
            presets.
        kwargs: Named arguments that are directly forwarded to Button.__init__.
            Typical arguments are button_type, label, and icon. For details, see
            https://docs.bokeh.org/en/latest/docs/user_guide/interaction/widgets.html#button

    Returns:
        The constructed button.
    """
    button = Button(**kwargs)

    # Trigger solver for parameter values
    js_callback = """
        // Update solver
        solver.params = {...presets};
        data_source.data = solver.solution;

        // Update sliders
        sliders.forEach(slider => {slider.value = presets[slider.name]});
    """
    button.js_on_event("button_click", CustomJS(args={"data_source": data_source, "presets": presets, "sliders": sliders},
                                                code=js_callback))
    return button


def make_description() -> Div:
    """Constructs the dashboard's description text.

    Returns:
        The description text as a Div to be directly used in a Bokeh layout.
    """

    text = r"""
        This dashboard visualizes the differential equations for the two components
        of the resilience of a social collective, robustness and adaptivity, as
        presented in the paper
        <ul>
            <li><i>"Struggling with change: The fragile resilience of collectives"</i><br>
                by Frank Schweitzer, Christian Zingg, and Giona Casiraghi.</li>
        </ul>
        The differential equations are
        <p id="equations">
        $$ \frac{dr}{dt} = \alpha_r(1 - q) + \gamma_{r_0}r - \gamma_{r_2}r^3 - \beta_a a $$<br>
        $$ \frac{da}{dt} = \alpha_a q - \gamma_a + \beta_r r $$
        </p>
        $$r$$ denotes robustness and $$a$$ denotes adaptivity.
        The parameters of the differential equations can be manipulated using the sliders above.
    """
    return Div(text=text)


def main():
    """Create dashboard layout and save HTML page."""

    # Initialize data with placeholder value (will be computed from within JavaScript)
    data_source = ColumnDataSource(data={"robustness": [0], "adaptivity": [0], "time": [0]})

    curdoc().js_on_event('document_ready', CustomJS(args={"data_source": data_source}, code="""
        data_source.data = solver.solution;
    """))

    # Initialize figure widgets
    trajectory_plot = make_trajectory_plot(data_source, "black", line_width=5,
                                           width=500, height=500, title=None,
                                           font_size_axes="15pt", autohide_toolbar=True)
    time_plot = make_timeseries_plot(data_source, color_robustness=COLOR_ROBUSTNESS,
                                     color_adaptivity=COLOR_ADAPTIVITY, fill_alpha=0.15,
                                     line_width=5, width=500, height=500, title=None,
                                     font_size_axes="15pt", autohide_toolbar=True)

    # Initialize interactive widgets (sliders, toggles, etc.)  # TODO: Turn this into a function for code cleanup?
    sliders = []
    for name, value in INITIAL_PARAMS.items():
        params = {"start": 0,
                  "end": 3,
                  "value": value,
                  "step": 0.01,
                  "title": f"$$\{name}$$",
                  "name": name}
        if name in {"step_size", "t_max"}:
            continue  # no sliders for internal solver parameters
        elif name == "q":
            params["end"] = 1
            params["title"] = "$$q$$"
        elif name == "gamma_r0":
            params["title"] = r"$$\gamma_{r_0}$$"
        elif name == "gamma_r2":
            params["title"] = r"$$\gamma_{r_2}$$"
        sliders.append(make_slider(params, data_source))

    preset_buttons = []
    for name, presets in PRESETS.items():
        preset_buttons.append(make_preset_button(presets, data_source, sliders,
                                                 button_type="primary", label=name))

    controls = column(*sliders,
                      Spacer(height=20),
                      row(Div(text="Presets: "), *preset_buttons))

    # Initialize description text
    description = make_description()

    # Arrange widgets
    dashboard = layout(
        row(trajectory_plot, Spacer(width=40), time_plot, Spacer(width=40), controls),
        Spacer(height=40),
        description
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

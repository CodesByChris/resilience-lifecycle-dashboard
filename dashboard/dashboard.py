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

from bokeh.embed import file_html
from bokeh.io import curdoc
from bokeh.io.util import default_filename
from bokeh.layouts import column, layout
from bokeh.models import ColumnDataSource, CustomJS, Slider
from bokeh.plotting import figure, save
from bokeh.resources import CDN

# Initial values and constants
T_MAX = 100 # (0, T_MAX) is time interval in which to solve and visualize the differential equations
VALUE_RANGE = (0, 1) # axis range for robustness and adaptivity
INITIAL_VALUES = {"robustness": 0.15, "adaptivity": 0.25, "time": 0}
INITIAL_PARAMS = {"t_max": T_MAX, "time_step": 0.1,
                  "q": 0.29, "alpha_r": 0.29, "gamma_r0": 1.27, "gamma_r2": 1.41,
                  "beta_a": 0.68, "alpha_a": 0.07, "gamma_a": 0.25, "beta_r": 0.34}
SLIDER_PARAMETERS = [{"start": 0, "end": 1, "value": 0.29, "step": 0.1, "title": "q"},
                     {"start": 0, "end": 10, "value": 0.11, "step": 0.1, "title": "alpha_r"},
                     {"start": 0, "end": 10, "value": 1.27, "step": 0.1, "title": "gamma_r0"},
                     {"start": 0, "end": 10, "value": 1.41, "step": 0.1, "title": "gamma_r2"},
                     {"start": 0, "end": 10, "value": 0.68, "step": 0.1, "title": "beta_a"},
                     {"start": 0, "end": 10, "value": 0.07, "step": 0.1, "title": "alpha_a"},
                     {"start": 0, "end": 10, "value": 0.25, "step": 0.1, "title": "gamma_a"},
                     {"start": 0, "end": 10, "value": 0.34, "step": 0.1, "title": "beta_r"},]


def make_slider(param_dict: dict, data_source: ColumnDataSource) -> Slider:
    """Constructs a slider and registers callback that triggers ODE recomputation upon change.

    Args:
        param_dict: A dict specifying the named arguments of the Slider
            constructor. The arguments are "start", "end", "value", "step", and
            "title". Typically, you will pass an entry from SLIDER_PARAMETERS.
        data_source: The ColumnDataSource holding the "robustness",
            "adaptivity", and "time" values displayed in the plots. This
            data_source is updated with the solver's solution.

    Returns:
        The constructed slider.
    """
    slider = Slider(**param_dict)

    # Trigger solver for updated parameter
    slider.js_on_change("value", CustomJS(args={"data_source": data_source}, code="""
        solver.params[cb_obj.title] = cb_obj.value;
        data_source.data = solver.solution;
    """))
    return slider


def main():
    """Create dashboard layout and save HTML page."""
    # Initialize data with placeholder value (will be computed from within JavaScript)
    data_source = ColumnDataSource(data={"robustness": [], "adaptivity": [], "time": []})

    curdoc().js_on_event('document_ready', CustomJS(args={"data_source": data_source}, code="""
        data_source.data = solver.solution;
    """))

    # Initialize left figure widget
    trajectory_plot = figure(x_range=VALUE_RANGE, y_range=VALUE_RANGE, width=500, height=500)
    trajectory_plot.line("robustness", "adaptivity", source=data_source, line_width=3)

    # Initialize right figure widget
    time_plot = figure(x_range=(0, T_MAX), y_range=VALUE_RANGE, width=500, height=500)
    time_plot.line("robustness", "time", source=data_source, line_width=2, color="red")
    time_plot.line("adaptivity", "time", source=data_source, line_width=2, color="blue")

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
        #     thus it cannot be used to initialize the solver. This is why the
        #     detour via file_html is used.


if __name__ == "__main__":
    main()

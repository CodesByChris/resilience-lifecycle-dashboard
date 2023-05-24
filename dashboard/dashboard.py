"""Interactive bokeh dashboard of the robustness/adaptivity equation system.

This script uses bokeh to generate the HTML code for a dashboard to visualize
the differential equations behind adaptivity and robustness and their dependence
on the parameters.

Plotted graphics are:
1. Adaptivity vs. robustness (Figure 4)
2. Adaptivity and Robustness vs. time (Figure 5)

The dashboard performs all computations for slider changes in the user's
browser. This has the advantage that no server from our side is required to
perform the computations in the background.
"""

from bokeh.layouts import layout
from bokeh.models import ColumnDataSource, CustomJS, Slider
from bokeh.plotting import figure, save
from bokeh.resources import Resources

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


def make_slider(param_dict: dict) -> Slider:
    """Constructs a slider and registers callback that triggers ODE recomputation upon change.

    Args:
        param_dict: A dict specifying the named arguments of the Slider
            constructor. The arguments are "start", "end", "value", "step", and
            "title". Typically, you will pass an entry from SLIDER_PARAMETERS.

    Returns:
        The constructed slider.
    """
    js_handler = CustomJS(args={"data_source": "data_source"}, code="""
        // Trigger equation solver
        solver.params[cb_obj.title] = cb_obj.value;
        data_source.data = solver.solution;

        // Trigger plot update
        // TODO: DO I HAVE TO TRIGGER PLOT UPDATE USING SOMETHING ALONG THE LINES OF source.change.emit();
    """)
    slider = Slider(**param_dict)
    slider.js_on_change("value", js_handler)
    return slider


def main():
    """Create dashboard layout and save HTML page."""
    # Initialize data with placeholder value (will be computed from within JavaScript)
    data_source = ColumnDataSource(data={"robustness": [0], "adaptivity": [0], "time": [0]})

    # Initialize left figure widget
    trajectory_plot = figure(x_range=VALUE_RANGE, y_range=VALUE_RANGE, width=500, height=500)
    trajectory_plot.line("robustness", "adaptivity", source=data_source, line_width=3)

    # Initialize right figure widget
    time_plot = figure(x_range=(0, T_MAX), y_range=VALUE_RANGE, width=500, height=500)
    time_plot.line("robustness", "time", source=data_source, line_width=2, color="red")
    time_plot.line("adaptivity", "time", source=data_source, line_width=2, color="blue")

    # Initialize input widgets (sliders, toggles, etc.)
    sliders = map(make_slider, SLIDER_PARAMETERS)

    # Arrange widgets
    dashboard = layout(
        [trajectory_plot, time_plot],
        sliders
    )

    # Load solver
    js_resources = Resources("inline", components=["dashboard.js"])

    dashboard.js_on_event("document_ready",
                          CustomJS(args={"params": INITIAL_PARAMS,
                                         "initial_values": INITIAL_VALUES,
                                         "data_source": data_source},
                                   code="""
        var solver = new Solver(params, initial_values);
        data_source.data = solver.solution  // Compute ODE for initial params
    """))

    # Save HTML
    save(dashboard, resources=js_resources)
    # TODO: Likely, I have to pass the library code to import the JavaScript ODE solver, see: https://stackoverflow.com/a/55043631


if __name__ == "__main__":
    main()

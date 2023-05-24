/** Contains the equation solver class for eqn. (4). */

class Solver {
    /** Class for solving the robustness-adaptivity coupled ODE and computing its vector field. */

    /** Constructor.
     *
     * @param params: A dictionary whose elements are the parameters. The keys
     *     are: "alpha_r", "alpha_a", "q", "gamma_r0", "gamma_r2", "gamma_a",
     *          "beta_a", and "beta_r".
     * @param initial_values: A dict containing the values of the ODE's solution
     *     at time t=0. The keys are "robustness", "adaptivity", "time".
     */
    constructor(params, initial_values) {
        // All attributes are intended for the user to change externally
        this.params = params;
        this.initial_values = initial_values;
    }

    get solution() {
        /** Returns the solution to the ODE computed with a forward Euler method using the stored parameters.
         *
         * @returns Array with the three columns (i) robustness, (ii)
         *     adaptivity, and (iii) time. The rows correspond to the evaluation
         *     points.
         */

        // Initialize solution at time t=0
        let {robustness: curr_rob, adaptivity: curr_ada, time: curr_time} = this.initial_values;

        // Solve over time
        let solution = {robustness: Array(), adaptivity: Array(), time: Array()};
        while (curr_time <= this.params.end) {
            // Store current values
            solution.robustness.append(curr_rob)
            solution.adaptivity.append(curr_ada)
            solution.time.append(curr_time)

            // Compute next values (simultaneous update!)
            delta_rob = this.computeDrDt(curr_rob, curr_ada) * self.params.time_step
            delta_ada = this.computeDaDt(curr_rob, curr_ada) * self.params.time_step
            curr_rob += delta_rob
            curr_ada += delta_ada
            curr_time += this.params.time_step
        }

        // TODO: implement link function exp(...)

        return solution
    }

    // get vector_field() {
    //     /** Returns the vector field of the ODE.
    //      *
    //      * @returns ...
    //      */
    //
    //     ...
    // }

    computeDrDt(rob, ada) {
        /** Computes dr/dt according to eqn (4).
         *
         * @param rob Current robustness value.
         * @param ada Current adaptivity value.
         * @returns The computed value for dr/dt.
         */
        const {alpha_r, q, gamma_r0, gamma_r2, beta_a} = this.params;
        return alpha_r*(1 - q) + gamma_r0*rob - gamma_r2*rob*rob*rob - beta_a * ada
    }


    computeDaDt(rob, ada) {
        /** Computes da/dt according to eqn (4).
         *
         * @param rob Current robustness value.
         * @param ada Current adaptivity value.
         * @returns The computed value for da/dt.
         */
        const {alpha_a, q, gamma_a, beta_r} = this.params;
        return alpha_a*q - gamma_a*ada + beta_r*rob
    }
}

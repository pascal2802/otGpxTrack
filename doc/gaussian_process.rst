Gaussian Process Theory
========================

Gaussian Process for Position Errors
-------------------------------------

A Gaussian process (GP) is a collection of random variables, any finite number of which have a joint Gaussian distribution. In the context of GPX tracks, we use a Gaussian process to model correlated position errors that mimic realistic GPS drift.

The Gaussian process :math:`X(t)` is defined by:
- A mean function :math:`m(t) = \mathbb{E}[X(t)]` (typically zero)
- A covariance function :math:`k(t, t') = \text{Cov}(X(t), X(t'))`

For stationary processes, the covariance depends only on the time difference :math:`\tau = t - t'`:

.. math::
    k(\tau) = \sigma^2 \cdot \rho(|\tau|)

where :math:`\sigma^2` is the variance and :math:`\rho(|\tau|)` is the correlation function.

Absolute Exponential Covariance Model
--------------------------------------

We use the Absolute Exponential (also called Laplacian) covariance model:

.. math::
    k(\tau) = \sigma^2 \exp\left(-\frac{|\tau|}{\ell}\right)

where:
- :math:`\sigma^2` is the **amplitude** (variance parameter)
- :math:`\ell` is the **scale** (correlation length in time)

The correlation function is:

.. math::
    \rho(|\tau|) = \exp\left(-\frac{|\tau|}{\ell}\right)

Key properties:
- At :math:`\tau = 0`: :math:`\rho(0) = 1` (perfect correlation with itself)
- At :math:`\tau = \ell`: :math:`\rho(\ell) = 1/e \approx 0.37` (correlation drops to ~37%)
- As :math:`\tau \to \infty`: :math:`\rho(\tau) \to 0` (uncorrelated for large time differences)

In OpenTURNS, this is implemented as `AbsoluteExponential([scale], [amplitude])`.

Measurement Ensemble
--------------------

For a track with :math:`n` points acquired at times :math:`t_1, t_2, \dots, t_n`, we generate error processes for both coordinates:

.. code-block:: python

    # Create time mesh
    mesh = ot.Mesh(ot.Sample.BuildFromPoint(time_values))
    
    # Create covariance model
    cov_model = ot.AbsoluteExponential([scale], [amplitude])
    
    # Create Gaussian processes for X and Y errors
    gp_x = ot.GaussianProcess(cov_model, mesh)
    gp_y = ot.GaussianProcess(cov_model, mesh)
    
    # Generate realizations
    err_x_field = gp_x.getRealization()
    err_y_field = gp_y.getRealization()

The noisy positions are then:

.. math::
    x^{\text{noisy}}_i = x_i + \varepsilon^x_i,
    \quad y^{\text{noisy}}_i = y_i + \varepsilon^y_i,

where :math:`\varepsilon^x_i` and :math:`\varepsilon^y_i` are samples from the Gaussian processes at the measurement times.

Instantaneous Speed Calculation
-------------------------------

The instantaneous speed between consecutive points is computed from the Euclidean distance between noisy positions divided by the time step:

.. math::
    v_i = \frac{\sqrt{(x^{\text{noisy}}_i - x^{\text{noisy}}_{i-1})^2 + (y^{\text{noisy}}_i - y^{\text{noisy}}_{i-1})^2}}{t_i - t_{i-1}}

This yields a stochastic speed field that can be sampled many times using `processSample()` to obtain confidence intervals for speed estimates.

Parameter Selection for GPS Data
---------------------------------

For GPS grand public data acquired at 1 Hz, the following parameters are recommended:

**Amplitude (σ)**: 1.5 meters
- Ensures 95% of position errors are within a 3-meter radius
- Based on the property that 95% of Gaussian values fall within ±1.96σ
- :math:`1.96 \times 1.5 \approx 3` meters

**Scale (ℓ)**: 5.0 seconds
- Appropriate for 1 Hz acquisition rate
- Captures correlation over ~5 measurement points
- Models realistic GPS drift patterns
- Shorter scales would create overly erratic errors; longer scales would over-smooth

Comparison with AR-1 Process
-----------------------------

- Both methods generate correlated errors on X and Y coordinates and compute speeds from noisy trajectories.
- Gaussian process provides a more flexible and mathematically rigorous framework for modeling continuous-time stochastic processes.

Key differences
~~~~~~~~~~~~~~~
- **Correlation structure**: AR-1 uses :math:`\phi^{|k|}`, GP uses :math:`\exp(-|\tau|/\ell)`
- **Parameters**: AR-1 uses ``phi`` and ``sigma_tot``, GP uses ``amplitude`` and ``scale``
- **Stationarity**: AR-1 requires :math:`|\phi| < 1`, GP is always stationary
- **Implementation**: AR-1 uses recursive formula, GP uses covariance model + Cholesky decomposition
- **Temporal resolution**: AR-1 uses discrete time steps, GP models continuous time (discretized)
- **Computational cost**: AR-1 is O(n), GP is O(n³) for Cholesky decomposition

References
----------

* Rasmussen, C. E., & Williams, C. K. I. (2006). *Gaussian Processes for Machine Learning*. MIT Press.
* OpenTURNS documentation - `GaussianProcess` and `AbsoluteExponential` classes.
* Papoulis, A., & Pillai, S. U. (2002). *Probability, Random Variables and Stochastic Processes*. McGraw-Hill.

AR-1 Process Theory
=====================

Autoregressive model of order 1 (AR‑1)
--------------------------------------

An AR‑1 process :math:`X_t` satisfies

.. math::
    X_t = \phi X_{t-1} + \varepsilon_t,

where ``phi`` (``phi``) is the autoregressive coefficient with ``|phi| < 1`` for stationarity and ``\varepsilon_t`` is a white‑noise term, typically Gaussian with variance

.. math::
    \sigma_\varepsilon^2 = \sigma_{\text{tot}}^2\,(1-\phi^2).

The process has zero mean, variance ``sigma_tot**2`` and autocorrelation function

.. math::
    \rho(k) = \phi^{|k|}.

In the context of GPX tracks the AR‑1 model is used to generate correlated position errors (``err_x`` and ``err_y``) that mimic realistic GPS drift.  The function :func:`generate_ar1_error` implements the recursion above using OpenTURNS ``Normal`` distribution for the noise term.

Measurement ensemble
--------------------

For a track with ``n`` points the error vectors are generated independently for the ``x`` and ``y`` coordinates:

.. code-block:: python

    err_x = generate_ar1_error(n, sigma_tot, phi)
    err_y = generate_ar1_error(n, sigma_tot, phi)

The noisy positions are then

.. math::
    x^{\text{noisy}}_t = x_t + \varepsilon^x_t,
    \quad y^{\text{noisy}}_t = y_t + \varepsilon^y_t,

and instantaneous speed is computed from the Euclidean distance between consecutive noisy points divided by the time step.  This yields a stochastic speed field that can be sampled many times (``processSample``) to obtain confidence intervals for speed estimates.

References
----------

* Box, G. E. P., Jenkins, G. M., & Reinsel, G. C. (2015). *Time Series Analysis: Forecasting and Control*.
* OpenTURNS documentation – ``ARMA`` and ``ProcessSample`` classes.

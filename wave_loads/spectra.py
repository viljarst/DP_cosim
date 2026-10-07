"""Wave spectra.

Pure math, no state. Frequencies in rad/s, Hs in metres, Tp in seconds.
The spectrum is one-sided, so the area under it is m0 = Hs^2 / 16.

References:
- Sørensen, Marine Control Systems, section 6.2.1
"""
import numpy as np


def pierson_moskowitz(omega, hs, tp):
    """Modified Pierson-Moskowitz (ITTC) spectrum [m^2 s/rad].

    S = A / omega^5 * exp(-B / omega^4)
    with A = 5/16 * Hs^2 * wp^4 and B = 5/4 * wp^4, where wp = 2*pi/Tp.
    """
    omega = np.atleast_1d(np.asarray(omega, dtype=float))
    wp = 2.0 * np.pi / tp                      # peak frequency [rad/s]
    S = np.zeros_like(omega)
    pos = omega > 0.0                          # avoid dividing by zero at omega = 0
    w = omega[pos]
    S[pos] = 5.0 / 16.0 * hs**2 * wp**4 / w**5 * np.exp(-1.25 * (wp / w) ** 4)
    return S


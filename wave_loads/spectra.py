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



def jonswap(omega, hs, tp, gamma):
    """JONSWAP spectrum [m^2 s/rad] with DNV normalisation.

    S_J = (1 - 0.287 ln(gamma)) * S_PM * gamma^r
    with r = exp(-0.5 * ((omega - wp) / (sigma * wp))^2),
    sigma = 0.07 for omega <= wp and 0.09 for omega > wp.

    The factor (1 - 0.287 ln(gamma)) keeps the area close to Hs^2 / 16.
    gamma = 1 gives back the Pierson-Moskowitz spectrum.
    """
    omega = np.atleast_1d(np.asarray(omega, dtype=float))
    wp = 2.0 * np.pi / tp                                   # peak frequency [rad/s]
    sigma = np.where(omega <= wp, 0.07, 0.09)               # peak width parameter
    r = np.exp(-0.5 * ((omega - wp) / (sigma * wp)) ** 2)   # 1 at the peak, ~0 far away
    peak = gamma ** r                                       # peak enhancement factor
    normalisation = 1.0 - 0.287 * np.log(gamma)
    return normalisation * pierson_moskowitz(omega, hs, tp) * peak
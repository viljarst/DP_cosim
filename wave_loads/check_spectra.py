"""Quick check of spectra.py. Run from the repo folder:  python wave_loads/check_spectra.py"""
import numpy as np

from spectra import pierson_moskowitz

hs = 3.0   # significant wave height [m]
tp = 9.0   # peak period [s]

omega = np.linspace(0.01, 5.0, 5000)          # frequencies [rad/s]
S = pierson_moskowitz(omega, hs, tp)

m0 = np.trapezoid(S, omega)                   # area under the spectrum
print(f"Area under spectrum m0 = {m0:.4f}")
print(f"Expected Hs^2/16       = {hs**2 / 16:.4f}")
print(f"Hs back from spectrum  = {4 * np.sqrt(m0):.3f} m  (should be {hs} m)")
print(f"Peak at omega          = {omega[np.argmax(S)]:.3f} rad/s  (should be 2*pi/Tp = {2 * np.pi / tp:.3f})")
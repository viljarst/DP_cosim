"""Run the whole chain for one sea state and plot the wave loads.

Run from the repo folder:  python wave_forces/run_wave_forces.py

waves block (wave components) -> force model (this folder) -> loads.
The vessel is held still at the origin (no vessel model yet), so this shows
the wave loads that a DP system would have to deal with.
"""
import forces_config  # noqa: F401  (must be first: makes Config/ and wave_loads/ importable)

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from forces_config import get_wave_forces_parameters
from model import build_model
from sea_state import directions_to, elevation, sea_from_parameters
from waveloads_config import get_waveloads_parameters

from enviroment_config import WAVE    # found because forces_config added Config/ to the path

# -- Settings for this run -----------------------------------------------------------
DURATION = 3 * 3600.0                 # [s] three hours, as in a DP analysis
DT = 0.5                              # [s] time step
HEADING_DEG = 0.0                     # vessel heading, 0 = north

# -- The waves block: make the wave components from config --------------------------
wave_parameters = get_waveloads_parameters()
sea, kept = sea_from_parameters(WAVE.hs, WAVE.tp, wave_parameters)
directions = directions_to(sea, WAVE.direction_deg, wave_parameters["direction_is_from"])

# -- The vessel block: build the force model and give it the wave components --------
model = build_model(get_wave_forces_parameters())
model.set_waves(sea.amplitudes, sea.frequencies, sea.phases, directions)
eta = np.array([0.0, 0.0, np.radians(HEADING_DEG)])   # north, east, heading

print(f"Sea state: Hs = {WAVE.hs} m, Tp = {WAVE.tp} s, waves from {WAVE.direction_deg} deg")
print(f"Vessel heading: {HEADING_DEG} deg,  {len(sea.amplitudes)} wave components ({kept:.1%} of the wave energy)")
print(f"Running {DURATION / 3600:.0f} hours with dt = {DT} s ...")

# -- Time loop (this is what do_step in the FMU will do, one step at a time) -------
t = np.arange(0.0, DURATION, DT)
first = np.zeros((len(t), 3))
drift = np.zeros((len(t), 3))
for i, ti in enumerate(t):
    first[i], drift[i] = model.loads(ti, eta)
zeta = elevation(t, sea)              # wave elevation at the vessel

# -- Statistics ------------------------------------------------------------------------
mean_drift = model.mean_drift(eta[2])
names = ("Fx [kN]", "Fy [kN]", "Mz [kNm]")
print()
print(f"{'':10s} {'drift mean':>11s} {'drift std':>10s} {'drift max':>10s} {'1st order std':>14s}")
for k, name in enumerate(names):
    d = drift[:, k] / 1000
    f = first[:, k] / 1000
    print(f"{name:10s} {d.mean():11.1f} {d.std():10.1f} {d[np.argmax(np.abs(d))]:10.1f} {f.std():14.1f}")
print(f"\nMean drift from mean_drift() (no time series): "
      f"Fx = {mean_drift[0] / 1000:.1f} kN, Fy = {mean_drift[1] / 1000:.1f} kN, Mz = {mean_drift[2] / 1000:.1f} kNm")
print(f"Hs from the wave elevation time series: {4 * np.std(zeta):.2f} m")

# -- Plot ------------------------------------------------------------------------------
# Left column: first-order loads, first 5 minutes (fast, large, average zero).
# Right column: drift loads, first 20 minutes (slow, smaller, push one way on average).
minutes = t / 60
fast = minutes <= 5
slow = minutes <= 20
fig, axes = plt.subplots(4, 2, figsize=(13, 10))
fig.suptitle(f"Wave loads, Hs = {WAVE.hs} m, Tp = {WAVE.tp} s, waves from {WAVE.direction_deg} deg, "
             f"vessel heading {HEADING_DEG} deg")

axes[0, 0].plot(minutes[fast], zeta[fast], lw=0.8)
axes[0, 0].set_title("Wave elevation at the vessel (first 5 min)")
axes[0, 0].set_ylabel("[m]")
axes[0, 1].plot(minutes[slow], zeta[slow], lw=0.5)
axes[0, 1].set_title("Wave elevation at the vessel (first 20 min)")

for k, name in enumerate(names):
    left, right = axes[k + 1, 0], axes[k + 1, 1]
    left.plot(minutes[fast], first[fast, k] / 1000, lw=0.8, color="tab:gray")
    left.set_ylabel(name)
    right.plot(minutes[slow], drift[slow, k] / 1000, lw=0.8)
    right.axhline(mean_drift[k] / 1000, ls="--", color="k", lw=1, label="mean drift")
axes[1, 0].set_title("First-order loads")
axes[1, 1].set_title("Drift loads (mean + slowly varying)")
axes[1, 1].legend(loc="upper right", fontsize=8)
axes[-1, 0].set_xlabel("Time [min]")
axes[-1, 1].set_xlabel("Time [min]")
fig.tight_layout()

out = Path(__file__).resolve().parent / "results" / "wave_forces_test.png"
out.parent.mkdir(exist_ok=True)
fig.savefig(out, dpi=120)
print(f"\nPlot saved to {out}")
plt.show()


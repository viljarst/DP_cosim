"""
Vessel spesific parameters
"""
import math
from classes import Hull, Thruster,VesselType

HULL = Hull(
    vessel_type=VesselType.OFFSHORE_SUPPLY_VESSEL,
    loa=88.0,
    lpp=80.0,
    draft=6.0,
    breadth=18.0,
    # Under water the hull reaches from x = -44 m (thrusters) to x = +42 m (bulb).
    los=86.0,
    s_h = 3.0,
    x_los=-1.0,
    # The waterline ends at x = 40 m and is B/4 = 4.5 m wide at x = 30 m.
    bow_angle=math.atan(4.5 / (40.0 - 30.0)),
    # Gives C_WLaft = 648 / (40 * 18) = 0.90, inside the [0.85, 1.15] range of [3.7].
    aw_laft=648.0,
    # Superstructure is forward, so the side area centre is forward of midships.
    af_wind=280.0,
    al_wind=700.0,
    xl_air=12.0,
    af_current=100.0,
    al_current=490.0,
    xl_current=-1.5,
    skegs=((-36.0, 0.0),),
)

THRUSTERS = (
    Thruster("AZ1", "azimuth", diameter=3.0, power_kw=2000.0, x=-40.0, y=5.5, z=1.8, ducted=True),
    Thruster("AZ2", "azimuth", diameter=3.0, power_kw=2000.0, x=-40.0, y=-5.5, z=1.8, ducted=True),
    Thruster("BT1", "tunnel", diameter=2.0, power_kw=900.0, x=31.0, y=0.0, z=2.5, pitch="CPP", tunnel_inlet="rounded"),
    Thruster("BT2", "tunnel", diameter=2.0, power_kw=900.0, x=28.0, y=0.0, z=2.5, pitch="CPP", tunnel_inlet="broken"),
    # Lowered below the keel when in use, hence z < 0.
    Thruster("RAZ", "azimuth", diameter=1.8, power_kw=800.0, x=22.0, y=0.0, z=-1.5),
)


"""
Environment for a run: wind, waves and current.
"""
from classes import Current, Wave, Wind

WIND = Wind(speed=13.8, direction_deg=45.0)
WAVE = Wave(hs=3.1, tp=8.5, direction_deg=45.0)
CURRENT = Current(speed=0.75, direction_deg=45.0)

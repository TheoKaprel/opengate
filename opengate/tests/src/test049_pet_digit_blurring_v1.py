#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from test049_pet_digit_blurring_helpers import *

paths = gate.get_default_test_paths(__file__, "gate_test049_pet_blur")

"""
see https://github.com/teaghan/PET_MonteCarlo
and https://doi.org/10.1002/mp.16032

PET simulation to test blurring options of the digitizer

- PET:
- phantom: nema necr
- output: singles with and without various blur options
"""

# create the simulation
sim = gate.Simulation()
create_simulation(sim)

# start simulation
sim.run()

# print results
stats = sim.output.get_actor("Stats")
print(stats)

# ----------------------------------------------------------------------------------------------------------
readout = sim.output.get_actor("Singles")
ig = readout.GetIgnoredHitsCount()
print()
print(f"Nb of ignored hits : {ig}")

# check stats
print()
gate.warning(f"Check stats")
p = paths.gate_output
stats_ref = gate.read_stat_file(p / "stats.txt")
is_ok = gate.assert_stats(stats, stats_ref, 0.025)

# check root hits
hc = sim.output.get_actor("Hits").user_info
f = p / "pet.root"
is_ok = check_root_hits(paths, 1, f, hc.output, "test049_hits.png") and is_ok

# check root singles
sc = sim.output.get_actor("Singles").user_info
is_ok = (
    check_root_singles(paths, 1, f, sc.output, png_output="test049_singles.png")
    and is_ok
)

gate.test_ok(is_ok)

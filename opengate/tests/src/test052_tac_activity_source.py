#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import opengate as gate
import numpy as np
import matplotlib.pyplot as plt

paths = gate.get_default_test_paths(__file__, "")

"""
Test the option in GenericSource to use a TAC Time Activity Curve
"""

# create the simulation
sim = gate.Simulation()

# units
m = gate.g4_units("m")
nm = gate.g4_units("nm")
mm = gate.g4_units("mm")
cm = gate.g4_units("cm")
Bq = gate.g4_units("Bq")
kBq = 1e3 * Bq
sec = gate.g4_units("s")
min = gate.g4_units("min")
keV = gate.g4_units("keV")

# verbose
ui = sim.user_info
ui.visu = False
ui.g4_verbose = False
ui.g4_verbose_level = 1
ui.number_of_threads = 1
ui.random_seed = "auto"

# world size
world = sim.world
world.size = [1 * m, 1 * m, 1 * m]
world.material = "G4_AIR"

# source of Ac225 ion
s1 = sim.add_source("GenericSource", "source")
s1.particle = "gamma"
s1.position.type = "sphere"
s1.position.radius = 1 * nm
s1.position.translation = [0, 0, 0]
s1.direction.type = "iso"
s1.energy.mono = 140 * keV

# create a decay TAC bw 2 and 5 sec
starting_activity = 100 * kBq / ui.number_of_threads
half_life = 2 * sec
times = np.linspace(1, 6, num=500, endpoint=True) * sec
decay = np.log(2) / half_life
activities = [starting_activity * np.exp(-decay * t) for t in times]
s1.tac_times = times
s1.tac_activities = activities

# stats
stats = sim.add_actor("SimulationStatisticsActor", "Stats")
stats.track_types_flag = True

# phsp actor for timing
phsp = sim.add_actor("PhaseSpaceActor", "phsp")
phsp.attributes = ["GlobalTime"]
phsp.output = paths.output / "test052_tac.root"

# go
# ui.running_verbose_level = gate.EVENT
# (purposely a "hole" in the runtime ; warning not too large otherwise the fit fails)
sim.run_timing_intervals = [[0, 2.9 * sec], [3 * sec, 7 * sec]]
sim.run(start_new_process=True)

# print
stats = sim.output.get_actor("Stats")
print(stats)

# check root
print()
gate.warning("Check root time")
root1, n1 = gate.open_root_as_np(phsp.output, "phsp")
etimes = root1["GlobalTime"] / sec
print(f"Number of events : {len(etimes)}")

# check fit (it is important to convert 'etimes' to sec otherwise
# the fit fails)
hl, xx, yy = gate.fit_exponential_decay(
    etimes, 0, 7
)  # times[0] / sec, times[-1] / sec)
tol = 0.05
hl_ref = half_life / sec
diff = abs(hl - hl_ref) / hl_ref
is_ok = b = diff < tol
diff *= 100
gate.print_test(b, f"Half life {hl_ref:.2f} sec vs {hl:.2f} sec : {diff:.2f}% ")

# plot the fit
f, ax = plt.subplots(1, 1, figsize=(25, 10))
gate.plot_hist(ax, etimes, f"Events times")
ax.plot(xx, yy, label=f"fit")
ax.legend()

fn = paths.output / "test052_tac_times.png"
plt.savefig(fn)
print(f"Plot in {fn}")

gate.test_ok(is_ok)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import opengate as gate
import opengate.contrib.spect_ge_nm670 as gate_spect

paths = gate.get_default_test_paths(__file__, "gate_test028_ge_nm670_spect")

# create the simulation
sim = gate.Simulation()

# main options
ui = sim.user_info
ui.g4_verbose = False
ui.visu = True
ui.visu_type = "vrml"
ui.visu_filename = "geant4VisuFile.wrl"
ui.number_of_threads = 1
ui.check_volumes_overlap = False

# units
m = gate.g4_units("m")
cm = gate.g4_units("cm")
keV = gate.g4_units("keV")
mm = gate.g4_units("mm")
Bq = gate.g4_units("Bq")
kBq = 1000 * Bq

# world size
world = sim.world
world.size = [1 * m, 1 * m, 1 * m]
world.material = "G4_AIR"

# spect head (debug mode = very small collimator)
spect, crystal = gate_spect.add_ge_nm67_spect_head(sim, "spect", debug=True)
psd = 6.11 * cm
spect.translation = [0, 0, -(20 * cm + psd)]

# waterbox
waterbox = sim.add_volume("Box", "waterbox")
waterbox.size = [15 * cm, 15 * cm, 15 * cm]
waterbox.material = "G4_WATER"
blue = [0, 1, 1, 1]
waterbox.color = blue

# physic list
p = sim.get_physics_user_info()
p.physics_list_name = "G4EmStandardPhysics_option4"
p.enable_decay = False

sim.physics_manager.global_production_cuts.gamma = 10 * mm
sim.physics_manager.global_production_cuts.electron = 10 * mm
sim.physics_manager.global_production_cuts.positron = 10 * mm
sim.physics_manager.global_production_cuts.proton = 10 * mm

sim.set_production_cut(
    volume_name="spect",
    particle_name="gamma",
    value=0.1 * mm,
)
sim.set_production_cut(
    volume_name="spect",
    particle_name="electron",
    value=0.1 * mm,
)
sim.set_production_cut(
    volume_name="spect",
    particle_name="positron",
    value=0.1 * mm,
)

# default source for tests
activity = 10 * Bq
beam1 = sim.add_source("GenericSource", "beam1")
beam1.mother = waterbox.name
beam1.particle = "gamma"
beam1.energy.mono = 140.5 * keV
beam1.position.type = "sphere"
beam1.position.radius = 3 * cm
beam1.position.translation = [0, 0, 0 * cm]
beam1.direction.type = "momentum"
beam1.direction.momentum = [0, 0, -1]
beam1.activity = activity / ui.number_of_threads

# add stat actor
stat = sim.add_actor("SimulationStatisticsActor", "Stats")
stat.track_types_flag = True

# start simulation
sim.run()

# stat
gate.warning("Compare stats")
stats = sim.output.get_actor("Stats")
print(stats)
print(f"Number of runs was {stats.counts.run_count}. Set to 1 before comparison")
stats.counts.run_count = 1  # force to 1
stats_ref = gate.read_stat_file(paths.gate_output / "stat1.txt")
is_ok = gate.assert_stats(stats, stats_ref, tolerance=0.02)

gate.test_ok(is_ok)

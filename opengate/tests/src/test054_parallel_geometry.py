#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import opengate as gate
from scipy.spatial.transform import Rotation

paths = gate.get_default_test_paths(__file__, None, "test054")

# create the simulation
sim = gate.Simulation()

# main options
ui = sim.user_info
# ui.visu_type = "vrml"
ui.visu = False
ui.check_volumes_overlap = True
ui.number_of_threads = 1
ui.random_seed = 654923

p = sim.get_physics_user_info()
p.physics_list_name = "G4EmStandardPhysics_option4"

# add a material database
sim.add_material_database(paths.data / "GateMaterials.db")

# units
m = gate.g4_units("m")
cm = gate.g4_units("cm")
MeV = gate.g4_units("MeV")
Bq = gate.g4_units("Bq")
mm = gate.g4_units("mm")

#  change world size
world = sim.world
world.size = [1 * m, 1 * m, 1 * m]
world.material = "G4_AIR"

fake = sim.add_volume("Box", "fake")
fake.size = [40 * cm, 40 * cm, 40 * cm]
fake.material = "G4_AIR"
fake.color = [1, 0, 1, 1]

# image
patient = sim.add_volume("Image", "patient")
patient.mother = fake.name
patient.image = paths.data / "patient-40mm.mhd"
patient.material = "G4_AIR"  # material used by default
patient.voxel_materials = [
    [-2000, -900, "G4_AIR"],
    [-900, -100, "Lung"],
    [-100, 0, "G4_ADIPOSE_TISSUE_ICRP"],
    [0, 300, "G4_TISSUE_SOFT_ICRP"],
    [300, 800, "G4_B-100_BONE"],
    [800, 6000, "G4_BONE_COMPACT_ICRU"],
]

# create two other parallel worlds
sim.add_parallel_world("world2")
sim.add_parallel_world("world3")

# detector in w2 (on top of world)
det = sim.add_volume("Box", "detector")
det.mother = "world2"
det.material = "G4_GLASS_LEAD"
det.size = [400 * mm, 400 * mm, 2 * mm]
det.translation = [0, 0, 200 * mm]
det.rotation = Rotation.from_euler("x", 40, degrees=True).as_matrix()
det.color = [1, 0, 0, 1]

# detector in w3 (on top of w2)
det2 = sim.add_volume("Box", "detector2")
det2.mother = "world3"
det2.material = "G4_GLASS_LEAD"  # set 'None' if this volume should be transparent
det2.size = [400 * mm, 400 * mm, 2 * mm]
det2.translation = [0, 0, 200 * mm]
det2.rotation = Rotation.from_euler("x", -40, degrees=True).as_matrix()
det2.color = [1, 0, 0, 1]

# source
source = sim.add_source("GenericSource", "source")
source.energy.mono = 0.1 * MeV
source.particle = "gamma"
source.position.type = "box"
source.position.size = [1 * mm, 200 * mm, 1 * mm]
source.position.translation = [0, 0, 0 * cm]
source.activity = 10000 * Bq / ui.number_of_threads
source.direction.type = "momentum"
source.direction.momentum = [0, 0, 1]

# add phsp actor detector 1 (overlap!)
phsp = sim.add_actor("PhaseSpaceActor", "phsp")
phsp.output = paths.output / "test054.root"
phsp.mother = det.name
phsp.attributes = [
    "KineticEnergy",
    "PrePosition",
]

# add stat actor
stats = sim.add_actor("SimulationStatisticsActor", "Stats")
stats.track_types_flag = True

# print
print("Geometry trees: ")
print(sim.dump_tree_of_volumes())

# start simulation
output = sim.start(True)

# print results at the end
stat = output.get_actor("Stats")
print(stat)
d = output.get_actor("phsp")
print(d)

keys = ["KineticEnergy", "PrePosition_X", "PrePosition_Y", "PrePosition_Z"]
tols = [0.01, 2.6, 1.8, 1.7]
ref = paths.output_ref / "test054_ref.root"
f = paths.output / "test054.png"
is_ok = gate.compare_root3(
    ref,
    phsp.output,
    "phsp",
    "phsp",
    keys,
    keys,
    tols,
    None,
    None,
    f,
    hits_tol=6.1,
)
gate.test_ok(is_ok)

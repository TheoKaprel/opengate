#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import click
from test045_gan_phsp_pet_gan_helpers import *

paths = gate.get_default_test_paths(__file__, "", "test045")

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


@click.command(context_settings=CONTEXT_SETTINGS)
@click.option("--phantom", "-p", default="analytic", help="Phantom : analytic or vox")
@click.option("--source", "-s", default="analytic", help="Source : analytic or vox")
@click.option("--rad", "-r", default="Ga68", help="Radionuclide Ga68 or F18, etc")
@click.option("--gaga", default=False, is_flag=True, help="Use gaga (GAN) or not")
@click.option("--pet", default=False, is_flag=True, help="W/wo PET output")
@click.option("--activity_bqml", "-a", default="10", help="Activity in BqmL")
@click.option("--threads", "-t", default=1, help="Nb of threads")
@click.option("--visu", "-v", default=False, is_flag=True, help="visu for debug")
@click.option(
    "--output_folder", "-o", default=".", help="output folder (AUTO for the tests)"
)
@click.option("--seed", default="auto", help="random engine seed")
def go(
    phantom, source, rad, gaga, pet, activity_bqml, visu, threads, output_folder, seed
):
    run_test_045_speedrun(
        phantom,
        source,
        rad,
        gaga,
        pet,
        activity_bqml,
        visu,
        threads,
        output_folder,
        seed,
    )


def run_test_045_speedrun(
    phantom, source, rad, gaga, pet, activity_bqml, visu, threads, output_folder, seed
):
    # WARNING
    # only to check computation times, I did not check results

    p = Box()
    p.phantom_type = phantom
    p.source_type = source
    p.use_gaga = gaga
    p.use_pet = pet
    p.activity_Bqml = float(activity_bqml)
    p.number_of_threads = threads
    p.radionuclide = rad

    # (could be options)
    p.iec_vox_mhd = str(paths.data / "iec_2mm.mhd")
    p.iec_vox_json = paths.data / "iec_2mm.json"
    p.source_vox_mhd = str(paths.data / "iec_source_4mm.mhd")
    p.gaga_pth = paths.data / "pth120_test9221_GP_0GP_10.0_100000.pth"

    gate.print_dic(p)

    # output
    if output_folder == "AUTO":
        output_folder = paths.output
    out = f"test045_speedup_p_{p.phantom_type}_s_{p.source_type}_pet_{p.use_pet}_gaga_{gaga}"
    p.pet_output = f"{output_folder}/{out}.root"

    # init the simulation
    sim = gate.Simulation()

    # visu
    sim.user_info.visu = visu
    if visu:
        p.iec_vox_mhd = paths.data / "5x5x5.mhd"
        p.activity_Bqml = 1

    # seed
    if seed != "auto":
        seed = int(seed)
    sim.user_info.random_seed = seed

    # create the simulation
    create_pet_simulation(sim, p)

    # warning cuts

    sim.run()

    # print
    stats = sim.output.get_actor("Stats")
    print(stats)

    # save
    stats.write(f"{output_folder}/{out}.txt")

    if p.use_pet:
        import uproot

        phsp = sim.output.get_actor("Singles").user_info
        f = phsp.output
        s = uproot.open(f)["Singles"]
        print(f"Number of singles: ", s.num_entries)

    return stats.pps


# --------------------------------------------------------------------------
if __name__ == "__main__":
    go()

import opengate as gate
import opengate_core as g4
from anytree import LevelOrderIter

from ..Decorators import requires


class PhysicsEngine(gate.EngineBase):
    """
    Class the contains all the information and mechanism regarding physics
    to actually run a simulation. It is associated to a simulation engine.

    """

    def __init__(self, simulation_engine):
        gate.EngineBase.__init__(self)
        # Keep a pointer to the current physics_manager
        self.physics_manager = simulation_engine.simulation.physics_manager

        # keep a pointer to the simulation engine
        # to which this physics engine belongs
        self.simulation_engine = simulation_engine

        # main g4 physic list
        self.g4_physic_list = None
        self.g4_decay = None
        self.g4_radioactive_decay = None
        self.g4_cuts_by_regions = []
        self.g4_em_parameters = None
        self.g4_step_limiter_storage = {}
        self.g4_special_user_cuts_storage = {}

    def __del__(self):
        if self.verbose_destructor:
            print("del PhysicsManagerEngine")
        pass

    def initialize(self):
        self.initialize_physics_list()
        self.initialize_decay()
        self.initialize_em_options()
        self.initialize_regions()
        self.initialize_user_limits()
        # self.initialize_cuts()

    def initialize_physics_list(self):
        """
        Create a Physic List from the Factory
        """
        ui = self.physics_manager.user_info
        pl_name = ui.physics_list_name
        # Select the Physic List: check if simple ones
        if pl_name.startswith("G4"):
            self.g4_physic_list = gate.create_modular_physics_list(pl_name)
        else:
            # If not, select the Physic List from the Factory
            factory = g4.G4PhysListFactory()
            if not factory.IsReferencePhysList(pl_name):
                s = (
                    f"Cannot find the physic list : {pl_name}\n"
                    f"Known list are : {factory.AvailablePhysLists()}\n"
                    f"With EM : {factory.AvailablePhysListsEM()}\n"
                    f"Default is {self.physics_manager.default_physic_list}\n"
                    f"Help : https://geant4-userdoc.web.cern.ch/UsersGuides/PhysicsListGuide/html/physicslistguide.html"
                )
                gate.fatal(s)
            self.g4_physic_list = factory.GetReferencePhysList(pl_name)

    def initialize_decay(self):
        """
        G4DecayPhysics - defines all particles and their decay processes
        G4RadioactiveDecayPhysics - defines radioactiveDecay for GenericIon
        """
        ui = self.physics_manager.user_info
        if not ui.enable_decay:
            return
        # check if decay/radDecay already exist in the physics list
        # (keep p and pp in self to prevent destruction)
        self.g4_decay = self.g4_physic_list.GetPhysics("Decay")
        if not self.g4_decay:
            self.g4_decay = g4.G4DecayPhysics(1)
            self.g4_physic_list.RegisterPhysics(self.g4_decay)
        self.g4_radioactive_decay = self.g4_physic_list.GetPhysics("G4RadioactiveDecay")
        if not self.g4_radioactive_decay:
            self.g4_radioactive_decay = g4.G4RadioactiveDecayPhysics(1)
            self.g4_physic_list.RegisterPhysics(self.g4_radioactive_decay)

    def initialize_em_options(self):
        # later
        pass

    def initialize_regions(self):
        for region in self.physics_manager.regions.values():
            region.physics_engine = self
            region.initialize()

    def initialize_cuts(self, tree):
        ui = self.physics_manager.user_info

        # range
        if ui.energy_range_min is not None and ui.energy_range_max is not None:
            gate.warning(f"WARNING ! SetEnergyRange only works in MT mode")
            pct = g4.G4ProductionCutsTable.GetProductionCutsTable()
            pct.SetEnergyRange(ui.energy_range_min, ui.energy_range_max)

        # inherit production cuts
        self.propagate_cuts_to_children(tree)

        # global cuts
        self.g4_em_parameters = g4.G4EmParameters.Instance()
        self.g4_em_parameters.SetApplyCuts(ui.apply_cuts)
        if not ui.apply_cuts:
            s = f"No production cuts (apply_cuts is False)"
            gate.warning(s)
            gate.fatal(
                "Not implemented: currently it crashes when apply_cuts is False. To be continued ..."
            )
            return

        # production cuts by region
        for region in ui.production_cuts:
            self.set_region_cut(region)

    # def initialize_max_step_size(self):
    #     for (
    #         volume_name,
    #         step_size_info,
    #     ) in self.physics_manager.user_info.max_step_size.items():
    #         # Check if there is actually a value for the volume
    #         if len(step_size_info.keys()) == 0:
    #             continue
    #         # NB: Currently, step_size is a numerical value to be applied to "all" particles.
    #         # This might need to be extended to per-particle values.
    #         # but that requires discrete processes to be added to the process_managers
    #         # ... to be implemented in the future
    #         # The step_size is handled via a G4UserLimit object
    #         # which is associated with a volume or region
    #         self.simulation_engine.volume_engine.set_max_step_size_in_volume(
    #             volume_name, step_size_info["all"]
    #         )
    #     self.g4_step_limiter_physics = g4.G4StepLimiterPhysics()
    #     self.g4_physic_list.RegisterPhysics(self.g4_step_limiter_physics)

    @requires("physics_manager")
    def initialize_user_limits(self):
        ui = self.physics_manager.user_info

        # 'all' overrides individual settings
        if ui.user_limits_particles["all"] is True:
            particles_to_consider = list(ui.user_limits_particles.keys())
        else:
            particles_to_consider = [
                p for p, v in ui.user_limits_particles.items() if v is True
            ]

        g4_particle_table = g4.G4ParticleTable.GetParticleTable()

        # register StepLimiter as process for relevant particles
        for p_name in particles_to_consider:
            particle = g4_particle_table.FindParticle(p_name)
            # FindParticle return nullptr if particle name was not found
            if particle is None:
                gate.fatal(
                    f"Cannot set user limits for {p_name}. Particle not found in G4 particle table."
                )
            pm = particle.GetProcessManager()

            # G4StepLimiter for the max_step_size cut
            g4_step_limiter = g4.G4StepLimiter("StepLimiter")
            pm.AddDiscreteProcess(g4_step_limiter, 1)

            # G4UserSpecialCuts for the other cuts
            g4_user_special_cuts = g4.G4UserSpecialCuts("UserSpecialCut")
            pm.AddDiscreteProcess(g4_user_special_cuts, 1)

            # store limiter and cuts in lists to
            # to avoid garbage collection after exiting the methods
            self.g4_step_limiter_storage[p_name] = g4_step_limiter
            self.g4_special_user_cuts_storage[p_name] = g4_user_special_cuts

    def propagate_cuts_to_child(self, tree):
        """This method is kept for legacy compatibility
        because the method name was changed to
        propagate_cuts_to_children.
        Should be deleted soon.

        """
        print(10 * "*" + 10 * "#" + 10 * "*")
        print("Old propagate_cuts_to_child method invoked. Please update the code.")
        print(10 * "*" + 10 * "#" + 10 * "*")
        self.propagate_cuts_to_children(tree)

    def propagate_cuts_to_children(self, tree):
        ui = self.physics_manager.user_info
        pc = ui.production_cuts
        # loop on the tree, level order
        for node in LevelOrderIter(tree[gate.__world_name__]):
            if not node.parent:
                # this is the world, do nothing
                continue
            # get the user cuts for this region
            if node.name in pc:
                cuts = pc[node.name]
            else:
                gate.fatal(f"Cannot find region {node.name} in the cuts list: {pc}")
            # get the cuts for the parent
            if node.parent.name in pc:
                pcuts = pc[node.parent.name]
            else:
                gate.fatal(
                    f"Cannot find parent region {node.parent.name} in the cuts list: {pc}"
                )
            for p in self.physics_manager.cut_particle_names:
                # set the cut for the current region like the parent
                # but only if it was not set by user
                if p not in cuts:
                    if p in pcuts:
                        cuts[p] = pcuts[p]
                    else:
                        # special case when the parent=world, with default cuts
                        cuts[p] = -1
                        pcuts[p] = -1

    def set_region_cut(self, region):
        ui = self.physics_manager.user_info
        # get the values for this region
        cuts_values = ui.production_cuts[region]
        # special case for world region
        if region == gate.__world_name__:
            region = "DefaultRegionForTheWorld"
        rs = g4.G4RegionStore.GetInstance()
        reg = rs.GetRegion(region, True)
        if not reg:
            l = ""
            for i in range(rs.size()):
                l += f"{rs.Get(i).GetName()} "
            s = f'Cannot find the region name "{region}". Knowns regions are: {l}'
            gate.warning(s)
            return
        # set the cuts for the region
        cuts = None
        for p in cuts_values:
            if p not in self.physics_manager.cut_particle_names:
                s = (
                    f'Cuts error : I find "{p}" while cuts can only be set for:'
                    f" {self.physics_manager.cut_particle_names.keys()}"
                )
                gate.fatal(s)
            if not cuts:
                cuts = g4.G4ProductionCuts()
            a = self.physics_manager.cut_particle_names[p]
            v = cuts_values[p]
            if type(v) != int and type(v) != float:
                gate.fatal(
                    f"The cut value must be a number, while it is {v} in {cuts_values}"
                )
            if v < 0:
                v = self.g4_physic_list.GetDefaultCutValue()
            cuts.SetProductionCut(v, a)
        reg.SetProductionCuts(cuts)
        # keep the cut object to prevent deletion
        self.g4_cuts_by_regions.append(cuts)

class Model(object):
    def __init__(self, moose, root_element):
        self.moose          = moose
        self.root_element   = root_element
        self.model_info     = moose.element(root_element.path + "/info")

    @staticmethod
    def create(moose, path):
        root_element = moose.element(path)
        model_type = moose.element(root_element.path + "/info").type.lower()
        if model_type == "chemical":
            return ChemicalModel(moose, root_element)
        elif model_type == "electrical":
            return ElectricalModel(moose, root_element)
        elif model_type == "multiscale":
            return MultiscaleModel(moose, root_element)
        else:
            ERROR("Undefined model type, " + model_type "of model " + model_element.path)
            sys.exit(0)

class ChemicalModel(Model):
    property
    def solver(self):
        return self.model_info.chemicalSolver

    @solver.setter
    def solver(self, value):
        value = value.lower()
        compartments = moose.wildcardFind(
            self.root_element.path + "/##[ISA=ChemCompt]"
                                         )

        def _unset_solver():
            """Delete ksolve before deleting stoich"""
            for compartment in compartments:
                if moose.exists(compartment.path + "/solver"):
                    moose.delete(compartment.path + "/solver")
                if moose.exists(compartment.path + "/stoich"):
                    moose.delete(compartment.path + "/stoich")

        def _set_solver(solver_object):
            for compartment in compartments:
                solver = solver_object(compartment.path + "/solver")
                stoich = moose.Stoich(compartment.path + "/stoich")
                stoich.compartment = compartment
                stoich.ksolve      = solver
                stoich.path        = compartment.path + "/##"

        if value in ["gsl", "rk5", "runge kutta"]:
            _unset_solver()
            _set_solver(moose.Ksolve)
            self.model_info.chemicalSolver = "gsl"
        elif value in ["gssa", "gillespie"]:
            _unset_solver()
            _set_solver(moose.Gsolve)
            self.model_info.chemicalSolver = "gssa"
        elif value in ["ee", "exponential euler"]:
            _unset_solver()
            self.model_info.chemicalSolver = "ee"
        else:
            ERROR("Undefined solver type, " + solver)
            sys.exit(0)


    property
    def simdt(self):
        return self.model_info.chemicalSimDt

    @simdt.setter
    def simdt(self, value):
        for clock_id in CHEMICAL_SIMULATION_CLOCK_IDS:
            moose.setClock(clock_id, value)
        self.model_info.chemicalSimDt = value

    property
    def simtime(self):
        return self.model_info.simTime

    @simtime.setter
    def simtime(self, value):
        self.model_info.simTime = value

    property
    def plotdt(self):
        return self.model_info.chemicalPlotDt

    @plotdt.setter
    def plotdt(self, value):
        for clock_id in CHEMICAL_PLOT_CLOCK_IDS:
            moose.setClock(clock_id, value)
        self.model_info.chemicalPlotDt = value

    def enable(self):
        compartments = moose.wildcardFind(
            self.root_element.path + "/##[ISA=ChemCompt]"
                                         )
        for compartment in compartments:
            if moose.exists(compartment.path + "/solver"):
                moose.element(compartment.path + "/solver").tick = CHEMICAL_SIMULATION_CLOCK_IDS[0]
            if moose.exists(compartment.path + "/stoich"):
                moose.element(compartment.path + "/stoich").tick = CHEMICAL_SIMULATION_CLOCK_IDS[0]
        for table in moose.wildcardFind(self.root_element + "/data/graph#/#"):
            table.tick = CHEMICAL_PLOT_CLOCK_IDS[0]

    def disable(self):
        # TODO : change path from /ksolve to /solver
        compartments = moose.wildcardFind(
            self.root_element.path + "/##[ISA=ChemCompt]"
                                         )
        for compartment in compartments:
            if moose.exists(compartment.path + "/solver"):
                moose.element(compartment.path + "/solver").tick = -1
            if moose.exists(compartment.path + "/stoich"):
                moose.element(compartment.path + "/stoich").tick = -1
        for table in moose.wildcardFind(self.root_element + "/data/graph#/#"):
            table.tick = -1


class ElectricalModel(Model):
    property
    def solver(self):
        return self.model_info.electricalSolver

    @solver.setter
    def solver(self, value):
        value = value.lower()
        # get all compartments
        # use a lambda to get path of neuron of all compartments
        # use a set to get unique names, because one neuron will contain many compartments
        # map a lambda again to get the actual neuron object
        neurons      = map( lambda path : moose.element(path)
                          , set( map( lambda x : x.parent.path
                               , moose.wildcardFind(
                            self.root_element.path + "/##[ISA=Compartment]"
                                                   )
                                    )
                               )
                          )

        def _unset_solver():
            for neuron in neurons:
                if moose.exists(neuron.path + "/solver"):
                    moose.delete(neuron.path + "/solver")

        def _set_solver(solver_object):
            for neuron in neurons:
                solver = solver_object(neuron.path + "/solver")
                solver.target = neuron.path

        if value in ["hines"]:
            _unset_solver()
            _set_solver(moose.Hsolve)
            self.model_info.electricalSolver = "hines"
        elif value in ["ee", "exponential euler"]:
            _unset_solver()
            self.model_info.electricalSolver = "ee"
        else:
            ERROR("Undefined solver type, " + solver)
            sys.exit(0)


    property
    def simdt(self):
        return self.model_info.chemicalSimDt

    @simdt.setter
    def simdt(self, value):
        for clock_id in ELECTRICAL_SIMULATION_CLOCK_IDS:
            moose.setClock(clock_id, value)
        self.model_info.chemicalSimDt = value

    property
    def simtime(self):
        return self.model_info.simTime

    @simtime.setter
    def simtime(self, value):
        self.model_info.simTime = value

    property
    def plotdt(self):
        return self.model_info.electricalPlotDt

    @plotdt.setter
    def plotdt(self, value):
        for clock_id in ELCTRICAL_PLOT_CLOCK_IDS:
            moose.setClock(clock_id, value)
        self.model_info.electricalPlotDt = value

    def enable(self):
        neurons      = map( lambda path : moose.element(path)
                          , set( map( lambda x : x.parent.path
                               , moose.wildcardFind(
                            self.root_element.path + "/##[ISA=Compartment]"
                                                   )
                                    )
                               )
                          )
        for neuron in neurons:
            if moose.exists(neuron.path + "/solver"):
                moose.element(neuron.path + "/solver").tick = ELECTRICAL_SIMULATION_CLOCK_IDS[0]
        for table in moose.wildcardFind(self.root_element + "/data/graph#/#"):
            table.tick = ELECTRICAL_PLOT_CLOCK_IDS[0]

    def disable(self):
        neurons      = map( lambda path : moose.element(path)
                          , set( map( lambda x : x.parent.path
                               , moose.wildcardFind(
                            self.root_element.path + "/##[ISA=Compartment]"
                                                   )
                                    )
                               )
                          )
        for neuron in neurons:
            if moose.exists(neuron.path + "/solver"):
                moose.element(neuron.path + "/solver").tick = -1
        for table in moose.wildcardFind(self.root_element + "/data/graph#/#"):
            table.tick = -1

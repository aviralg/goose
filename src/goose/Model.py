class Model(object)

    def __init__(self, moose, root_element):
        self.moose          = moose
        self.root_element   = root_element
        self.model_info     = moose.element(root_element.path + "/info")

    @staticmethod
    def create(moose, filename):
        model_element = moose.load(filename)
        model_type = moose.modeltype(model_element)
        if model_type == moose.CHEMICAL_MODEL:
            model_class = ChemicalModel
        elif model_type == moose.ELECTRICAL_MODEL:
            model_class = ElectricalModel
        elif model_type == moose.MULTISCALE_MODEL:
            model_class = MultiscaleModel
        else:
            ERROR("Undefined model type, " + model_type "of model " + model_element.path)
            sys.exit(0)
        return model_class(moose, model_element)

    @property
    def simulation_dt(self):
        return self._simulation_dt

    @simulation_dt.setter
    def simulation_dt(self, value):
        self._simulation_dt = value

    def state(self):
        pass

    def disable_tables(self):
        for table in self.tables: table.tick = -1

    def enable_tables(self, value)
16 for table 18 for simulation

    def enable_solver(self):
        self.solver.tick = -1

    def disable_solver(self):
        self.solver.tick = -1

    def disable(self):
        self.disable_solver()

    def enable(self):
        self.enable_solver()

    def run(self):
        pass

    @property
    def plot_table_dt(self):
        return [ self.clock.tickDt[clock_id] for clock_id
               in self._plot_table_clock_ids]

    @plot_table_dt.setter
    def plot_table_dt(self, values):
        for clock_id, value in zip(self._plot_table_clock_ids, values):
            self.clock.tickDt[clock_id] = value

    @property
    def simulation_dt(self):
        return [ self.clock.tickDt[clock_id] for clock_id
               in self._simulation_clock_ids ]

    @simulation_dt.setter
    def simulation_dt(self, values):
        for clock_id, value in zip(self._simulation_clock_ids, values):
            self.clock.tickDt[clock_id] = value

    @property
    def solver(self):
        raise NotImplementedError("")

    @solver.setter
    def solver(self, value = None):
        raise NotImplementedError("")


CHEMICAL_SIMULATION_CLOCKS = [ 8 , 9 ]
CHEMICAL_PLOT_TABLE_CLOCKS = [10, 11]

class ChemicalModel(self):
    simulation_clock_ids     = CHEMICAL_SIMULATION_CLOCK_IDS
    plot_table_clock_ids     = CHEMICAL_PLOT_TABLE_CLOCK_IDS
    def __init__( self
                , simulation_runtime    = DEFAULT_CHEMICAL_SIMULATION_RUNTIME
                ):
        self.root   = root
        self.clock  = moose.element("/clock")
        self.plots  =

        self.simulation_clocks = [ moose.clock("/clock").tick[clock_id]
                                   for clock_id in CHEMICAL_SIMULATION_CLOCK_IDS ]
        moose.clock("/clock").tick[8].dt =

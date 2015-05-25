from PyQt4 import Qt, QtCore, QtGui
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from utils import *
import time

# simulation_data = { "tables"        : { "container_path"    :   { "table_name" : data
#                                                                 , "table_name" : data
#                                                                 }
#                                       , "container_path"    :   { "table_name" : data
#                                                                 , "table_name" : data
#                                                                 }
#                                       }
#                   , "chemical"      : { "hash_id"   :  { "conc"    : value
#                                                         , "n"       : n
#                                                         , "concInit":
#                                                         , "nInit"   :
#                                                         }
#                                       }
#                   , "electrical"    : { "hash_id"   :  { "vm"      : vm
#                                                         , "im"      : im
#                                                         }
#                                       }
#                   , "time"          : {}
#                   }

class SimulationToolBar(QToolBar):
    """docstring for SimulationToolBar"""

    def __init__(self, parent, slots = {}):
        super(SimulationToolBar, self).__init__(parent)
        self.setFloatable(False)
        self.setMovable(False)
        # self.instance   = parent.instance
        # self.moose      = self.instance["moose"]
        # self.service    = self.instance["service"]
        # self._model         = model
        # self._application   = application
        # self._parent        = parent
        # self._signals       = signals
        # self._slots         = slots
        self._last_pressed_action = None
        self._setup_actions()
        self.simulation_data = { "time"         : 0.0
                               , "chemical"     : {}
                               , "electrical"   : {}
                               }


    def replace_action(self, old_action, new_action):
        self.insertAction(old_action, new_action)
        self.removeAction(old_action)

    def _reset_slot(self):
        if not self.paused():
            self.replace_action(self._pause_action, self._run_action)
        self._reset_action.setDisabled(True) # Makes no sense to disable twice.

    def _run_slot(self):
        self.replace_action(self._run_action, self._pause_action)

    def _pause_slot(self):
        self.replace_action(self._pause_action, self._run_action)

    def print_simulation_data(self):
        import pprint
        pprint.pprint("Printing => " + str(self.simulation_data["time"]))

    def print_on_console(self, simulation_data):
        try:
            print("Called")
            self.simulation_data = copy.deepcopy(simulation_data)
        #     import copy
        #     for mid in simulation_data[]
        #     self.simulation_data = copy.deepcopy()
        #     self.simulation_data["time"] = self.parent().instance["moose"].element("/clock").runTime
        #     for pool in self.parent().instance["moose"].wildcardFind("/##[ISA=PoolBase]"):
        #         self.simulation_data["chemical"][pool.__hash__()] = { "concInit"    : pool.concInit
        #                                                             , "conc"        : pool.conc
        #                                                             , "n"           : pool.n
        #                                                             , "nInit"       : pool.nInit
        #                                                             , "path"        : pool.path
        #                                                             }
        # # print("Hello")
        # # print(self.simulation_data)
        #     print("Done")
        finally:
            QTimer.singleShot(0, self.print_simulation_data)

        # if self.tables is None:
        #     self.tables = self.parent().instance["moose"].wildcardFind("/##[ISA=Table2]")
        # for table in self.tables:
        #     print(table.vector

    # def _start_slot(self):
    #     if self._last_pressed_action == self.NO_BUTTON:
    #         self._initialize_slot()
    #     elif self._last_pressed_action == self.INITIALIZE_BUTTON:
    #         self._initialize_slot()


    def _setup_actions(self):
        self._start_action  = QAction(self)
        self._start_action.setIcon(QIcon(RUN_SIMULATION_ICON_PATH))
        self._start_action.triggered.connect(lambda _ : self.parent().instance["service"].run_simulation())
        self.addAction(self._start_action)
        # self._resume_action = QAction("Resume Simulation")
        # self._pause_action  = QAction("Pause Simulation")
        self._reset_action  = QAction(self)
        self._reset_action.setIcon(QIcon(RESET_SIMULATION_ICON_PATH))
        self._reset_action.triggered.connect(
            lambda _ : self.parent().instance["service"].initialize_simulation( 5e-3
                                                                              , self.print_on_console
                                                                              )
                                            )
        self.addAction(self._reset_action)

    def _create(self):
        self._run_simulation_button = QPushButton("&Run", self)
        self._run_simulation_button.setIcon(QIcon(RUN_SIMULATION_ICON_PATH))
        self._run_simulation_button.setToolTip("Run/Resume Simulation")
        self._run_simulation_button.setFlat(True)
        self._run_simulation_button.setFocusPolicy(QtCore.Qt.NoFocus)
        self._run_simulation_button.clicked.connect(
            lambda : self._slots["simulation"]["run"](float(self._total_simtime_field.text()))
                                                   )
        self.addWidget(self._run_simulation_button)

        self._stop_simulation_button = QPushButton("&Stop", self)
        self._stop_simulation_button.setIcon(QIcon(STOP_SIMULATION_ICON_PATH))
        self._stop_simulation_button.setToolTip("Stop/Pause Simulation")
        self._stop_simulation_button.setFlat(True)
        self._stop_simulation_button.setFocusPolicy(QtCore.Qt.NoFocus)
        self._stop_simulation_button.clicked.connect(self._slots["simulation"]["pause"])
        self.addWidget(self._stop_simulation_button)

        self._reset_simulation_button = QPushButton("&Reset", self)
        self._reset_simulation_button.setIcon(QIcon(RESET_SIMULATION_ICON_PATH))
        self._reset_simulation_button.setToolTip("Reset Simulation")
        self._reset_simulation_button.setFlat(True)
        self._reset_simulation_button.setFocusPolicy(QtCore.Qt.NoFocus)
        self._reset_simulation_button.clicked.connect(self._slots["simulation"]["stop"])
        self.addWidget(self._reset_simulation_button)

        self.addSeparator()

        label = QLabel("Run for ")
        self.addWidget(label)
        self._total_simtime_field        = QLineEdit(self)
        self._total_simtime_field.setValidator(QDoubleValidator())
        self._total_simtime_field.setFixedWidth(75)
        self.addWidget(self._total_simtime_field)
        self.addWidget(QLabel(" (s)"))
        self.addSeparator()

        self._start_simtime_label = QLabel("0123456789 s")
        self._start_simtime_label.setFixedWidth(100)
        self._start_simtime_label.setAlignment(QtCore.Qt.AlignCenter);

        self.addWidget(self._start_simtime_label)
        self._finish_simtime_label = QLabel("0123456789 s")
        self._finish_simtime_label.setFixedWidth(100)
        self._finish_simtime_label.setAlignment(QtCore.Qt.AlignCenter);

        self._remaining_realtime_field   = QProgressBar(self)
        self._remaining_realtime_field.setStyleSheet(
            """ QProgressBar
                {
                    border          : none;
                    background      : #c0c0c0;
                    color           : white;
                    text-align      : center;
                }
                QProgressBar::chunk
                {
                    background-color: #000000;
                }"""
            )
        #             # # border          : 1px solid black;
        #             # padding         : 0px;

        # self._remaining_realtime_field.setStyleSheet(
        #     """                                                    )
        self._remaining_realtime_field.setValue(50)
        self._remaining_realtime_field.setFixedWidth(400)
        self.addWidget(self._remaining_realtime_field)
        self.addWidget(self._finish_simtime_label)

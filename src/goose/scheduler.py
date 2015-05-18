from PyQt4 import Qt, QtCore, QtGui
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from utils import *


class SchedulingWidget(QToolBar):
    """docstring for Scheduler"""

    def __init__( self
                , model         = None
                , application   = None
                , parent        = None
                , signals       = None
                , slots         = None
                ):
        super(SchedulingWidget, self).__init__(parent)
        self.setFloatable(False)
        self.setMovable(False)
        self._model         = model
        self._application   = application
        self._parent        = parent
        self._signals       = signals
        self._slots         = slots
        self._create()

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

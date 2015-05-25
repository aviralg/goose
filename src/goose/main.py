import sys
import subprocess
import os
import pprint
import time
import rpyc
import socket
import errno
import itertools
import widgets
from .utils import *
from widgets import *
import imp
from .utils import *
from PyQt4 import Qt, QtCore, QtGui
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import signal
from scheduler import SimulationToolBar
import atexit
import signal
# import widgets
# from widgets import kkit
# from widgets.kkit.kkit import KineticsWidget
from widgets import *
from objectedit import ObjectEditDockWidget
# from win32process import DETACHED_PROCESS, CREATE_NEW_PROCESS_GROUP
# print(QtCore.PYQT_VERSION_STR)
# rpyc.classic.connect("0.0.0.0", "1000", keepalive = True)


class MainWindow(QMainWindow):
    simulation_run          = pyqtSignal()
    simulation_start        = pyqtSignal()
    simulation_run          = pyqtSignal()
    simulation_pause        = pyqtSignal()
    simulation_run          = pyqtSignal()
    simulation_stopped      = pyqtSignal()

    signals = { "pre"   :       { "connect"     :   pyqtSignal()
                                , "quit"        :   pyqtSignal()
                                , "fullscreen"  :   { "enable"  :   pyqtSignal()
                                                    , "disable" :   pyqtSignal()
                                                    }
                                , "menubar"     :   { "show"    :   pyqtSignal()
                                                    , "hide"    :   pyqtSignal()
                                                    }
                                , "windows"     :   { "tile"    :   pyqtSignal()
                                                    , "tabify"  :   pyqtSignal()
                                                    }
                                , "model"       :   { "open"        :   pyqtSignal(str)
                                                    , "close"       :   pyqtSignal(str)
                                                    , "create"      :   pyqtSignal(str)
                                                    , "add"         :   pyqtSignal(str, str)
                                                    , "remove"      :   pyqtSignal(str, str, str)
                                                    , "move"        :   pyqtSignal(str, str, str)
                                                    , "run"         :   pyqtSignal(int, int)
                                                    , "pause"       :   pyqtSignal(int, int)
                                                    , "stop"        :   pyqtSignal(int, int)
                                                    , "data"        :   pyqtSignal(dict)
                                                    }
                                }
              , "post"  :   { "new"         :   pyqtSignal()
                            , "open"        :   pyqtSignal()
                            , "connect"     :   pyqtSignal()
                            , "quit"        :   pyqtSignal()
                            , "fullscreen"  :   { "enable"  :   pyqtSignal()
                                                , "disable" :   pyqtSignal()
                                                }
                            , "menubar"     :   { "show"    :   pyqtSignal()
                                                , "hide"    :   pyqtSignal()
                                                }
                            , "windows"     :   { "tile"    :   pyqtSignal()
                                                , "tabify"  :   pyqtSignal()
                                                }
                            , "model"       :   { "load"        :   pyqtSignal(str)
                                                , "delete"      :   pyqtSignal(str)
                                                , "add"         :   pyqtSignal(str, str)
                                                , "remove"      :   pyqtSignal(str, str, str)
                                                , "move"        :   pyqtSignal(str, str, str)
                                                , "run"         :   pyqtSignal(object)
                                                , "pause"       :   pyqtSignal(int, int)
                                                , "stop"        :   pyqtSignal(int, int)
                                                , "data"        :   pyqtSignal(dict)
                                                }
                            }
              }
    signals["post"]["model"]["run"] = pyqtSignal(object)

    def __init__(self, application, goose_log_directory, models):
        super(MainWindow, self).__init__()
        self.goose_log_directory = goose_log_directory
        self.instances      = {}
        self.instance       = None
        self._application = application
        self.message_box    = QMessageBox(self)
        self.message_box.setStandardButtons(QMessageBox.NoButton)
        flags = self.message_box.windowFlags()
        if Qt.WindowCloseButtonHint == (flags & Qt.WindowCloseButtonHint):
            flags = flags ^ Qt.WindowCloseButtonHint
            self.message_box.setWindowFlags(flags |  Qt.FramelessWindowHint)
        atexit.register(self.stop_moose_servers)
        self._setup_global_widgets()
        self._setup_main_window()
        self._setup_central_widget()
        self._setup_signals()
        self._setup_actions()
        self._setup_slots()
        self._setup_menubar()
        self._application.aboutToQuit.connect(self.stop_moose_servers)
        self._setup_toolbars()
        [self.load_slot(model) for model in models]

    @QtCore.pyqtSlot(str)
    def busy_slot(self, message = DEFAULT_MESSAGE):
        self.message_box.setText(message)
        self.message_box.show()

    @QtCore.pyqtSlot()
    def free_slot(self):
        self.message_box.hide()

    def _setup_global_widgets(self):
        self._console = QDockWidget(self)
        self._console.setWidget(IPythonConsole( globals()
                                              , instances   = self.instances
                                              , instance    = self.instance
                                              , window      = self
                                              )
                               )
        self._console.setWindowTitle("Interactive Python Console")
        self.addDockWidget(Qt.BottomDockWidgetArea, self._console)
        self._console.hide()

        self._property_editor = ObjectEditDockWidget(self)
        self.addDockWidget(Qt.RightDockWidgetArea, self._property_editor)
        self._property_editor.hide()

    def _setup_main_window(self):
        self.setWindowTitle("GOOSE")
        self.setWindowFlags(self.windowFlags()
                           | QtCore.Qt.WindowContextHelpButtonHint
                           | QtCore.Qt.CustomizeWindowHint
                           | QtCore.Qt.WindowMinimizeButtonHint
                           | QtCore.Qt.WindowMaximizeButtonHint
                           # | QtCore.Qt.WindowStaysOnTopHint
                           )
        self.setDockOptions( QMainWindow.AnimatedDocks
                           | QMainWindow.AllowNestedDocks
                           | QMainWindow.AllowTabbedDocks
                           | QMainWindow.VerticalTabs
                           )
        self.setWindowIcon(QIcon(APPLICATION_ICON_PATH))
        self.setAcceptDrops(True)

    @QtCore.pyqtSlot(str, object)
    def show_property_slot(self, path, moose):
        self._property_editor.setObject(path, moose)

    def _setup_toolbars(self):
        self.addToolBar(SimulationToolBar(slots = self._slots, parent = self))
        pass

    def _setup_central_widget(self):
        widget = MdiArea()
        self.setCentralWidget(widget)
        # self.centralWidget.tileSubWindows()
        widget.setDocumentMode(True)
        # self.setWindowState(QtCore.Qt.WindowFullScreen)
        # self.showFullScreen()
        # background = QBrush( QColor(255, 255, 255, 255)
        #                    , QPixmap(APPLICATION_BACKGROUND_PATH)
        #                    )
        # # background.setColor()
        # centralWidget.setBackground(background)
        # w = IPythonConsole(globals())
        # w.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.FramelessWindowHint)
        # centralWidget.addSubWindow(w)
        # self.centralWidget().addSubWindow(widgets.IPythonConsole(globals()))
        # centralWidget.addSubWindow(IPythonConsole(globals() ))
        # return centralWidget

    def _setup_signals(self):
        pass

    def _setup_actions(self):

        def create_new_action():
            action = QAction("New", self)
            action.setToolTip("Create new model")
            action.setShortcut(QKeySequence(QtCore.Qt.CTRL + QtCore.Qt.Key_N))
            action.setShortcutContext(QtCore.Qt.ApplicationShortcut)
            return action

        def create_open_action():
            action = QAction("Open", self)
            action.setToolTip("Open an existing model")
            action.setShortcut(QKeySequence(QtCore.Qt.CTRL + QtCore.Qt.Key_O))
            action.setShortcutContext(QtCore.Qt.ApplicationShortcut)
            return action

        def create_connect_action():
            action = QAction("Connect", self)
            action.setToolTip("Connect to a moose instance")
            action.setShortcut(QKeySequence(QtCore.Qt.CTRL + QtCore.Qt.Key_C))
            action.setShortcutContext(QtCore.Qt.ApplicationShortcut)
            return action

        def create_quit_action():
            action = QAction("Quit", self)
            action.setToolTip("Quit")
            action.setShortcut(QKeySequence(QtCore.Qt.CTRL + QtCore.Qt.Key_Q))
            action.setShortcutContext(QtCore.Qt.ApplicationShortcut)
            return action

        def create_toggle_fullscreen_action():
            action = QAction("Enter Full Screen", self)
            action.setShortcut(QKeySequence(QtCore.Qt.Key_F11))
            action.setShortcutContext(QtCore.Qt.ApplicationShortcut)
            return action

        def create_toggle_window_arrangement_action():
            action = QAction("Tabbed View", self)
            return action

        def create_interactive_python_console_action():
            action = QAction("Interactive Python Console", self)
            action.setToolTip("Show interactive pyton console")
            action.setShortcut(QKeySequence(QtCore.Qt.CTRL + QtCore.Qt.Key_I))
            action.setShortcutContext(QtCore.Qt.ApplicationShortcut)
            return action


        # def create_toggle_menubar_action():
        #     action = QAction("Hide Menu Bar", self)
        #     action.setShortcut(QKeySequence(QtCore.Qt.Key_F10))
        #     action.setShortcutContext(QtCore.Qt.ApplicationShortcut)
        #     return action

        self.new_action     = create_new_action()
        self.open_action    = create_open_action()
        self.connect_action = create_connect_action()
        self.quit_action    = create_quit_action()
        self.toggle_fullscreen_action = create_toggle_fullscreen_action()
        self.toggle_window_arrangement_action = create_toggle_window_arrangement_action()
        self.interactive_python_console_action = create_interactive_python_console_action()

        # self.toggle_menubar_action = create_toggle_menubar_action()

    def print_simulation_data(self, data):
        import pprint
        INFO(pprint.pformat(data))

    def _run_simulation(self, total_simtime):
        self.current_model["service"].run_simulation( total_simtime
                                                    , self.print_simulation_data
                                                    )

    def _pause_simulation(self):
        self.current_model["service"].pause_simulation()

    def _stop_simulation(self):
        self.current_model["service"].stop_simulation()

    def _setup_slots(self):
        self._slots = { "simulation"    :   { "run"     :   self._run_simulation
                                            , "pause"   :   self._pause_simulation
                                            , "stop"    :   self._stop_simulation
                                            }
                      }
        self.simulation_run.connect(self.print_simulation_data)
        self.open_action.triggered.connect(self.open_slot)
        self.quit_action.triggered.connect(self._application.exit)
        self.connect_action.triggered.connect(self.connect_slot)
        self.toggle_window_arrangement_action.triggered.connect(self.toggle_window_arrangement_slot)
        self.toggle_fullscreen_action.triggered.connect(self.toggle_fullscreen_slot)
        # self.toggle_menubar_action.triggered.connect(self.toggle_menubar_slot)
        self.interactive_python_console_action.triggered.connect(self.interactive_python_console_slot)

    @pyqtSlot(object)
    def interactive_python_console_slot(self):
        # self.removeDockWidget(self._console)
        self.addDockWidget(Qt.BottomDockWidgetArea, self._console)
        self._console.show()

    @pyqtSlot(object)
    def toggle_menubar_slot(self):
        if self.menuBar().isVisible(): self.menuBar().hide()
        else: self.menuBar().show()

    @pyqtSlot(object)
    def toggle_window_arrangement_slot(self):
        if self.centralWidget().viewMode() == QMdiArea.SubWindowView:
            self.centralWidget().setViewMode(QMdiArea.TabbedView)
            self.toggle_window_arrangement_action.setText("Sub Window View")
        else:
            self.centralWidget().setViewMode(QMdiArea.SubWindowView)
            self.toggle_window_arrangement_action.setText("Tabbed View")

    @pyqtSlot(object)
    def toggle_fullscreen_slot(self):
        self.setWindowState(self.windowState() ^ Qt.WindowFullScreen)

    def _setup_menubar(self):

        def create_file_menu(menubar):
            menu = menubar.addMenu("File")
            menu.addAction(self.new_action)
            menu.addAction(self.open_action)
            menu.addAction(self.connect_action)
            menu.addAction(self.quit_action)
            return menu

        def create_view_menu(menubar):
            menu = menubar.addMenu("View")
            menu.addAction(self.toggle_fullscreen_action)
            # menu.addAction(self.toggle_menubar_action)
            menu.addAction(self.toggle_window_arrangement_action)
            return menu

        def create_widgets_menu(menubar):
            menu = menubar.addMenu("Widgets")
            menu.addAction(self.interactive_python_console_action)
            return menu

        def create_help_menu(menubar):
            menu = menubar.addMenu("Help")
            menu.addAction(self.gui_documentation_action)
            menu.addAction(self.moose_documentation_action)
            menu.addAction(self.report_bug_action)
            menu.addAction(self.request_feature_action)
            return menu

        menubar = self.menuBar()
        create_file_menu(menubar)
        create_view_menu(menubar)
        create_widgets_menu(menubar)
        # create_help_menu(menubar)

        return menubar


    def get_free_port(self):
        s = socket.socket()
        s.bind(('localhost', 0))
        port = s.getsockname()[1]
        s.close()
        return port

    def check_server(self, address, port):
        # Create a TCP socket
        s = socket.socket()
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        print "Attempting to connect to %s on port %s" % (address, port)
        try:
            s.connect((address, port))
            s.shutdown(socket.SHUT_RDWR)
            s.close()
            time.sleep(10)
            print "Connected to %s on port %s" % (address, port)
            return True
        except socket.error, e:
            print "Connection to %s on port %s failed: %s" % (address, port, e)
            return False

    def start_moose_server(self):
        port = self.get_free_port()
        host = "localhost"
        logfile = os.path.join(self.goose_log_directory, str(port) + ".log")
        open(logfile, "w").close()
        args    = ["moose-server", "-p", str(port), "--logfile", logfile]
        INFO("Starting moose server on port " + str(port))
        pid = subprocess.Popen(args).pid
        return (host, port, pid)




        # connection = rpyc.classic.connect("0.0.0.0", port, keepalive = True)
        # INFO("Connected to moose server on port " + str(port))
        # return connection

        # return None
                # time.sleep(10.0)
                # connection = rpyc.classic.connect("0.0.0.0", port, keepalive = True)
                # INFO("Connected to moose server on port " + str(port))
                # return connection

            # try:
            #     connection = rpyc.classic.connect(host, port)
            #     connection.close()
            # except:
            #     args    = ["python", GOOSE_DIRECTORY + "/rpyc_classic.py", "-p", str(port)]
            #     INFO("Starting moose server on port " + str(port))
            #     subprocess.Popen(args)
            #     time.sleep(10.0)
            #     connection = rpyc.classic.connect("0.0.0.0", port, keepalive = True)
            #     INFO("Connected to moose server on port " + str(port))
            #     return connection

    def connect_to_moose_server(self, host, port, pid, filename):
        global instance
        try:
            DEBUG("Connecting to Moose server on " + host + ":" + str(port))
            connection = rpyc.classic.connect(host, port, keepalive=True)
            INFO("Connected to Moose server on " + host + ":" + str(port))
            # if filename.endswith(".py"):
            #     sys.path.append(os.path.dirname(filename))
            #     script = imp.load_source("temp_script" ,filename)
            #     modelname = script.main(connection.modules.moose)
            # else:
            # modelname =
            # modelname = connection.root.modelname(filename)
            modelname = connection.root.load(filename)
            #modelname = "/model"
            INFO("Loaded " + modelname)
            self.instance = self.instances[modelname] = \
                { "conn"     :   connection
                , "moose"    :   connection.modules.moose
                , "pid"      :   pid
                , "host"     :   host
                , "port"     :   port
                , "model"    :   connection.modules.moose.element(modelname)
                , "service"  :   connection.root
                , "thread"   :   rpyc.BgServingThread(connection)
                }

            self._console.widget().update_namespace( instance = self.instance
                                                   , moose = self.instance["moose"]
                                                   , conn  = self.instance["conn"]
                                                   , model = self.instance["model"]
                                                   , port  = self.instance["port"]
                                                   )
            # dockWidget.widget().update_namespace( instance = self.instance
            #                                        , moose = self.instance["moose"]
            #                                        , conn  = self.instance["conn"]
            #                                        , model = self.instance["model"]
            #                                        , port  = self.instance["port"]
            #                                        )

            # # DEBUG("Creating 3D widget")
            # nkit_widget = NeuroKitWidget(self.instance)
            # self._console.widget().update_namespace(network = nkit_widget.network)
            # # nkit_widget.show()
            # DEBUG("Created 3D widget")
            # self.centralWidget().addSubWindow(nkit_widget)
            # nkit_widget.show()


            # widget = KineticsWidget(self.instance,mainWindow=self,multiScale = False)
            # self.centralWidget().addSubWindow(widget)
            # widget.show()

            # widget = NeuroKitWidget(self.instance, signals = self.signals, slot = self.kkit_slot)
            # self.centralWidget().addSubWindow(widget)
            # widget.show()

            # widget = NeuroKitWidget(self.instance, signals = self.signals, slot = self.kkit_slot, details = 1)
            # self.centralWidget().addSubWindow(widget)
            # widget.show()

            # widget = KineticsWidget( self.instance
            #                        , elecCompt = self.instance["moose"].element("/model/elec/dend_1_2")
            #                        , voxelIndex = 23,mainWindow = self,multiScale = True
            #                        )
            # self.centralWidget().addSubWindow(widget)
            # widget.show()

            # widget1 = KineticsWidget( self.instance
            #                        , elecCompt = self.instance["moose"].element("/model/elec/dend_1_2")
            #                        , voxelIndex = 0,mainWindow = self
            #                        , multiScale = True
            #                        )
            # self.centralWidget().addSubWindow(widget1)
            # widget1.show()
            widget2 = KineticsWidget( self.instance
                                   , elecCompt = self.instance["moose"].element("/model/elec/head1")
                                   , voxelIndex = 1,mainWindow = self,multiScale=True
                                   )
            self.centralWidget().addSubWindow(widget2)
            widget2.show()
            # self.kkit_slot( "/model[0]/elec[0]/apical_f_113_0[0]"
            #               , 3452
            #               )
            # widget = PlotWidget(self.instance, "/model/graphs", "Conc")
            # self.centralWidget().addSubWindow(widget)
            # widget.show()
<<<<<<< HEAD
            widget = KineticsWidget( self.instance
                                   , elecCompt = self.instance["moose"].element("/model[0]/elec[0]/dend_f_3_0[0]")
                                   , voxelIndex = 17
                                   , mainWindow = self
                                   )
            self.centralWidget().addSubWindow(widget)
            self.free_slot()
            widget.show()

=======
            #moose.le('/model/elec/')
            # widget = KineticsWidget( self.instance
            #                        , elecCompt = self.instance["moose"].element("/model[0]/elec[0]/apical_f_88_1")
            #                        , voxelIndex = 17
            #                        , mainWindow = self
            #                        , multiScale = True
            #                        )
            # self.centralWidget().addSubWindow(widget)
            # widget.show()
>>>>>>> 10a73ee618dcac86c01be1b535d32bba9cf5b3c0
            # widget.show()

            # widget = KineticsWidget( self.instance
            #                        , elecCompt = self.instance["moose"].element("/model[0]/elec[0]/soma_1_0")
            #                        , voxelIndex = 0
            #                        )
            # widget = KineticsWidget( self.instance
            #                        , elecCompt = self.instance["moose"].element("/model[0]/elec[0]/apical_e_2_0")
            #                        , voxelIndex = 1
            #                        )

            # self.centralWidget().addSubWindow(widget1)
            # widget1.show()


        except socket.error as serr:
            if serr.errno != errno.ECONNREFUSED:
                raise serr
            DEBUG("Failed to connect to Moose server on " + host + ":" + str(port))
            QTimer.singleShot(1000, lambda : self.connect_to_moose_server(host, port, pid, filename))

    def kkit_slot(self, electrical_compartment_path, index):
        widget = KineticsWidget( self.instance
                               , elecCompt = self.instance["moose"].element(electrical_compartment_path)
                               , voxelIndex = index
                               , multiScale = True
                               , mainWindow = self
                               )
        self.centralWidget().addSubWindow(widget)
        widget.show()

    def load_slot(self, filename):
        self.busy_slot()
        (host, port, pid) = self.start_moose_server()
        self.connect_to_moose_server(host, port, pid, filename)

    @pyqtSlot(object)
    def quit_slot(self):
        self.stop_moose_servers()

    def stop_moose_servers(self):
        for modelname in self.instances.keys():
            info = self.instances.pop(modelname)
            info["thread"].stop()
            INFO("Closing Moose server on " + info["host"] + ":" + str(info["port"]))
            os.kill(info["pid"], signal.SIGTERM)
        self.instance = None

        # unique_modelname(model)

        # temp = model = modelname(filename)
        # index = 1
        # while temp in self.models:
        #     index += 1
        #     temp = model + "-" + str(index)
        # self.models[temp] = { "conn"    :
        #                     , "moose"   :
        #                     }
        # model in self.models:
        # self.models[model] =


    @pyqtSlot(object)
    def connect_slot(self):
        connect_window = QDialog()
        connect_window.setWindowTitle("Connect to moose instance.")
        connect_window.setLayout(QGridLayout())
        connect_window.layout().addWidget(QLabel("Hostname"), 0, 0)
        connect_window.layout().addWidget(QLineEdit(), 0, 1)
        connect_window.layout().addWidget(QLabel("Port"), 1, 0)
        connect_window.layout().addWidget(QLineEdit(), 1, 1)
        connect_button = QPushButton("Connect")
        connect_button.setDefault(True)
        connect_window.layout().addWidget(connect_button, 2, 1, Qt.AlignRight)
        # connect_button.triggered.connect(
        #     lambda : self.connect_to_moose_server(hostname)
        #                                 )
        # hostname.text()
        # connect_window.exec_()
        # instance = self.start_instance_slot()
        # self.connect_instance_slot()
        # self.read_instance_slot()
        # self.disconnect_instance_slot()
        # self.close_instance_slot()

    def create_plot_widget(self, moose_object, field, plot_type, color):
        index = str(len(self.get_plot_widgets()))
        path = self.instance["model"].path + "/graph-" + index
        if plot_type == LINE_PLOT:
            plot_widget = LinePlotWidget( self.instance
                                        , self.instance["moose"].Neutral(path)
                                        , field
                                        )
        plot_widget.set_title_slot("Plot {index}".format(index = index))
        plot_widget.setWindowTitle(
            "Plot - {index} | {field}".format( index = index
                                             , field = FIELD_DATA[field]["name"]
                                             )
                                  )
        plot_widget.add(moose_object, color)
        self.centralWidget().addSubWindow(plot_widget)
        plot_widget.show()

    @QtCore.pyqtSlot(QPoint, object, str, str, str)
    def plot_slot( self
                 , position
                 , moose_object
                 , fields
                 , plot_type
                 , color
                 ):

        menu = QMenu()
        print("Hi =>", moose_object)
        for widget in self.get_plot_widgets(moose_object, fields):
            action = menu.addAction(
                "{title} ({field})".format( title = widget.get_title()
                                          , field = FIELD_DATA[widget.get_field()]["name"]
                                          )
                                   )
            action.triggered.connect(lambda x, w = widget : w.add(moose_object, color))
        menu.addSeparator()
        new_plot_menu = menu.addMenu("New Plot")
        for field in fields:
            action = new_plot_menu.addAction(FIELD_DATA[field]["name"])
            action.triggered.connect( lambda x, f = field: self.create_plot_widget( moose_object
                                                                                  , f
                                                                                  , plot_type
                                                                                  , color
                                                                                  )
                                    )
        menu.exec_(position)

    @QtCore.pyqtSlot(str, list)
    def get_plot_widgets(self, moose_object = None, fields = ALL_FIELDS):
        widgets = []
        for subWindow in self.centralWidget().subWindowList():
            widget = subWindow.widget()
            if isinstance(widget, PlotWidget) and widget.get_field() in fields:
                if moose_object is None:
                    widgets.append(widget)
                elif not widget.exists(moose_object):
                    widgets.append(widget)
        return widgets

    @pyqtSlot(object)
    def open_slot(self):
        def generate_filter(extensions):
           return "(" + " ".join([ "*." + extension for extension in extensions]) + ")"

        nameFilters = [ "All Supported Files "
                      + generate_filter(list(set(itertools.chain(*EXTENSIONS.values()))))
                      ]

        for format_name, extensions in EXTENSIONS.items():
            nameFilters.append( format_name + " " + "Files " + generate_filter(extensions))

        # sbml_filter      = "SBML Files "    + generate_filter(SBML_EXTENSION)
        # python_filter    = "Python Files "  + generate_filter(PYTHON_EXTENSION)
        # cspace_filter    = "CSPACE Files "  + generate_filter(CSPACE_EXTENSION)
        # genesis_filter   = "Genesis Files " + generate_filter(GENESIS_EXTENSION)
        # neuroml_filter   = "NeuroML Files " + generate_filter(NEUROML_EXTENSION)
        # all_filter       = "All Supported Files " + generate_filter(ALL_EXTENSION)

        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.ExistingFiles)
        dialog.setNameFilters(nameFilters)
        files = dialog.selectedFiles() if dialog.exec_() else []
        # self.progress_bar = QProgressBar()
        # self.progress_bar.setRange(0,0)
        # self.progress_bar.show()
        for filename in files:
                DEBUG(filename)
                QTimer.singleShot(0, lambda target = filename: self.load_slot(target))
        # map(self.load_slot, files)
        # menus["view"].addAction(createFullScreenAction(menubar, self))
        # menus["view"].addAction(createHideMenuBarAction(menubar, menubar))
        # menus["file"].addAction(createFileOpenAction)
        # # fullscreen.triggered.connect(self.showFullScreen)
        # return (menubar, menus)


def portgen(self):
    port = 65535
    hostname = "localhost"
    while port > 0:
        try:
            connection = rpyc.classic.connect(hostname, port)
            connection.close()
            port -= 1
        except:
            yield port

"""Contains multi document interface window implementation for the MainWindow.
"""

class MdiArea(QMdiArea):
    """Multi Document Interface window. Allows any number of child widgets
       to be displayed in a tiled or tabified manner.
    """
    def __init__(self):
        super(MdiArea, self).__init__()
        self._background_image = QImage(APPLICATION_BACKGROUND_IMAGE_PATH)
        self._background      = None

    def resizeEvent(self, event):
        """Called every time the window is resized.
           Resizes and shows the moose image in the background.
           Source : http://qt-project.org/faq/answer/when_setting_a_background_pixmap_for_a_widget_it_is_tiled_if_the_pixmap_is_
        """
        self._background = QImage( event.size()
                                 , QImage.Format_ARGB32_Premultiplied
                                 )
        painter = QPainter(self._background)
        painter.fillRect( self._background.rect()
                        , QColor(255, 255, 255, 255)
                        )
        scaled = self._background_image.scaled( event.size()
                                              , QtCore.Qt.KeepAspectRatio
                                              )
        scaled_rect = scaled.rect()
        scaled_rect.moveCenter(self._background.rect().center())
        painter.drawImage(scaled_rect, scaled)
        self.setBackground(QBrush(self._background))
        super(MdiArea, self).resizeEvent(event)

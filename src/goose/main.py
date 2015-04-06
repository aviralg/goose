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
from PyQt4 import Qt, QtCore, QtGui
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import signal
from scheduler import SchedulingWidget

# from win32process import DETACHED_PROCESS, CREATE_NEW_PROCESS_GROUP
# print(QtCore.PYQT_VERSION_STR)
# rpyc.classic.connect("0.0.0.0", "1000", keepalive = True)

class MainWindow(QMainWindow):
    simulation_run = pyqtSignal()
    signals = { "pre"  :   { "connect"     :   pyqtSignal()
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
        self.instance   = None
        self.instances  = {}
        self._application = application
        self._setup_main_window()
        self._setup_central_widget()
        self._setup_signals()
        self._setup_actions()
        self._setup_slots()
        self._setup_menubar()
        self._application.aboutToQuit.connect(self.stop_moose_servers)
        self._setup_toolbars()
        [self.load_slot(model) for model in models]

    def _setup_main_window(self):
        self.setWindowTitle("Moose")
        self.setWindowFlags(self.windowFlags()
                           | QtCore.Qt.WindowContextHelpButtonHint
                           | QtCore.Qt.CustomizeWindowHint
                           | QtCore.Qt.WindowMinimizeButtonHint
                           | QtCore.Qt.WindowMaximizeButtonHint
                           )
        self.setDockOptions( QMainWindow.AnimatedDocks
                           | QMainWindow.AllowNestedDocks
                           | QMainWindow.AllowTabbedDocks
                           | QMainWindow.ForceTabbedDocks
                           | QMainWindow.VerticalTabs
                           )
        self.setWindowIcon(QIcon(APPLICATION_ICON_PATH))
        self.setAcceptDrops(True)

    def _setup_toolbars(self):
        self.addToolBar(SchedulingWidget(slots = self._slots))

    def _setup_central_widget(self):
        widget = MdiArea()
        self.setCentralWidget(widget)
        # self.centralWidget.tileSubWindows()
        widget.setViewMode(QMdiArea.TabbedView)
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
        # centralWidget.addSubWindow(IPythonConsole(globals()))
        # centralWidget.addSubWindow(IPythonConsole(globals()))
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

        self.new_action     = create_new_action()
        self.open_action    = create_open_action()
        self.connect_action = create_connect_action()
        self.quit_action    = create_quit_action()


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

    def _setup_menubar(self):

        def create_file_menu(menubar):
            menu = menubar.addMenu("File")
            menu.addAction(self.new_action)
            menu.addAction(self.open_action)
            menu.addAction(self.quit_action)
            return menu

        def create_view_menu(menubar):
            menu = menubar.addMenu("View")
            menu.addAction(self.toggle_fullscreen_action)
            menu.addAction(self.hide_menubar_action)
            menu.addAction(self.toggle_window_arrangement_action)
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
        # create_view_menu(menubar)
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

    def modelname(self, filename):
        return os.path.splitext(os.path.basename(filename))[0]

    def unique_modelname(self, filename):
        temp = modelname = self.modelname(filename)
        index = 0
        while temp in self.models:
            index += 1
            temp = modelname + "[" + str(index) + "]"
        return modelname

    def connect_to_moose_server(self, host, port, pid, filename):
        try:
            DEBUG("Connecting to Moose server on " + host + ":" + str(port))
            connection = rpyc.classic.connect(host, port)
            INFO("Connected to Moose server on " + host + ":" + str(port))
            modelname = self.unique_modelname(filename)
            connection.modules.moose.load(filename, modelname)
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
            # sys.modules["moose"] = connection.modules.moose
            # import widgets.kkit
            # DEBUG(id(connection.modules.moose))
            self.centralWidget().addSubWindow(
                widgets.kkit.KineticsWidget(self.instance)
                                             )

        except socket.error as serr:
            if serr.errno != errno.ECONNREFUSED:
                raise serr
            DEBUG("Failed to connect to Moose server on " + host + ":" + str(port))
            QTimer.singleShot(2000, lambda : self.connect_to_moose_server(host, port, pid, filename))

    def load_slot(self, filename):
        (host, port, pid) = self.start_moose_server()
        self.connect_to_moose_server(host, port, pid, filename)

    def stop_moose_servers(self):
        for modelname, info in self.models.items():
            INFO("Closing Moose server on " + info["host"] + ":" + str(info["port"]))
            os.kill(info["pid"], signal.SIGTERM)

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
        map(self.load_slot, files)

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

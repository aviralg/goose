from __future__ import unicode_literals
import sys
import os
import random
import csv
from PyQt4 import Qt, QtGui, QtCore

from PyQt4.QtGui import *
from PyQt4.QtCore import *
from matplotlib.lines import Line2D
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
from matplotlib.figure import Figure
import numpy
from goose.utils import *

class PlotWidget(QWidget):
    def __init__( self
                , instance
                , container
                , field
                , parent        = None
                , figure_width  = 5.0
                , figure_height = 4.0
                , dpi           = 100
                , facecolor     = ""
                , legend_alpha  = 0.5
                ):
        QWidget.__init__(self)
        self.instance       = instance
        self.moose          = instance["moose"]
        self.container      = container
        self.field          = field
        self.figure_width   = figure_width
        self.figure_height  = figure_height
        self.dpi            = dpi
        self.grid_visible   = False
        self.legend_visible = True
        self.facecolor = facecolor
        self.legend_alpha = legend_alpha
        self._setup_prelude()
        self._setup_plot_canvas()
        self._setup_navigation_toolbar()
        self._setup_actions()
        self._setup_context_menu()
        self._setup_signal_slot_connections()
        self._setup_postlude()
        # self.remove()


    # def _read_tables(self):
    #     for table in self.container.children():
    #         object_name = table.neighbors["requestOut"][0][0].name
    #         field       = table["neighbors"][]



    def get_title(self):
        return self.axes.get_title()

    @QtCore.pyqtSlot(str)
    def set_title_slot(self, title):
        self.axes.set_title(title)

    def get_field(self):
        return self.field

    def add(self, moose_object, color = AUTOMATIC):
        table_name = self._object_path_to_table_name(moose_object.path)
        table_path = self.container.path + "/" + table_name
        if self.moose.exists(table_path): return
        table = self.create_table(table_path)
        line = self.axes.plot( numpy.array([])
                             , numpy.array([])
                             , label = moose_object.name
                             , gid   = table_name
                             )[0]
        print(color)
        if color is not AUTOMATIC : line.set_color(color)
        self._create_legend()

    def _setup_prelude(self):
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.setLayout(QGridLayout())

        # self.CONC  = 0
        # self.N     = 1
        # self.VM    = 2
        # self.IM    = 3
        # self.SPIKE = 4
        # self.table_class_map = { self.CONC  :   self.moose.Table2
        #                        , self.N     :   self.moose.Table2
        #                        , self.VM    :   self.moose.Table
        #                        , self.IM    :   self.moose.Table
        #                        , self.SPIKE :   self.moose.Table
        #                        }
        # self.plot_variable_map = { CONC
        #                          ,
        #                          }
        # self._set_field(field)
        # plotTables = list(self.moose.wildcardFind(self.graph.path + '/##[TYPE=Table]'))
        # plotTables.extend(self.moose.wildcardFind(self.graph.path + '/##[TYPE=Table2]'))
        # self._fields = { "conc"     : ("Conc", "mM"  , "Concentration (mM)")
        #                , "n"        : ("N"   , ""    , "Number of Molecules")
        #                , "vm"       : ("Vm"  , "mV"  , "Membrane Voltage (mV)")
        #                , "im"       : ("Im"  , "mA"  , "Membrane Current (mA)")
        #                , "time"     : (""    , "s"   , "Time (s)")
        #                }

    def _setup_postlude(self):
        pass

    def _setup_plot_canvas(self):
        self.figure = Figure( ( self.figure_width
                              , self.figure_height
                              )
                            , dpi       = self.dpi
                            , facecolor = '#F3EFEE'
                            )
        self.canvas = FigureCanvas(self.figure)
        self.layout().addWidget(self.canvas, 0, 0)
        self.axes = self.figure.add_subplot(1, 1, 1)
        self.legend = None
        self._set_field(self.field)

    def _create_legend(self):
        self.legend = self.axes.legend( loc='upper right'
                                      , prop= {'size' : 10 }
                                      # , bbox_to_anchor=(1.0, 0.5)
                                      , fancybox = True
                                      , shadow=False
                                      , ncol=1
                                      )
        self.legend.draggable()
        self.legend.get_frame().set_alpha(self.legend_alpha)
        if self.legend_visible:
            self.show_legend_slot()
        else:
            self.hide_legend_slot()


    def _setup_navigation_toolbar(self):
        self.navigation_toolbar = NavigationToolbar(self.canvas, self)
        self.layout().addWidget(self.navigation_toolbar, 1, 0)

    def _setup_actions(self):

        self.toggle_grid_action      = QAction(self)
        self.toggle_grid_action.setText("Show Grid")

        self.toggle_autoscale_action = QAction(self)
        self.toggle_autoscale_action.setText("Enable Autoscaling")

        self.toggle_axis_hold_action = QAction(self)
        self.toggle_axis_hold_action.setText("Hold Axes")

        self.toggle_legend_action    = QAction(self)
        self.toggle_legend_action.setText("Hide Legend")

        self.export_to_csv_action    = QAction(self)
        self.export_to_csv_action.setText("CSV")

    def _setup_signal_slot_connections(self):
        self.canvas.mpl_connect('pick_event', self.pick_event_slot)
        self.toggle_grid_action.triggered.connect(self.toggle_grid_slot)
        self.toggle_autoscale_action.triggered.connect(self.toggle_autoscale_slot)
        self.toggle_axis_hold_action.triggered.connect(self.toggle_axis_hold_slot)
        self.toggle_legend_action.triggered.connect(self.toggle_legend_slot)
        self.export_to_csv_action.triggered.connect(self.export_to_csv_slot)
        self.connect( self
                    , SIGNAL("customContextMenuRequested(QPoint)")
                    , self
                    , SLOT("show_context_menu_slot(QPoint)")
                    )

    @QtCore.pyqtSlot()
    def draw_slot(self):
        self.canvas.draw()

    def pick_event_slot(self, event):
        pass

    def show_grid_slot(self):
        self.axes.grid(True)
        self.toggle_grid_action.setText("Hide Grid")
        self.draw_slot()

    def hide_grid_slot(self):
        self.axes.grid(False)
        self.toggle_grid_action.setText("Show Grid")
        self.draw_slot()

    def toggle_grid_slot(self):
        self.hide_grid_slot() if self.grid_visible else self.show_grid_slot()
        self.grid_visible = not self.grid_visible

    def toggle_autoscale_slot(self):
        pass

    def toggle_axis_hold_slot(self):
        pass

    def show_legend_slot(self):
        if self.legend is None : return
        self.legend.set_visible(True)
        self.toggle_legend_action.setText("Hide Legend")
        self.draw_slot()

    def hide_legend_slot(self):
        if self.legend is None : return
        self.legend.set_visible(False)
        self.toggle_legend_action.setText("Show Legend")
        self.draw_slot()

    def toggle_legend_slot(self):
        self.hide_legend_slot() if self.legend_visible else self.show_legend_slot()
        self.legend_visible = not self.legend_visible


    def _set_field(self, field):
        self.axes.set_xlabel("Time (s)")
        self.axes.set_ylabel( "{name} ({unit})".format( name = FIELD_DATA[field]["name"]
                                                      , unit = FIELD_DATA[field]["unit"]
                                                      )
                            )
        # (self._field, self._unit, self._y_label) = self._fields[field.lower()]
        # self.


    @pyqtSlot(QtCore.QPoint)
    def show_context_menu_slot(self, point):
        self.context_menu.exec_(self.mapToGlobal(point))

    def _setup_context_menu(self):

        self.context_menu = QMenu()

        self.context_menu.addAction(self.toggle_grid_action)

        self.context_menu.addAction(self.toggle_autoscale_action)

        self.context_menu.addAction(self.toggle_axis_hold_action)

        self.context_menu.addAction(self.toggle_legend_action)

        export_menu = self.context_menu.addMenu("Export")
        export_menu.addAction(self.export_to_csv_action)

    def toggle_line_visibility_slot(self, line):
        line.set_visible(not line.get_visible())

    def _table_name_to_object_name(self, table_name):
        return self._table_name_to_object_path(table_name).rsplit("/", 1)[-1]

    def _object_path_to_table_name(self, object_path):
        return object_path.replace("/", "@").replace("[", "<").replace("]", ">")

    def _table_name_to_object_path(self, table_name):
        return table_name.replace("@", "/").replace("<", "[").replace(">", "]")

    # def _table_class(self):
    #     y_field =
    #     return  [self._y_field()]

    def create_table(self, table_path):
        return self.moose.__dict__[FIELD_DATA[self.field]["table"]](table_path)

    def remove_plot(self):
        pass

    @QtCore.pyqtSlot(str)
    def export_to_csv_slot(self, filepath):
        with open(filepath,"wb") as csv_file:
            writer = csv.writer( csv_file
                               , delimiter  = ' '
                               , quotechar  = '"'
                               , fieldnames = ["Time"] + self._tables.keys()
                               , quoting    = csv.QUOTE_NONNUMERIC
                               )
            writer.writerow(["#MODEL             : {model}".format(model = self.instance["model"])])
            writer.writerow(["#TIMESTAMP         : {timestamp}".format(timestamp = int(time.time()))])
            writer.writerow(["#MOOSE VERSION     : {moose_version}".format(moose_version = "123")])
            writer.writerow(["#GOOSE VERSION     : {goose_version}".format(goose_version = "456")])
            writer.writeheader()
            units = ["s"] + [self._unit] * len(self._tables)
            writer.writerow(units)
            data = [ value.get_ydata() for value in self._tables.values() ]
            data = data + data[0].get_xdata()
            data = transpose(data)
            writer.writerows(data)

        #     for table_name, line in self.tables.items():
        #         object_name = self._table_name_to_object_name(table_name)
        #         y_data      = line.get_ydata();
        #         writer.writerow()
        # """Save selected plot data in CSV file"""
        # src = self.lineToDataSource[line]
        # xSrc = moose.element(src.x)
        # ySrc = moose.element(src.y)
        # y = ySrc.vector.copy()
        # if isinstance(xSrc, moose.Clock):
        #     x = np.linspace(0, xSrc.currentTime, len(y))
        # elif isinstance(xSrc, moose.Table):
        #     x = xSrc.vector.copy()
        # filename = str(directory)+'/'+'%s.csv' % (ySrc.name)
        # np.savetxt(filename, np.vstack((x, y)).transpose())
        # print 'Saved data from %s and %s in %s' % (xSrc.path, ySrc.path, filename)
    def closeEvent(self, event):
        self.moose.delete(self.container.path)

class LinePlotWidget(PlotWidget):

    @QtCore.pyqtSlot(object)
    def update_plots_slot(self, simdata):
        for line in self.axes.lines :
            self.update_plot_slot( line
                                 , simdata["time"]["current"]
                                 , simdata["tables"][line.get_gid()]
                                 )

    # @QtCore.pyqtSlot(Line2D, numpy.array, numpy.array)
    def update_plot_slot(self, line, simtime, ydata):
        xdata = numpy.linspace( 0.0
                              , simtime
                              , len(ydata)
                              )
        line.set_xdata(xdata)
        line.set_ydata(ydata)


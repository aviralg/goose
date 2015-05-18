from __future__ import nested_scopes
from __future__ import generators
from __future__ import division
from __future__ import absolute_import
from __future__ import with_statement
from __future__ import print_function
from __future__ import unicode_literals

import pkg_resources
import os
from time import strftime, localtime
import goose

APPLICATION_BACKGROUND_IMAGE_PATH   = pkg_resources.resource_filename(
    goose.__name__ , "data/images/moose.png"
                                                                     )

APPLICATION_ICON_PATH               = pkg_resources.resource_filename(
    goose.__name__ , "data/icons/moose-icon.png"
                                                                     )

RUN_SIMULATION_ICON_PATH            = pkg_resources.resource_filename(
    goose.__name__ , "data/icons/play.svg"
                                                                     )

STOP_SIMULATION_ICON_PATH           = pkg_resources.resource_filename(
    goose.__name__ , "data/icons/pause.svg"
                                                                     )

RESET_SIMULATION_ICON_PATH          = pkg_resources.resource_filename(
    goose.__name__ , "data/icons/stop.svg"
                                                                     )

FUNCTION_IMAGE_PATH                 = pkg_resources.resource_filename(
    goose.__name__ , "data/images/Function.png"
                                                                     )

RAINBOW_COLORMAP_PATH               = pkg_resources.resource_filename(
    goose.__name__ , "data/colormaps/rainbow.pkl"
                                                                     )
PLOT_ICON_PATH          = pkg_resources.resource_filename(
    goose.__name__ , "data/icons/plot.svg"
                                                                      )
CLONE_ICON_PATH          = pkg_resources.resource_filename(
    goose.__name__ , "data/icons/clone.svg"
                                                                      )
DELETE_ICON_PATH          = pkg_resources.resource_filename(
    goose.__name__ , "data/icons/delete.svg"
                                                                      )
MOVE_ICON_PATH          = pkg_resources.resource_filename(
    goose.__name__ , "data/icons/move.svg"
                                                                      )
EXTENSIONS          = { "SBML"      :   ["xml"]
                      , "Python"    :   ["py"]
                      , "CSPACE"    :   ["cspace"]
                      , "Genesis"   :   ["g"]
                      , "NeuroML"   :   ["nml", "xml"]
                      , "SWC"       :   ["swc"]
                      }

CHEMICAL_PLOT_CLOCK_IDS             = [18]
CHEMICAL_SIMULATION_CLOCK_IDS       = range(11, 18)

ELECTRICAL_PLOT_CLOCK_IDS           = [8]
ELECTRICAL_SIMULATION_CLOCK_IDS     = range(0, 8)

AUTOMATIC           = "AUTOMATIC"

LINE_PLOT           = "LINE PLOT"
SCATTER_PLOT        = "SCATTER PLOT"

TIME                = "TIME"
CONCENTRATION       = "CONCENTRATION"
MOLECULES           = "MEOLCULES"
MEMBRANE_VOLTAGE    = "MEMBRANE VOLTAGE"
MEMBRANE_CURRENT    = "MEMBRANE CURRENT"

ALL_FIELDS = [ CONCENTRATION
             , MOLECULES
             , MEMBRANE_VOLTAGE
             , MEMBRANE_CURRENT
             ]

FIELD_DATA   =   { CONCENTRATION        :   { "name"        :   "Concentration"
                                            , "moose_field" :   "getConc"
                                            , "unit"        :   "mM"
                                            }
                 , MOLECULES            :   { "name"        :   "Molecules"
                                            , "moose_field" :   "getN"
                                            , "unit"        :   None
                                            }
                 , MEMBRANE_VOLTAGE     :   { "name"        :   "Concentration"
                                            , "moose_field" :   "getVm"
                                            , "unit"        :   "mV"
                                            }
                 , MEMBRANE_CURRENT     :   { "name"        :   "Membrane Current"
                                            , "moose_field" :   "getIm"
                                            , "unit"        :   "mA"
                                            }
                 , TIME                 :   { "name"        :   "Time"
                                            , "moose_field" :   "getTime"
                                            , "unit"        :   "s"
                                            }
                 }

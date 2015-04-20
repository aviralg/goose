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

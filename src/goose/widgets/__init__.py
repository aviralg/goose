from .console import IPythonConsole
from .kkit.kkit import KineticsWidget
from .nkit.__main__ import NeuroKitWidget
from .plots.plot import LinePlotWidget, PlotWidget

__all__ = [ "IPythonConsole"
		  , "KineticsWidget"
          , "NeuroKitWidget"
          , "LinePlotWidget"
          , "PlotWidget"
		  ]

#from kkit import KineticsWidget
# from .kkit import KineticsWidget

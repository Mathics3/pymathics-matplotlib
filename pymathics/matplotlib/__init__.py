# -*- coding: utf-8 -*-
"""
PyMathics MatPlotLib module.
"""

import os
from pymathics.matplotlib.version import __version__
from pymathics.matplotlib.__main__ import ToMatplotlib, MPlot # noqa

__all__ = ("__version__", "ToMatplotlib", "MPlot", "pymathics_version_data")

# To be recognized as an external mathics module, the following variable
# is required:
#
pymathics_version_data = {
    "author": "The Mathics Team",
    "version": __version__,
    "requires": [],
}

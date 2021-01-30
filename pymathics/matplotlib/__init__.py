# -*- coding: utf-8 -*-
"""
PyMathics MatPlotLib module.
"""

import os
from pymathics.matplotlib.version import __version__
from pymathics.matplotlib.__main__ import MPLGraphicsBox
#MPLExportGraphics, MPLShow, MPLExportGraphicsToString # noqa

__all__ = ("__version__", "MPLGraphicsBox", "pymathics_version_data")
#__all__ = ("__version__", "MPLExportGraphicsToString", "MPLExportGraphics", "MPLShow", "pymathics_version_data")

# To be recognized as an external mathics module, the following variable
# is required:
#
pymathics_version_data = {
    "author": "The Mathics Team",
    "version": __version__,
    "requires": [],
}



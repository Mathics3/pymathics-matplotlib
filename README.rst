pymathics-matplotlib
====================

A PyMathics module to use matplotlib as a rendering engine
for Graphics in Mathics.

To install in development mode, run from the source tree::

    $ make develop

Once installed, you can load this inside Mathics using the
``LoadModule[]`` function.

This makes the functions ``ToMatplotlib[]`` and ``MPlot[]`` available.

::

      $ mathicsscript
      In[1]:= MPlot[ToMatplotlib[Line[{{0.25,0.5},{0.25,0.25},{0.5,0.25},{0.5,0.5}}]]]

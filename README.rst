PyMathics module to use matplotlib as a rendering endgine for Graphics.

To install in development mode (run code from the source tree):

::

   $ make develop


After installing inside Mathics you can load this using the
``LoadModule[]`` function.

Then to the function ``Pymathics\`Hello[]`` and the variable ``PyMathics\`$HelloUser`` will be available.

::

      $ mathicsscript
      In[1]:= MPlot[ToMatplotlib[Line[{{0.25,0.5},{0.25,0.25},{0.5,0.25},{0.5,0.5}}]]]

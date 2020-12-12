# -*- coding: utf-8 -*-
import matplotlib.lines as lines
from mathics.builtin.base import Builtin, String
from mathics.core.expression import Expression
import matplotlib.pyplot as plt

class ToMatplotlib(Builtin):
    """
    <dl>
      <dt>'ToMatplotlib'[$expr$]
      <dd>Convert $expr$ in patplotlib.
    </dl>
    >> PyMathics`ToMatplotlib[Line[{{0.25,0.5},{0.25,0.25},{0.5,0.25},{0.5,0.5}}]]
    """
    def __init__(self, *args, **kwargs):
        super(Builtin, self).__init__()
        self.fig, self.ax = plt.subplots()

    def apply(self, expr, evaluation):
        "%(name)s[expr_]"
        return self.to_matplotlib(expr)

    def to_matplotlib(self, graphics_expr, *args, **kwargs):
        """
        Convert the Expression to a Matplotlib object:
        """
        head_name = graphics_expr._head.get_name()
        if head_name == "System`Line":
            self.matplotlib = self.add_line(graphics_expr)
        return graphics_expr

    def add_line(self, graphics_expr):
        # Remove Expr[Line ... ]]
        points = graphics_expr.leaves[0].to_python()
        xdata = [p[0] for p in points]
        ydata = [p[1] for p in points]
        graphics_expr.line = lines.Line2D(xdata, ydata)
        self.ax.add_line(graphics_expr.line)

    def apply_boxes(self, expr, evaluation) -> Expression:
        'ToMatplotlib[expr_, PythonForm]'
        return self.apply(expr, evaluation)


class MPlot(Builtin):
    """
    <dl>
      <dt>'MPLot'[$expr$]
      <dd>Convert $expr$ in matplotlib.
    </dl>
    >> PyMathics`ToMatplotlib[Line[{{0.25,0.5},{0.25,0.25},{0.5,0.25},{0.5,0.5}}]]
    """
    def apply(self, expr, evaluation):
        "%(name)s[expr_]"
        plt.show()
        return expr

# -*- coding: utf-8 -*-
import matplotlib.lines as lines
from mathics.builtin.base import Builtin, String
from mathics.core.expression import Expression
from mathics.core.rules import Rule
import matplotlib.pyplot as plt

class ToMatplotlib(Builtin):
    """
    <dl>
      <dt>'ToMatplotlib'[$expr$]
      <dd>Convert $expr$ to matplotlib.
    </dl>
    >> PyMathics`ToMatplotlib[Line[{{0.25,0.5},{0.25,0.25},{0.5,0.25},{0.5,0.5}}]]
    """

    def __init__(self, *args, **kwargs):
        super(Builtin, self).__init__()
        self.fig, self.ax = plt.subplots()

    def apply(self, expr, evaluation):
        "%(name)s[expr_]"
        return self.to_matplotlib(expr, evaluation)

    def to_matplotlib(self, graphics_expr, evaluation):
        """
        Convert the Expression to a Matplotlib object:
        """
        head_name = graphics_expr._head.get_name()
        if head_name == "System`Line":
            self.matplotlib = self.add_line(graphics_expr)
        elif head_name == "System`Rule":
            option_name, option_value = graphics_expr.leaves
            option_fn = self.option_name_to_fn.get(option_name.get_name(), None)
            if option_fn:
                option_fn(self, option_value, evaluation)
        return graphics_expr

    def add_line(self, graphics_expr):
        # Remove Expr[Line ... ]]
        points = graphics_expr.leaves[0].to_python()
        xdata = [p[0] for p in points]
        ydata = [p[1] for p in points]
        graphics_expr.line = lines.Line2D(xdata, ydata)
        self.ax.add_line(graphics_expr.line)

    def axes_aspect_ratio(self, aspect_ratio_value, evaluation):
        aspect_ratio = Expression('N', aspect_ratio_value).evaluate(evaluation).to_python()
        self.ax.set_box_aspect(aspect_ratio)

    def apply_boxes(self, expr, evaluation) -> Expression:
        'ToMatplotlib[expr_, PythonForm]'
        return self.apply(expr, evaluation)

    option_name_to_fn = {
        "System`AspectRatio": axes_aspect_ratio,
    }





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

if __name__ == "__main__":
    from mathics.session import MathicsSession
    session = MathicsSession(add_builtin=True, catch_interrupt=False)
    session.evaluate(
        """
        LoadModule["pymathics.matplotlib"];
        MPlot[PyMathics`ToMatplotlib[AspectRatio -> 1 / GoldenRatio]];
        MPlot[PyMathics`ToMatplotlib[Line[{{0.25,0.5},{0.25,0.25},{0.5,0.25},{0.5,0.5}}]]]
        """
    )

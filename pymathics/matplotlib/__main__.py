# -*- coding: utf-8 -*-
import matplotlib.lines as lines
from mathics.builtin.base import Builtin, String
from mathics.core.expression import Expression
from mathics.core.rules import Rule
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.collections import PatchCollection

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

    def apply(self, expr, evaluation):
        "%(name)s[expr__]"
        self.fig, self.ax = plt.subplots()
        for e in expr.get_sequence():
            result = self.to_matplotlib(expr, evaluation)
        return result

    def to_matplotlib(self, graphics_expr: Expression, evaluation) -> None:
        """
        read and plot `graphics_expr` updating the state of `plt`.
        """
        head_name = graphics_expr._head.get_name()
        if head_name == "System`Line":
            self.matplotlib = self.add_line(graphics_expr)
        elif head_name == "System`Rule":
            option_name, option_value = graphics_expr.leaves
            option_fn = self.option_name_to_fn.get(option_name.get_name(), None)
            if option_fn:
                option_fn(self, option_value, evaluation)
        elif head_name == "System`Rectangle":
            print(graphics_expr.leaves)
            if len(graphics_expr.leaves) == 1:
                xmin, ymin = graphics_expr.leaves[0].to_python()
                xy = [0.0, 0.0]
                width = 1.0
                height = 1.0
                if (xmin, ymin) != (0, 0):
                    assert not hasattr(xmin, "len")
                    width = (1.0 - xmin)
                    xy[0] = 0
                    assert not hasattr(ymin, "len")
                    height = (1.0 - ymin)
                    # In the specification (0,0) is the upper left and
                    # xy is lower right. In plotting xy should be the
                    # *upper* right and lower right y value should be 0
                    xy[1] = 0
            else:
                xy, max_p = [l.to_python() for l in graphics_expr.leaves]
                width = xy[0] + max_p[0]
                height = xy[0] + max_p[1]

            print("xy=", xy, "height=", height, "width=", width)

            # add a rectangle
            patches = []
            rectangle = mpatches.Rectangle(xy, width=width, height=height)
            patches.append(rectangle)

            # FIXME: we probably need to reoganize this to arrange to do it once at the end
            collection = PatchCollection(patches)
            self.ax.add_collection(collection)

        elif head_name == "System`Circle":
            print(graphics_expr.leaves)
            patches = []
            rectangle = mpatches.Circle(xy = (0.5,0.5), radius = 0.25)
            patches.append(rectangle)
            collection = PatchCollection(patches)
            self.ax.add_collection(collection)

        elif head_name == "System`Polygon":
            print(graphics_expr.leaves)
            points = graphics_expr.leaves[0].to_python()
            # Close file by adding a line from the last point to the first one
            points.append(points[0])
            matplotlib_polygon(points)

        return graphics_expr

    def add_line(self, graphics_expr):
        # Convert leaves to points...

        # Remove Expr[Line ... ]]
        points = graphics_expr.leaves[0].to_python()

        xdata = [p[0] for p in points]
        ydata = [p[1] for p in points]
        graphics_expr.line = lines.Line2D(xdata, ydata)
        self.ax.add_line(graphics_expr.line)

    def axes_aspect_ratio(self, aspect_ratio_value, evaluation):
        aspect_ratio = (
            Expression("N", aspect_ratio_value).evaluate(evaluation).to_python()
        )
        self.ax.set_box_aspect(aspect_ratio)

    def apply_boxes(self, expr, evaluation) -> Expression:
        "ToMatplotlib[expr_, PythonForm]"
        return self.apply(expr, evaluation)

    option_name_to_fn = {
        "System`AspectRatio": axes_aspect_ratio,
    }


def matplotlib_polygon(points):
    print(points)
    xdata = [p[0] for p in points]
    ydata = [p[1] for p in points]
    plt.fill(xdata, ydata)


class MPlot(Builtin):
    """
    <dl>
      <dt>'MPLot'[$expr$]
      <dd>Convert $expr$ in matplotlib.
    </dl>

    >> PyMathics`ToMatplotlib[Line[{{0.25,0.5},{0.25,0.25},{0.5,0.25},{0.5,0.5}}]]
    """

    # This is copied Graphics in graphics.py
    # DRY the two
    options = {
        "Axes": "False",
        "TicksStyle": "{}",
        "AxesStyle": "{}",
        "LabelStyle": "{}",
        "AspectRatio": "Automatic",
        "PlotRange": "Automatic",
        "PlotRangePadding": "Automatic",
        "ImageSize": "Automatic",
        "Background": "Automatic",
        "$OptionSyntax": "Ignore",
    }

    def apply(self, expr, evaluation, options):
        "%(name)s[expr_, OptionsPattern[%(name)s]]"
        ticks_style = options.get('System`TicksStyle').to_python()
        axes_style = options.get('System`AxesStyle').to_python()
        if not axes_style:
            plt.axis("off")
        plt.show()
        return expr


if __name__ == "__main__":
    from mathics.session import MathicsSession

    session = MathicsSession(add_builtin=True, catch_interrupt=False)
    session.evaluate(
        """
        LoadModule["pymathics.matplotlib"];
        MPlot[ToMatplotlib[AspectRatio -> 1 / GoldenRatio]];
        MPlot[ToMatplotlib[Line[{{0.25,0.5},{0.25,0.25},{0.5,0.25},{0.5,0.5}}]]]
        MPlot[ToMatplotlib[Rectangle[{0, 0.5}]], AxesStyle->False]
        """
    )

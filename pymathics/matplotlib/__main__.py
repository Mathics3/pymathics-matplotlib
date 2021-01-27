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
        fig, ax = plt.subplots()
        evaluation.current_mpl_context = {"fig": fig,
                                          "ax": ax,
                                          "patches": [],
                                          "options": "",
                                          "brush": {
                                              "color": "black",
                                              "thickness": "auto",
                                              "style": "-"
                                          },
        }
        for e in expr.get_sequence():
            print("e=", e.get_head_name())
            result = self.to_matplotlib(e, evaluation)
        return result

    def to_matplotlib(self, graphics_expr: Expression, evaluation) -> None:
        """
        read and plot `graphics_expr` updating the state of `plt`.
        """
        ax = evaluation.current_mpl_context["ax"]
        patches = evaluation.current_mpl_context["patches"]
        brush = evaluation.current_mpl_context["brush"]
        head_name = graphics_expr._head.get_name()
        if head_name in ("System`Graphics",
                         "System`GraphicsBox",
                         "System`List"):
            for leaf in graphics_expr.get_leaves():
                print("   leaf=", leaf.get_head_name())
                self.to_matplotlib(leaf, evaluation)
        elif head_name == "System`RGBColor":
            rgbcolor = graphics_expr.leaves
            rgbcolor = [ c.to_python() for c in rgbcolor]
            print("rgbcolor=",rgbcolor)
            brush["color"] = rgbcolor
        elif head_name == "System`Line":
            self.matplotlib = self.add_line(graphics_expr, evaluation)
        elif head_name == "System`Text":
            self.matplotlib = self.add_text(graphics_expr, evaluation)
        elif head_name == "System`Rule":
            option_name, option_value = graphics_expr.leaves
            option_fn = self.option_name_to_fn.get(option_name.get_name(), None)
            if option_fn:
                option_fn(self, option_value, evaluation)
        elif head_name == "System`Rectangle":
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

            # add a rectangle
            rectangle = mpatches.Rectangle(xy, width=width, height=height)
            patches.append(rectangle)

            # FIXME: we probably need to reoganize this to arrange to do it once at the end
        elif head_name == "System`Circle":
            leaves = graphics_expr.get_leaves()
            if len(leaves) >1:
                r = float(leaves[1].to_python())
            else:
                r = 1.
            if len(leaves) >0:
                center = leaves[0].to_python()
            circle = mpatches.Circle(xy = center, radius = r, color=brush['color'],fill=False)
            patches.append(circle)
        elif head_name == "System`Disk":
            leaves = graphics_expr.get_leaves()
            if len(leaves) >1:
                r = float(leaves[1].to_python())
            else:
                r = 1.
            if len(leaves) >0:
                center = leaves[0].to_python()
            circle = mpatches.Circle(xy = center, radius = r, color=brush['color'], fill=True)
            patches.append(circle)

        elif head_name == "System`Polygon":
            points = graphics_expr.leaves[0].to_python()
            # Close file by adding a line from the last point to the first one
            points.append(points[0])
            matplotlib_polygon(points, evaluation)
        return

    def add_text(self, graphics_expr, evaluation):
        ax = evaluation.current_mpl_context["ax"]
        brush = evaluation.current_mpl_context["brush"]
        leaves = graphics_expr.get_leaves()
        text = leaves[0]
        if type(text) is String:
            text = text.get_string_value()
        else:
            text = text.format(evaluation, "TeXForm")
            text = "$" + text.boxes_to_text() + "$"

        print(text)
        if len(leaves)<2:
            x, y = (0,0)
        else:
            x, y = leaves[1].to_python()
        ax.text(x, y, text, color=brush["color"])
        

    def add_line(self, graphics_expr, evaluation):
        ax = evaluation.current_mpl_context["ax"]
        # Convert leaves to points...

        # Remove Expr[Line ... ]]
        points = graphics_expr.leaves[0].to_python()

        xdata = [p[0] for p in points]
        ydata = [p[1] for p in points]
        graphics_expr.line = lines.Line2D(xdata, ydata)
        ax.add_line(graphics_expr.line)

    def axes_aspect_ratio(self, aspect_ratio_value, evaluation):
        ax = evaluation.current_mpl_context["ax"]
        aspect_ratio = (
            Expression("N", aspect_ratio_value).evaluate(evaluation).to_python()
        )
        ax.set_box_aspect(aspect_ratio)

    def apply_boxes(self, expr, evaluation) -> Expression:
        "ToMatplotlib[expr_, PythonForm]"
        return self.apply(expr, evaluation)

    option_name_to_fn = {
        "System`AspectRatio": axes_aspect_ratio,
    }


def matplotlib_polygon(points, evaluation):
    ax = evaluation.current_mpl_context["ax"]
    xdata = [p[0] for p in points]
    ydata = [p[1] for p in points]
    ax.fill(xdata, ydata)


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
        fig = evaluation.current_mpl_context["fig"]
        ax  = evaluation.current_mpl_context["ax"]
        patches = evaluation.current_mpl_context["patches"]
        collection = PatchCollection(patches)
        ax.add_collection(collection)
        
        ticks_style = options.get('System`TicksStyle').to_python()
        axes_style = options.get('System`AxesStyle').to_python()
        print("axes_style=",axes_style, "  ticks=",ticks_style)
        # axes_style should overwrite what is defined in the argument. 
        #if not axes_style:
        #    ax.axis("off")
        fig.show()
        evaluation.current_mpl_context = None
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

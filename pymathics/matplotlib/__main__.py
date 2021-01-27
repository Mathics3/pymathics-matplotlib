# -*- coding: utf-8 -*-
import matplotlib.lines as lines
from mathics.builtin.base import Builtin, String
from mathics.core.expression import Expression
from mathics.core.rules import Rule
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.collections import PatchCollection


class WL2MLP:
    def __init__(self, expr, evaluation):
        fig, ax = plt.subplots()
        self.context = {"fig": fig,
                        "ax": ax,
                        "patches": [],
                        "options": "",
                        "brush": {
                            "color": "black",
                            "thickness": "auto",
                            "style": "-"
                        },
                        "style":{
                            "ticks_style": None,
                            "axes_style": None,
                            "axes": True
                        }
        }
        for e in expr.get_sequence():
            print("e=", e.get_head_name())
            self.to_matplotlib(e, evaluation)

    def _complete_render(self):
        "call me before show or export"
        patches = self.context["patches"]
        collection = PatchCollection(patches)
        ax = self.context["ax"]
        ax.add_collection(collection)
        self.context["patches"] = []
        # Apply the style options
        style = self.context["style"]
        for key in style:
            option_fn = self.option_name_to_fn.get(key, None)
            if option_fn:
                option_fn(self, style[key], evaluation)

    def show(self):
        self._complete_render()
        self.context["fig"].show()

    def export(self, filename, format=None):
        self._complete_render()
        if format:
            self.context["fig"].savefig(filename, format=format)
        else:
            self.context["fig"].savefig(filename)

    def to_matplotlib(self, graphics_expr: Expression, evaluation) -> None:
        """
        read and plot `graphics_expr` updating the state of `plt`.
        """
        ax = self.context["ax"]
        patches = self.context["patches"]
        brush = self.context["brush"]
        print("to_mpl",graphics_expr)
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
            self.context["style"][option_name] = option_value.to_python()
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
            self.add_circle(graphics_expr, False, evaluation)
        elif head_name == "System`Disk":
            self.add_circle(graphics_expr, True, evaluation)
        elif head_name == "System`Polygon":
            points = graphics_expr.leaves[0].to_python()
            # Close file by adding a line from the last point to the first one
            points.append(points[0])
            self.matplotlib_polygon(points, evaluation)
        return

    def add_circle(self, graphics_expr, fill, evaluation):
        brush = self.context["brush"]
        leaves = graphics_expr.get_leaves()
        if len(leaves) >1:
            r = float(leaves[1].to_python())
        else:
            r = 1.
        if len(leaves) >0:
            center = leaves[0].to_python()
        else:
            center=(0,0)
        circle = mpatches.Circle(xy = center, radius = r, color=brush['color'],fill=fill)
        self.context["patches"].append(circle)
        
    def add_text(self, graphics_expr, evaluation):
        ax = self.context["ax"]
        brush = self.context["brush"]
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
        ax = self.context["ax"]
        wllines = graphics_expr.leaves[0]
        if wllines.leaves[0].leaves[0].has_form('List', None):
            mpllines = wllines.to_python()
        else:
            mpllines = [wllines.to_python()]
        for points in mpllines:
            print("addline ge=",points)
            xdata = [p[0] for p in points]
            ydata = [p[1] for p in points]
            line = lines.Line2D(xdata, ydata, color=self.context["brush"]["color"])
            print("xdata=",xdata)
            print("ydata=",ydata)
            ax.add_line(line)

    def matplotlib_polygon(self, points, evaluation):
        ax = self.context["ax"]
        xdata = [p[0] for p in points]
        ydata = [p[1] for p in points]
        ax.fill(xdata, ydata)

    def axes_aspect_ratio(aspect_ratio_value, evaluation):
        ax = self.context["ax"]
        aspect_ratio = (
            Expression("N", aspect_ratio_value).evaluate(evaluation).to_python()
        )
        ax.set_box_aspect(aspect_ratio)

    def axes_show(value, evaluation):
        if not value:
            return
        value = value.to_python()
        ax = self.context["ax"]
        if type(axes) is bool:
            axes = (axes, axes)
        axes = tuple(axes)
        ax.xaxes.set_visible(axes[0])
        ax.xaxes.set_visible(axes[1])

    option_name_to_fn = {
        "System`AspectRatio": axes_aspect_ratio,
        "System`Axes": axes_show,
    }



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
        evaluation.current_wl2mpl = WL2MLP(expr, evaluation) 
        return result

    def apply_boxes(self, expr, evaluation) -> Expression:
        "ToMatplotlib[expr_, PythonForm]"
        return self.apply(expr, evaluation)


class MLPExportGraphics(Builtin):
    """
    <dl>
      <dt>'System`ConvertersDump`MLPExportGraphics'[$filename$, $graphics$]
      <dd>Export  $graphics$ to a file $filename$
      <dt>'System`ConvertersDump`MLPExportGraphics'[$filename$, $graphics$, $format$]
      <dd>Force to use $format$.
    </dl>
    """
    context = "System`ConvertersDump"
    messages = {
        "errexp": "`1` could not be saved in `2`",
    }
    
    def apply(self, filename, expr, format,  evaluation, options):
        "%(name)s[filename_String, expr_, format__String,  OptionsPattern[]]"
        wl2mpl = WL2MLP(expr, evaluation)
        context = wl2mpl.context
        try:
            wlmpl.export(filename.get_string_value())
        except:
            evaluation.message("System`ConvertersDump","error",expr, filename)
            raise

    
class MPLShow(Builtin):
    """
    <dl>
      <dt>'MPLot'[$expr$]
      <dd>Convert $expr$ in matplotlib.
    </dl>
    >> PyMathics`MPLShow[Line[{{0.25,0.5},{0.25,0.25},{0.5,0.25},{0.5,0.5}}]]
     :
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
        # Process the options
        wl2mpl = WL2MLP(expr, evaluation)
        context = wl2mpl.context
        context["style"]["ticks_style"] = options.get('System`TicksStyle').to_python()
        context["style"]["axes_style"] = options.get('System`AxesStyle').to_python()
        context["style"]["axes"] = options.get('System`Axes').to_python()
        wl2mpl.show()
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

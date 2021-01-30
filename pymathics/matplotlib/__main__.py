# -*- coding: utf-8 -*-
import matplotlib.lines as lines
from mathics.builtin.base import Builtin, String, BoxConstruct
from mathics.core.expression import Expression, Symbol, from_python
from mathics.core.rules import Rule
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.collections import PatchCollection
from mathics.builtin.colors import hsb_to_rgb
from mathics.builtin.graphics import _Color, GRAPHICS_OPTIONS



class MPLGraphicsBox(BoxConstruct):
    options = GRAPHICS_OPTIONS
    attributes = ("HoldAll", "ReadProtected")


    def apply_box(self, elems, evaluation, options):
        """System`MakeBoxes[System`Graphics[elems_, System`OptionsPattern[System`Graphics]],
        System`StandardForm|System`TraditionalForm|System`OutputForm]"""
        instance = MPLGraphicsBox(elems)
        instance.wl2mpl = _WL2MLP(elems, evaluation)
        return instance

    def boxes_to_text(self, leaves=None, **options):
        self.wl2mpl.show(options["evaluation"])
        return "--graphics-- text"

    def boxes_to_tex(self, leaves=None, **options):
        from io import StringIO
        out =  StringIO()
        self.wl2mpl.export(out, options["evaluation"],format="pgf") 
        return out.getvalue()

    def boxes_to_xml(self, leaves=None, **options):
        if not leaves:
            leaves = self._leaves
        return self.boxes_to_svg(options["evaluation"])

    def boxes_to_svg(self, evaluation):
        from io import StringIO
        out =  StringIO()
        self.wl2mpl.export(out, evaluation,format="svg") 
        return out.getvalue()


class _WL2MLP:
    def __init__(self, expr, evaluation, drawsymbols=True):
        fig, ax = plt.subplots()
        self.context = {"fig": fig,
                        "ax": ax,
                        "patches": [],
                        "options": {},
                        "brush": {
                            "color": "black",
                            "thickness": "auto",
                            "style": "-"
                        },
                        "style":{
                            "ticks_style": None,
                            "axes_style": None,
                            "axes": True,
                            "plotrange": None
                        }
        }
        options = self.context["options"]
        for opt in GRAPHICS_OPTIONS:
            options["System`"+opt] = None

        for e in expr.get_sequence():
            self.to_matplotlib(e, evaluation, drawsymbols=drawsymbols)


    def _complete_render(self, evaluation):
        "call me before show or export"
        patches = self.context["patches"]
        collection = PatchCollection(patches)
        ax = self.context["ax"]
        ax.add_collection(collection)
        self.context["patches"] = []
        # Apply the style options
        options = self.context["options"]
        for key in options:
            option_fn = self.option_name_to_fn.get(key, None)
            if option_fn:
                option_fn(self, options[key], evaluation)
        return


    def show(self, evaluation):
        self._complete_render(evaluation)
        #self.context["fig"].show()
        plt.show()

    def export(self, filename, evaluation, format=None):
        self._complete_render(evaluation)
        if format:
            res= self.context["fig"].savefig(fname=filename, format=format)
            print(res)
        else:
            self.context["fig"].savefig(filename)


    def to_matplotlib(self, graphics_expr: Expression, evaluation, drawsymbols=True) -> None:
        """
        read and plot `graphics_expr` updating the state of `plt`.
        """
        ax = self.context["ax"]
        patches = self.context["patches"]
        brush = self.context["brush"]
        if graphics_expr.is_symbol() or type(graphics_expr) is String:
            if drawsymbols:
                self.to_matplotlib(Expression("Text",
                                              graphics_expr),
                                   evaluation)
            return
        head_name = graphics_expr._head.get_name()
        # Iterables
        if head_name in ("System`Graphics",
                         "System`GraphicsBox",
                         "System`List"):
            for leaf in graphics_expr.get_leaves():
                self.to_matplotlib(leaf, evaluation)
        # Options
        elif head_name == "System`Rule":
            option_name, option_value = graphics_expr.leaves
            self.context["options"][option_name.get_name()] = option_value
        # Styles
        elif head_name in ("System`RGBColor", "System`Hue"):
            graphics_expr = _Color.create(graphics_expr)
            color = graphics_expr.to_rgba()
            brush["color"] = color
        # Shapes and lines
        elif head_name == "System`Line":
            self.matplotlib = self.add_line(graphics_expr, evaluation)
        elif head_name == "System`Text":
            self.matplotlib = self.add_text(graphics_expr, evaluation)
        elif head_name == "System`Rectangle":
            self.add_rectangle(graphics_expr, evaluation)
        elif head_name == "System`Circle":
            self.add_circle(graphics_expr, False, evaluation)
        elif head_name == "System`Disk":
            self.add_circle(graphics_expr, True, evaluation)
        elif head_name == "System`Polygon":
            points = graphics_expr.leaves[0].to_python()
            # Close file by adding a line from the last point to the first one
            points.append(points[0])
            self.matplotlib_polygon(points, evaluation)
        # Default
        else:
            if drawsymbols:
                self.to_matplotlib(Expression("Text",
                                              graphics_expr),
                                   evaluation)            
        return

## Draw shapes and lines

    def add_rectangle(self, graphics_expr, evaluation):
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
        self.context["ax"].add_artist(rectangle)

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
        self.context["ax"].add_artist(circle)
        #self.context["patches"].append(circle)
        
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
            xdata = [p[0] for p in points]
            ydata = [p[1] for p in points]
            line = lines.Line2D(xdata, ydata, color=self.context["brush"]["color"])
            ax.add_line(line)

    def matplotlib_polygon(self, points, evaluation):
        ax = self.context["ax"]
        xdata = [p[0] for p in points]
        ydata = [p[1] for p in points]
        ax.fill(xdata, ydata)

######  Option handling

    def axes_aspect_ratio(self, aspect_ratio_value, evaluation):
        if not aspect_ratio_value or \
           aspect_ratio_value == Symbol("System`Automatic"):
            return
        ax = self.context["ax"]
        aspect_ratio = (
            Expression("N", aspect_ratio_value).evaluate(evaluation).to_python()
        )
        ax.set_box_aspect(aspect_ratio)


    def axes_show(self, axes, evaluation):
        ax = self.context["ax"]
        if not axes:
            axes = False
        else:
            axes = axes.to_python()
            
        if type(axes) is bool:
            axes = (axes, axes)
        axes = tuple(axes)
        ax.xaxis.set_visible(axes[0])
        ax.yaxis.set_visible(axes[1])

    def set_image_size(self, value, evaluation):
        ax = self.context["ax"]
        if not value:
            return
        if value.has_form("List", 2):
            value = value.to_python()
            self.context["fig"].set_size_inches(*value)

    def set_plot_range(self, value, evaluation):
        ax = self.context["ax"]
        if not value or value in (Symbol("System`Automatic"),
                                  Symbol("System`All"),
                                  Symbol("System`Full")):
            return
        if not value.has_form("List", None):
            evaluation.message("", "Invalid plot range")
            return
        if len(value.leaves) == 1:
            value = value.to_python()
            value = [value, value]
        elif len(value.leaves) == 2:
            value = value.to_python()
        else:
            evaluation.message("", "Invalid plot range")
            return

        if type(value[0]) is list:
            ax.set_xlim(value[0][0],value[0][1])
        if type(value[1]) is list:
            ax.set_ylim(value[1][0],value[1][1])

        
    option_name_to_fn = {
        "System`AspectRatio": axes_aspect_ratio,
        "System`Axes": axes_show,
        "System`PlotRange": set_plot_range,
        "System`ImageSize": set_image_size,
    }





class MPLExportGraphics(Builtin):
    """
    <dl>
      <dt>'System`ConvertersDump`MPLExportGraphics'[$filename$, $graphics$]
      <dd>Export  $graphics$ to a file $filename$
      <dt>'System`ConvertersDump`MPLExportGraphics'[$filename$, $graphics$, $format$]
      <dd>Force to use $format$.
    </dl>
    """

    messages = {
        "errexp": "`1` could not be saved in `2`",
    }
    options = GRAPHICS_OPTIONS
    
    def apply(self, filename, expr, format,  evaluation, options):
        "MPLExportGraphics[filename_String, expr_, format___String,  OptionsPattern[MPLExportGraphics]]"
        wl2mpl = _WL2MLP(expr, evaluation, drawsymbols=True)
        context = wl2mpl.context
        try:
            if type(format) is String:
                format = format.get_string_value()
            elif len(format.leaves)>0:
                format=format.leaves[0].get_string_value()
            else:
                format = None
            
            if format:
                wl2mpl.export(filename.get_string_value(),
                              evaluation,
                              format=format)
            else:
                wl2mpl.export(filename.get_string_value(),
                              evaluation
                              )
        except:
            evaluation.message("System`ConvertersDump","error",expr, filename)
            raise
        return filename


class MPLExportGraphicsToString(Builtin):
    """
    <dl>
      <dt>'System`ConvertersDump`MPLExportGraphicsToString'[$graphics$]
      <dd>Export  $graphics$ to a file $filename$
      <dt>'System`ConvertersDump`MPLExportGraphics'[$filename$, $graphics$, $format$]
      <dd>Force to use $format$.
    </dl>
    """
    messages = {
        "errexp": "`1` could not be saved in `2`",
    }
    options = GRAPHICS_OPTIONS

    rules = {"System`GraphicsToSVG[expr_]"  : 'System`MPLExportGraphicsToString[expr, "svg"]',
             "System`GraphicsToTeX[expr_]"  : 'System`MPLExportGraphicsToString[expr, "pgf"]',
    }

    def apply(self, expr, format,  evaluation, options):
        "MPLExportGraphicsToString[expr_, format___String,  OptionsPattern[MPLExportGraphicsToString]]"
        from io import StringIO, BytesIO
        out =  BytesIO()
        wl2mpl = _WL2MLP(expr, evaluation, drawsymbols=True)
        context = wl2mpl.context
        try:
            if type(format) is String:
                format = format.get_string_value()
            elif len(format.leaves)>0:
                format=format.leaves[0].get_string_value()
            else:
                format = None
            if format:
                print("format=", format)
                wl2mpl.export(out,
                              evaluation,
                              format=format)
            else:
                print("should be svg")
                wl2mpl.export(out,
                              evaluation, format="SVG"
                              )
        except:
            evaluation.message("System`ConvertersDump","error",expr)
            raise
        return String(out.getvalue().decode('utf8'))


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
    options = GRAPHICS_OPTIONS

#    def apply_box(self, content, evaluation):
#        """System`MakeBoxes[System`content_System`Graphics, System`StandardForm]"""
##        """System`MakeBoxes[System`content_System`Graphics, System`StandardForm|System`TraditionalForm|System`OutputForm]"""
 #       self.apply(content, evaluation, [])
#        return String("--Graphics--")


    def apply(self, expr, evaluation, options):
        "%(name)s[expr_, OptionsPattern[%(name)s]]"
        # Process the options
        wl2mpl = _WL2MLP(expr, evaluation)
        context = wl2mpl.context
        for opt in options:
            context["options"][opt] = options[opt]

        wl2mpl.show(evaluation)
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

"""
Extract svg from the COLR tabel of the font. nanoemoju's colr_to_svg module is used for the conversion.

"""

# FIXME: check if black-renderer can be better than nanoemoji. While not
# directly related, if a support for variable font is required, we may use
# blackrender.

# black-renderer : https://github.com/BlackFoundryCom/black-renderer
# nanoemoji : https://github.com/googlefonts/nanoemoji


from fontTools.ttLib import TTFont

from nanoemoji.colr_to_svg import glyph_region
from nanoemoji.colr_to_svg import (_colr_v0_glyph_to_svg,
                                   _colr_v1_glyph_to_svg)
import nanoemoji.colr_to_svg

from lxml import etree
from copy import copy

import numpy as np

# svgPathPen in nanoemoji has a bug in qCurveTo when there is None at the end.
# We patch nanoemoji to use fontTools.pens.svgPathPen instead.

from fontTools.pens.transformPen import TransformPen
from fontTools.pens.svgPathPen import SVGPathPen

def _draw_svg_path(
    svg_path,
    glyph_set,
    glyph_name,
    font_to_vbox,
):
    # use glyph set to resolve references in composite glyphs
    svg_pen = SVGPathPen(glyph_set)
    # wrap svg pen with "filter" pen mapping coordinates from UPEM to SVG space
    transform_pen = TransformPen(svg_pen, font_to_vbox)

    glyph = glyph_set[glyph_name]
    glyph.draw(transform_pen)

    svg_path.attrib["d"] = svg_pen.getCommands()


def monkey_patch_nanoemoji():
    if nanoemoji.colr_to_svg._draw_svg_path is not _draw_svg_path:
        nanoemoji.colr_to_svg._draw_svg_path = _draw_svg_path

monkey_patch_nanoemoji()

class Ligatures:
    def __init__(self, gsub, cmap):
        # only select LookupType of 4, which are ligatures. FIXME Not sure if
        # updating the dictionary in sequence is a right approch.
        self._cmap = cmap
        self._ligatures = dict()
        for lookup in gsub.table.LookupList.Lookup:
            if lookup.LookupType == 4:
                for tbl in lookup.SubTable:
                    self._ligatures.update(tbl.ligatures)

    def get_gid(self, c):
        # check the ligature mapping to find a glyph id. Return None if not found.
        gidl = list(self._cmap[ord(c1)] for c1 in c)

        t = self._ligatures.get(gidl[0], None)
        if t is None:
            return None
        kk = dict([(tuple(t1.Component), t1) for t1 in t])
        lig = kk.get(tuple(gidl[1:]), None)
        if lig is None:
            return None

        return lig.LigGlyph


class Colr2SVG:
    """Extract SVG element of glyphs from the COLR table."""
    def __init__(self, ftname, view_box_callback=None):
        self._font = TTFont(ftname)

        assert "COLR" in self._font

        self._colr_version = self._font["COLR"].version

        self._cmap = self._font["cmap"].getBestCmap() # tables[4]
        self._glyph_set = self._font.getGlyphSet()
        self._view_box_callback = self._view_box if view_box_callback is None else view_box_callback
        if self._colr_version == 0:
            self._colr_glyph_to_svg = _colr_v0_glyph_to_svg
            self._glyph_map = dict((g, g) for g in self._font["COLR"].ColorLayers)

        elif self._colr_version == 1:
            self._colr_glyph_to_svg = _colr_v1_glyph_to_svg
            _glyph_list = self._font["COLR"].table.BaseGlyphList.BaseGlyphPaintRecord
            self._glyph_map = dict((g.BaseGlyph, _glyph_list[i] ) for i, g in
                                   enumerate(_glyph_list))

        gsub = self._font["GSUB"]
        self._ligatures = Ligatures(gsub, self._cmap)

    def get(self, c):
        if len(c) == 1:
            gid = self._cmap[ord(c)]
        else:
            gid = self._ligatures.get_gid(c)

        g = self._glyph_map[gid]

        svg_el = self._colr_glyph_to_svg(self._font, self._glyph_set,
                                         self._view_box_callback,
                                         g)

        return svg_el

    def _view_box(self, glyph_name: str):
        # we want a viewbox that results in no scaling when translating from font-space
        return glyph_region(self._font, glyph_name)

    # svg helper 
    @staticmethod
    def tostring(svg_el):
        return etree.tostring(svg_el)

    @staticmethod
    def get_scaled_svg(svg_el, size):
        svg_el = copy(svg_el)
        xywh = svg_el.attrib["viewBox"].split()
        x, y, w, h = map(float, xywh)
        scale = min(size / w, size / h)
        svg_el.attrib["viewBox"] = f"0 0 {w*scale} {h*scale}"

        paths = svg_el[1:]
        svg_el[1:] = [etree.Element("g")]
        svg_el[1][:] = paths

        # svg_el[1].attrib["transform"] = f"translate({x}, {y}) scale(0.5 0.5)"
        svg_el[1].attrib["transform"] = f"scale({scale} {scale}) translate({-x} {-y}) "

        return svg_el

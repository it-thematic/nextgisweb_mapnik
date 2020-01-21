# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
from collections import namedtuple

from lxml import etree
try:
    import mapnik
except ImportError:
    import mapnik2 as mapnik
from zope.interface import implementer

from nextgisweb import db
from nextgisweb.env import env
from nextgisweb.feature_layer import IFeatureLayer, on_data_change as on_data_change_feature_layer
from nextgisweb.models import declarative_base
from nextgisweb.render import (
    IExtentRenderRequest,
    ILegendableStyle,
    IRenderableStyle,
    ITileRenderRequest,
    on_data_change as on_data_change_renderable,
    on_style_change
)
from nextgisweb.resource import (
    DataScope,
    Resource,
    ResourceScope,
    Serializer,
    SerializedProperty
)
from nextgisweb.resource.exception import ValidationError

from .util import _, DEFAULT_STYLE_XML

Base = declarative_base()

VectorRenderOptions = namedtuple('VectorRenderOptions', ['style', 'render_size', 'extended', 'target_box'])
RasterRenderOptions = namedtuple('RasterRenderOptions', ['style', 'render_size', 'extended', 'target_box'])
LegendOptions = namedtuple('LegendOptions', ['style', ])


def _render_bounds(extent, size, padding):
    res_x = (extent[2] - extent[0]) / size[0]
    res_y = (extent[3] - extent[1]) / size[1]

    # Bounding box with padding
    extended = (
        extent[0] - res_x * padding,
        extent[1] - res_y * padding,
        extent[2] + res_x * padding,
        extent[3] + res_y * padding,
    )

    # Image dimensions
    render_size = (
        size[0] + 2 * padding,
        size[1] + 2 * padding
    )

    # Crop box
    target_box = (
        padding,
        padding,
        size[0] + padding,
        size[1] + padding
    )

    return extended, render_size, target_box


@implementer(IRenderableStyle, ILegendableStyle)
class MapnikVectorStyle(Base, Resource):
    identity = 'mapnik_vector_style'
    cls_display_name = _("Mapnik style")

    __scope__ = DataScope

    xml = db.Column(db.Unicode, default=DEFAULT_STYLE_XML, nullable=False)

    @classmethod
    def check_parent(cls, parent):
        return IFeatureLayer.providedBy(parent)

    @property
    def feature_layer(self):
        return self.parent

    @property
    def srs(self):
        return self.parent.srs

    def render_request(self, srs, cond=None):
        return RenderRequest(self, srs, cond)

    def _render_image(self, src, extent, size, cond, padding=0):
        extended, render_size, target_box = _render_bounds(extent, size, padding)
        options = VectorRenderOptions(self, render_size, extended, padding)

        return env.mapnik.renderer_job(options)


@on_data_change_feature_layer.connect
def on_data_change_feature_layer(resource, geom):
    for child in resource.children:
        if isinstance(child, MapnikVectorStyle):
            on_data_change_renderable.fire(child, geom)


@implementer(IExtentRenderRequest, ITileRenderRequest)
class RenderRequest(object):

    def __init__(self, style, srs, cond=None):
        """

        :param MapnikStyle style:
        :param SRS srs:
        :param dict cond:
        """
        self.style = style
        self.srs = srs
        self.cond = cond

    def render_extent(self, extent, size):
        return self.style._render_image(self.srs, extent, size, self.cond)

    def render_tile(self, tile, size):
        extent = self.srs.tile_extent(tile)
        return self.style._render_image(
            self.srs, extent, (size, size),
            self.cond,
            padding=size / 2
        )


DataScope.read.require(DataScope.read, attr='parent', cls=MapnikVectorStyle)


class _xml_attr(SerializedProperty):

    def setter(self, srlzr, value):
        try:
            etree.fromstring(value)
        except etree.XMLSyntaxError as e:
            raise ValidationError(e.message)

        except etree.DocumentInvalid as e:
            raise ValidationError(e.message)

        SerializedProperty.setter(self, srlzr, value)

        on_style_change.fire(srlzr.obj)


class StyleSerializer(Serializer):
    identity = MapnikVectorStyle.identity
    resclass = MapnikVectorStyle

    xml = _xml_attr(read=ResourceScope.read, write=ResourceScope.update)

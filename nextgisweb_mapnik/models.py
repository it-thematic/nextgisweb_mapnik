# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import sqlalchemy as sa
from PIL import Image
from lxml import etree

try:
    from StringIO import StringIO as StringIO
except ImportError:
    from io import StringIO as StringIO

try:
    import mapnik
except ImportError:
    import mapnik2 as mapnik

from zope.interface import implements

from nextgisweb.geometry import box
from nextgisweb.feature_layer import IFeatureLayer, on_data_change as on_data_change_feature_layer
from nextgisweb.models import declarative_base
from nextgisweb.render import (IRenderableStyle, IExtentRenderRequest, ITileRenderRequest, ILegendableStyle,
                               on_style_change,
                               on_data_change as on_data_change_renderable)
from nextgisweb.resource import Resource, ResourceScope, DataScope, Serializer, SerializedProperty
from nextgisweb.resource.exception import ValidationError

from .util import _, DEFAULT_IMAGE_FORMAT, DEFAULT_STYLE_XML

Base = declarative_base()


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


class MapnikStyle(Base, Resource):
    identity = 'mapnik_style'
    cls_display_name = _("Mapnik style")

    __scope__ = DataScope

    implements(IRenderableStyle, ILegendableStyle)

    xml = sa.Column(sa.Unicode, nullable=False)

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

    @classmethod
    def default_style_xml(cls, layer):
        return DEFAULT_STYLE_XML

    @classmethod
    def is_layer_supported(cls, layer):
        return IFeatureLayer.providedBy(layer)

    def render_image(self, srs, extent, size, cond, padding=0):
        extended, render_size, target_box = _render_bounds(extent, size, padding)

        feature_query = self.parent.feature_query()

        if cond:
            feature_query.filter(**cond)

        if hasattr(feature_query, 'src'):
            feature_query.srs(srs)
        feature_query.intersects(box(*extended, srid=srs.id))
        feature_query.geom()
        features = feature_query()

        if features.total_count < 1:
            return Image.new('RGBA', (size[0], size[1]), (255, 255, 255, 0))

        ds = mapnik.MemoryDatasource()
        for (id, f) in enumerate(features):
            if mapnik.mapnik_version() < 200100:
                feature = mapnik.Feature(id)
            else:
                feature = mapnik.Feature(mapnik.Context(), id)
            feature.add_geometries_from_wkb(f.geom.wkb)
            ds.add_feature(feature)

        style_content = str(self.xml)

        m = mapnik.Map(render_size[0], render_size[1])
        mapnik.load_map_from_string(m, style_content)
        m.zoom_to_box(mapnik.Box2d(*extended))

        layer = mapnik.Layer('main')
        layer.datasource = ds

        root = etree.fromstring(style_content)
        styles = [s.attrib.get('name') for s in root.iter('Style')]
        for s in styles:
            layer.styles.append(s)
        m.layers.append(layer)

        img = mapnik.Image(render_size[0], render_size[1])
        mapnik.render(m, img)
        data = img.tostring(DEFAULT_IMAGE_FORMAT)

        # Преобразуем изображение из PNG в объект PIL
        buf = StringIO()
        buf.write(data)
        buf.seek(0)

        img = Image.open(buf)
        return img


@on_data_change_feature_layer.connect
def on_data_change_feature_layer(resource, geom):
    for child in resource.children:
        if isinstance(child, MapnikStyle):
            on_data_change_renderable.fire(child, geom)


class RenderRequest(object):
    implements(IExtentRenderRequest, ITileRenderRequest)

    def __init__(self, style, srs, cond=None):
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


DataScope.read.require(
    DataScope.read,
    attr='parent', cls=MapnikStyle)


class _xml_attr(SerializedProperty):

    def setter(self, srlzr, value):
        try:
            layer = etree.fromstring(value)
        except etree.XMLSyntaxError as e:
            raise ValidationError(e.message)

        except etree.DocumentInvalid as e:
            raise ValidationError(e.message)

        SerializedProperty.setter(self, srlzr, value)

        on_style_change.fire(srlzr.obj)


PR_READ = ResourceScope.read
PR_UPDATE = ResourceScope.update


class MapnikStyleSerializer(Serializer):
    identity = MapnikStyle.identity
    resclass = MapnikStyle

    xml = _xml_attr(read=PR_READ, write=PR_UPDATE)

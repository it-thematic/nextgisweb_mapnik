# -*- coding: utf-8 -*-
import sqlalchemy as sa
from StringIO import StringIO
from PIL import Image
import xml.etree.ElementTree as ET

try:
    import mapnik
except ImportError:
    import mapnik2 as mapnik

from nextgisweb.geometry import box
from nextgisweb.feature_layer import IFeatureLayer


def include(comp):

    Style = comp.env.style.Style

    @Style.registry.register
    class MapnikStyle(Style):
        __tablename__ = 'mapnik_style'

        identity = __tablename__
        cls_display_name = u"Стиль Mapnik"

        style_id = sa.Column(sa.Integer, sa.ForeignKey('style.id'), primary_key=True)
        style_content = sa.Column(sa.Unicode, nullable=False)

        __mapper_args__ = dict(
            polymorphic_identity=identity,
        )

        @classmethod
        def is_layer_supported(cls, layer):
            return IFeatureLayer.providedBy(layer)

        def render_image(self, extent, img_size, settings):
            # Выбираем объекты по экстенту
            feature_query = self.layer.feature_query()
            feature_query.intersects(box(*extent, srid=self.layer.srs_id))
            feature_query.geom()
            features = feature_query()

            ds = mapnik.MemoryDatasource()
            for (id, f) in enumerate(features):
                if mapnik.mapnik_version() < 200100:
                    feature = mapnik.Feature(id)
                else:
                    feature = mapnik.Feature(mapnik.Context(), id)
                feature.add_geometries_from_wkb(f.geom.wkb)
                ds.add_feature(feature)

            style_content = str(self.style_content)

            m = mapnik.Map(img_size[0], img_size[1])
            mapnik.load_map_from_string(m, style_content)
            m.zoom_to_box(mapnik.Box2d(*extent))

            layer = mapnik.Layer('main')
            layer.datasource = ds

            root = ET.fromstring(style_content)
            styles = [s.attrib.get('name') for s in root.iter('Style')]
            for s in styles:
                layer.styles.append(s)
            m.layers.append(layer)

            img = mapnik.Image(img_size[0], img_size[1])
            mapnik.render(m, img)
            data = img.tostring('png')

            # Преобразуем изображение из PNG в объект PIL
            buf = StringIO()
            buf.write(data)
            buf.seek(0)

            img = Image.open(buf)
            return img

    comp.MapnikStyle = MapnikStyle

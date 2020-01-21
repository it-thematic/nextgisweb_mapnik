# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

try:
    import mapnik
except ImportError:
    import mapnik2 as mapnik
import six

from threading import Thread

from lxml import etree
from nextgisweb.component import Component
from nextgisweb.geometry import box
from PIL import Image
from six.moves.queue import Queue

from .models import Base, VectorRenderOptions, RasterRenderOptions, LegendOptions, MapnikVectorStyle
from .util import _


class MapnikStyleComponent(Component):
    identity = 'mapnik_style'
    metadata = Base.metadata

    default_max_zoom = 19
    default_render_timeout = 30.0

    def initialize(self):
        super(MapnikStyleComponent, self).initialize()

        try:
            self._render_timeout = float(self.settings.get('render_timeout', self.__class__.default_render_timeout))
        except ValueError:
            self.logger.error(_('Invalid value of "%s". The default value is %s.') % (
                self.__class__.default_render_timeout.__class__.__name__, self.__class__.default_render_timeout))
            self._render_timeout = self.__class__.default_render_timeout

        mapnik.register_fonts(self.options['fontpath'].encode('utf-8') if 'fontpath' in self.options else None)

        self.queue = Queue()
        self.worker = Thread(target=self.renderer)
        self.worker.daemon = True
        self.worker.start()

    def configure(self):
        super(MapnikStyleComponent, self).configure()

    def setup_pyramid(self, config):
        from . import views
        views.setup_pyramid(self, config)

    @staticmethod
    def _create_empty_image():
        return Image.new('RGBA', (256, 256), (0, 0, 0, 0))

    def renderer_job(self, options):
        result_queue = Queue()
        self.queue.put((options, result_queue))

        result = result_queue.get(block=True, timeout=self._render_timeout)

        if isinstance(result, Exception):
            raise result
        return result

    def renderer(self):
        while True:
            options, result = self.queue.get()
            try:
                if isinstance(options, LegendOptions):
                    self.logger.error(_('Not supported yet'))
                elif isinstance(options, VectorRenderOptions):  # type: VectorRenderOptions
                    style, render_size, extended, target_box = options

                    feature_query = style.parent.feature_query()
                    feature_query.intersects(box(*extended, srid=style.parent.srs_id))
                    feature_query.geom()
                    features = feature_query()
                    # make datasource
                    ds = mapnik.MemoryDatasource()
                    for (id, f) in enumerate(features):
                        if mapnik.mapnik_version() < 200100:
                            feature = mapnik.Feature(id)
                        else:
                            feature = mapnik.Feature(mapnik.Context(), id)
                        feature.add_geometries_from_wkb(f.geom.wkb)
                        ds.add_feature(feature)

                    # make style
                    style_content = six.text_type(style.xml)

                    # make map
                    m = mapnik.Map(render_size[0], render_size[1])
                    mapnik.load_map_from_string(m, style_content)
                    m.zoom_to_box(mapnik.Box2d(*extended))

                    # build
                    layer = mapnik.Layer('main')
                    layer.datasource = ds
                    root = etree.fromstring(style_content)
                    styles = [s.attrib.get('name') for s in root.iter('Style')]
                    for s in styles:
                        layer.styles.append(s)
                    m.layers.append(layer)

                    img = mapnik.Image(render_size[0], render_size[1])
                    mapnik.render(m, img)
                    data = img.tostring('png')

                    # Преобразуем изображение из PNG в объект PIL
                    buf = six.StringIO()
                    buf.write(data)
                    buf.seek(0)

                    img = Image.open(buf)
                    result.put(img)
                else:
                    self.logger.error(_('Invalid options type: %s' % type(options)))
            except Exception as e:
                self.logger.error(e.message)
                result.put(e)

    settings_info = (
        dict(key='render_timeout', desc='Mapnik rendering timeout for one request.'),
        dict(key='fontpath', desc='Font search folder')
    )


def pkginfo():
    return dict(components=dict(mapnik="nextgisweb_mapnik"))


def amd_packages():
    return (
        ('mapnik_style', 'nextgisweb_mapnik:amd_packages/ngw-mapnik'),
    )

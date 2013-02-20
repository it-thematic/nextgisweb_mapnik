# -*- coding: utf-8 -*-
from nextgisweb.component import Component, require


@Component.registry.register
class MapnikStyleComponent(Component):
    identity = 'mapnik_style'

    @require('style')
    def initialize(self):
        Component.initialize(self)

        from . import models
        models.include(self)

    def setup_pyramid(self, config):
        from . import views
        views.setup_pyramid(self, config)


def amd_packages():
    return (
        ('mapnik_style', 'nextgisweb_mapnik:amd_packages/mapnik_style'),
    )

# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from nextgisweb.i18n import trstring_factory

COMP_ID = 'mapnik'
_ = trstring_factory(COMP_ID)

DEFAULT_IMAGE_FORMAT = b'png'

DEFAULT_STYLE_XML = """
<Map srs="+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs">
    <Style name="defautl" filter-mode="first" >
        <Rule>
            <LineSymbolizer stroke-width="5" stroke="#777777" />
        </Rule>
        <Rule>
            <PolygonSymbolizer fill="rgb(206,154,156)"/>
            <LineSymbolizer stroke="rgb(106,106,106)"/>
        </Rule>
        <Rule>
            <MarkersSymbolizer width="6" fill="#ff4455" stroke="#881133" allow-overlap="true" />
        </Rule>  
    </Style>
</Map>
"""
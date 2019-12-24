# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
from json import dumps
from lxml import etree
from pyramid.response import Response

from nextgisweb.env import env
from nextgisweb.object_widget import ObjectWidget
from nextgisweb.resource import Widget

from .models import MapnikStyle
from .util import _


class MapnikStyleWidget(Widget):
    resource = MapnikStyle
    operation = ('create', 'update')
    amdmod = 'ngw-mapnik/Widget'

    def config(self):
        res = super(MapnikStyleWidget, self).config()

        # TODO: Security
        if self.operation == 'create':
            res['defaultValue'] = MapnikStyle.default_style_xml(self.obj.parent)
        return res


def setup_pyramid(comp, config):

    class MapnikStyleObjectWidget(ObjectWidget):
        def is_applicable(self):
            return self.operation in ('create', 'edit')

        def validate(self):
            result = super(MapnikStyleObjectWidget, self).validate()

            self.error = []

            def err(msg):
                self.error.append(dict(message=msg))
                return False

            try:
                layer = etree.fromstring(self.data['xml'])
            except etree.XMLSyntaxError as e:
                result = err(_("XML syntax error: %(message)s") % dict(message=e.message))
            except etree.DocumentInvalid as e:
                result = err(_("XML schema error: %(message)s") % dict(message=e.message))
            return result

        def populate_obj(self):
            super(MapnikStyleObjectWidget, self).populate_obj()
            self.obj.xml = self.data['xml']

        def widget_module(self):
            return 'mapnik_style/Widget'

        def widget_params(self):
            result = super(MapnikStyleObjectWidget, self).widget_params()

            if self.obj:
                result['value'] = dict(xml=self.obj.xml)
            else:
                result['value'] = dict(xml=MapnikStyle.default_style_xml(self.options['parent']))
            return result

    MapnikStyle.object_widget = MapnikStyleObjectWidget

    def mapnik_import(request):
        fileid = request.json_body['file']['upload_meta'][0]['id']
        filename, metadata = env.file_upload.get_filename(fileid)

        elem = etree.parse(filename).getroot()

        def warn(src, dst, msg):
            dst.append(etree.Comment(' ' + msg + ' '))
        dst = elem

        body = etree.tostring(dst, pretty_print=True, encoding='utf-8')

        _xml, _json = 'text/xml', 'application/json'

        if request.accept.best_match([_xml, _json]) == _xml:
            return Response(body, content_type=_xml)
        else:
            return Response(dumps(body), content_type=_json)

    config.add_route('mapnik.import', '/mapnik/import', client=()).add_view(mapnik_import, request_method='POST')

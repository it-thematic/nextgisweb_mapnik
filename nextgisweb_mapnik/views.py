# -*- coding: utf-8 -*-
from nextgisweb.object_widget import ObjectWidget


def setup_pyramid(comp, config):

    class MapnikStyleObjectWidget(ObjectWidget):
        def is_applicable(self):
            return self.operation in ('create', 'edit')

        def populate_obj(self):
            ObjectWidget.populate_obj(self)
            self.obj.style_content = self.data['content']

        def widget_module(self):
            return 'mapnik_style/Widget'

        def widget_params(self):
            result = ObjectWidget.widget_params(self)

            if self.obj:
                result['value'] = dict(
                    content=self.obj.style_content
                )

            return result

    comp.MapnikStyle.object_widget = MapnikStyleObjectWidget

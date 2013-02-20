define([
    "dojo/_base/declare",
    "ngw/modelWidget/Widget",
    "ngw/modelWidget/ErrorDisplayMixin",
    "dijit/_TemplatedMixin",
    "dijit/_WidgetsInTemplateMixin",
    "dojo/text!./templates/Widget.html",
    "dojox/layout/TableContainer",
    "dijit/layout/TabContainer",
    "dijit/form/TextBox",
    "dijit/form/Textarea",
    "dijit/ColorPalette",
    "dijit/form/NumberSpinner"
], function (
    declare,
    Widget,
    ErrorDisplayMixin,
    _TemplatedMixin,
    _WidgetsInTemplateMixin,
    template
) {
    return declare([Widget, ErrorDisplayMixin, _TemplatedMixin, _WidgetsInTemplateMixin], {
        templateString: template,
        identity: "mapnik_style",
        title: "Стиль Mapnik",

        _getValueAttr: function () {
            return {
                style_content: this.wStyleContent.get("value"),
            };
        },

        _setValueAttr: function (value) {
            this.inherited(arguments);
            this.wStyleContent.set("value", value.style_content);
        }
    });
})

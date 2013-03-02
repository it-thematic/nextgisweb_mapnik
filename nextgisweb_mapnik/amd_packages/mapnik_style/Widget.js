/*global define*/
define([
    "dojo/_base/declare",
    "ngw/modelWidget/Widget",
    "ngw/modelWidget/ErrorDisplayMixin",
    "dijit/_TemplatedMixin",
    "dijit/_WidgetsInTemplateMixin",
    "dojo/text!./templates/Widget.html",
    // template
    "ngw/form/CodeMirror"
], function (
    declare,
    Widget,
    ErrorDisplayMixin,
    _TemplatedMixin,
    _WidgetsInTemplateMixin,
    template
) {
    return declare([Widget, ErrorDisplayMixin, _TemplatedMixin, _WidgetsInTemplateMixin], {
        identity: "mapnik_style",
        title: "Стиль Mapnik",

        templateString: template,

        _getValueAttr: function () {
            return {
                content: this.content.get("value")
            };
        },

        _setValueAttr: function (value) {
            this.content.set("value", value.content);
        }
    });
});
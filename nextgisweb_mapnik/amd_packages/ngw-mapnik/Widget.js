/*global define*/
define([
    "dojo/_base/declare",
    "dojo/aspect",
    "dojo/json",
    "dojo/request/xhr",
    "dijit/layout/ContentPane",
    "dijit/_TemplatedMixin",
    "dijit/_WidgetsInTemplateMixin",
    "ngw/route",
    "ngw-pyramid/i18n!mapnik",
    "ngw-pyramid/hbs-i18n",
    "ngw-resource/serialize",
    "dojo/text!./templates/Widget.hbs",
    // template

    "ngw-pyramid/form/CodeMirror",
    "ngw-file-upload/Uploader",
    "dijit/form/NumberSpinner"
], function (
    declare,
    aspect,
    json,
    xhr,
    ContentPane,
    _TemplatedMixin,
    _WidgetsInTemplateMixin,
    route,
    i18n,
    hbsI18n,
    serialize,
    template
) {
    return declare([ContentPane, serialize.Mixin, _TemplatedMixin, _WidgetsInTemplateMixin], {
        templateString: hbsI18n(template, i18n),
        title: i18n("Manik style"),
        prefix: "manik_style",

        postCreate: function() {
            this.inherited(arguments);

            var widget = this;
            aspect.after(this.mapnikUploader, "uploadComplete", function (file) {
                widget.mapnikUploadComplete(file);
            }, true);
            aspect.after(this.mapnikUploader, "uploadBegin", function () {
                widget.mapnikUploadBegin();
            }, true);

            if (this.composite.operation === "create" && this.composite.config["ngw-mapnik/Widget"].defaultValue) {
                this.xml.set("value", this.composite.config["ngw-mapnik/Widget"].defaultValue);
            }
        },

        mapnikShowDialog: function () {
            this.mapnikDialog.show();
        },

        mapnikUploadBegin: function () {
            this.mapnikPreview.set("value", "");
        },

        mapnikUploadComplete: function (file) {
            var widget = this;
            xhr.post(route.mapnik.import(), {
                data: json.stringify({file: file})
            }).then(
                function (data) { widget.mapnikPreview.set("value", data); },
                function () { widget.mapnikPreview.set("value", i18n.gettext("<!-- An unknown error occurred during the file conversion -->")); }
            ).then(undefined, function (err) { console.error(err); });
        },

        mapnikAccept: function () {
            this.xml.set("value", this.mapnikPreview.get("value"));
            this.mapnikDialog.hide();
        },

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
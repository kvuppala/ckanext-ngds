/* Copyright (c) 2014, Siemens Corporate Technology and Arizona Geological Survey */
/* Copyright (c) 2014, Siemens Corporate Technology and Arizona Geological Survey */
/* Copyright (c) 2014, Siemens Corporate Technology and Arizona Geological Survey */
$(document).ready(function () {
    $("button[data-ogc-publish]").click(function (ev) {
        var resource_id = $(this).attr("data-ogc-resource"),
            collection_id = $(this).attr("data-ogc-collection"),
            content_model_layer = $(this).attr("data-ogc-layer");
            if (content_model_layer) {
                ngds.publisher.publish_usgin(resource_id, collection_id, content_model_layer);
            } else {
                ngds.publisher.publish_other(resource_id, collection_id);
            }
    });

    $("button[data-ogc-unpublish]").click(function (ev) {
        var resource_id = $(this).attr("data-ogc-resource");
        var layer_name = $(this).attr("data-ogc-layer");
        ngds.publisher.unpublish(resource_id, layer_name);
    });

    ngds.publisher = {
        'publish_other': function (resource_id, collection_id) {
            var template = [
                '<div class="modal">',
                '<div class="modal-header">',
                '<button type="button" class="close" data-dismiss="modal">×</button>',
                '<h3>Publish resource to OGC</h3>',
                '</div>',
                '<div class="modal-body">',
                '<div class="geoserver-layer-modal">',
                '<label>Geoserver Layer Name</label><input type="text" name="geoserver_layer_name" />',
                '</div>',
                '<div id="processing">Please wait while we try to fetch field names in this resource ...</div>',
                '</div>',
                '<div class="modal-footer">',
                '<button class="btn btn-cancel">Cancel</button>',
                '<button class="btn btn-primary">Confirm</button>',
                '</div>',
                '</div>'
            ].join('\n');

            var element = $(template);
            var modal = element.modal({'show': true});

            ngds.ckanlib.datastore_search(resource_id, function (response) {
                var lat_select = $("<select/>", {'class': 'geoserver-lat-selector', "name": "lat"});
                var lng_select = $("<select/>", {'class': 'geoserver-lng-selector', "name": "lng"});

                var optionify = function (fields) {
                    return fields.map(function (field) {
                        return $('<option/>', {'text': field['id'], 'value': field['id'] });
                    });
                };

                var lat_fields = optionify(response.result.fields);
                var lng_fields = optionify(response.result.fields);

                lat_fields.map(function (field) {
                    lat_select.append(field);
                });

                lng_fields.map(function (field) {
                    lng_select.append(field);
                });

                var lat_select_div = $("<div/>", {});
                var lng_select_div = $("<div/>", {});
                var container = $("<div/>", {});


                var lat_label = $("<label/>", {'text': 'Latitude Field'});
                var lng_label = $("<label/>", {'text': 'Longitude Field'});

                lat_select_div.append(lat_label);
                lat_select_div.append(lat_select);
                lng_select_div.append(lng_label);
                lng_select_div.append(lng_select);
                container.append(lat_select_div);
                container.append(lng_select_div);

                $(".modal #processing").replaceWith(container);
            });

            element.on('click', '.btn-primary', function (ev) {
                    ev.preventDefault();
                    modal.modal('hide');
                    ckan.notify("Please wait while this resource is published ...... ", "", "info");
                    ngds.ckanlib.publish_to_geoserver({
                        'action': '/api/action/geoserver_publish_layer',
                        'layer_name': $("[name=geoserver_layer_name]").val(),
                        'resource_id': resource_id,
                        'package_id': collection_id,
                        'col_geo': "geometry",
                        'col_lat': $("[name=lat]").val(),
                        'col_lng': $("[name=lng]").val(),
                        'callback': function (resp_obj) {
                            if (resp_obj['status'] === 'failure') {
                                ckan.notify("Sorry. The action requested could not be successfully completed.", "", "error")
                            }
                            else {
                                ckan.notify("This resource has now been published as an OGC service.", "", "success");
                                window.location.reload();
                            }
                        }
                    });
                }
            );
            element.on('click', '.btn-cancel', function (ev) {
                ev.preventDefault();
                modal.modal('hide');
            });
        },
        'publish_usgin': function (resource_id, collection_id, content_model_layer) {
            ckan.notify("Publishing tier 3 structured OGC services...", "", "info");
            ngds.ckanlib.datastore_search(resource_id, function (response) {
                var fields = response.result.fields,
                    field_ids = (function() {
                        var these_ids = [];
                        for (var i=0; i<fields.length; i++) {
                            these_ids.push(fields[i].id);
                        }
                        return these_ids;
                    })(),
                    geo_fields = (function() {
                        if (field_ids.indexOf('LatDegree') !== -1 && field_ids.indexOf('LongDegree') !== -1) {
                            return geo_fields = {'lat': 'LatDegree', 'lng': 'LongDegree'}
                        } else {
                            return geo_fields = {'lat': 'LatDegreeWGS84', 'lng': 'LongDegreeWGS84'}
                        }
                    })();

                ngds.ckanlib.publish_to_geoserver({
                    'action': '/api/action/geoserver_publish_usgin_layer',
                    'layer_name': content_model_layer,
                    'resource_id': resource_id,
                    'package_id': collection_id,
                    'content_model_layer': content_model_layer,
                    'col_geo': "geometry",
                    'col_lat': geo_fields.lat,
                    'col_lng': geo_fields.lng,
                    'callback': function (resp_obj) {
                        if (resp_obj['status'] === 'failure') {
                            ckan.notify("Failed to publish OGC services", "", "error")
                        } else {
                            window.location.reload();
                        }
                    }
                });
            });
        },
        'unpublish': function (resource_id, layer_name) {
            console.log("Unpublishing " + resource_id + " " + layer_name);
            ckan.notify("Removing OGC services for this dataset", "", "info");
            ngds.ckanlib.unpublish_layer({
                'layer_name': layer_name,
                'resource_id': resource_id,
                'callback': function (resp_obj) {
                    if (resp_obj['status'] === "failure") {
                        ckan.notify("Sorry. The action requested could not be successfully completed.", "", "error");
                    }
                    else {
                        window.location.reload();
                    }
                }
            });
        }
    };
});
(function () {
    var url = $("#prospector-btn").attr("res_url"),
        layer = $("#prospector-btn").attr("res_layer"),
        data = JSON.stringify({'url': url, 'layer': layer});

    $("#prospector-btn").attr("data-toggle", "tooltip");
    $("#prospector-btn").attr("title", "Loading data...");

    $.ajax({
        url: '/api/action/geothermal_prospector',
        type: 'POST',
        data: data,
        success: function (response) {
            var wms_url = response.result.wms;
            $("#prospector-btn").attr("href", wms_url);
            $("#prospector-btn").attr("target", "_blank");
            $("#prospector-btn").removeClass("disabled");
            $("#prospector-btn").removeAttr("data-toggle");
            $("#prospector-btn").removeAttr("title");
        },
        error: function () {
            $("#prospector-btn").removeAttr("title");
            $("#prospector-btn").attr("title", "Error loading service");
        }
    })
}).call(this);
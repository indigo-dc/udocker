/*
 * Copyright (C) 2012-2015 Bitergia
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
 *
 * This file is a part of the VizGrimoireJS-lib package
 *
 * Authors:
 *   Alvaro del Castillo San Felix <acs@bitergia.com>
 *   Luis Cañas-Díaz <lcanas@bitergia.com>
 *
 */

var Timezones = {};

(function() {

    var data_tz = false;

    Timezones.widget = function(){
        var divs = $(".TimezonesBlock");
        if (divs.length > 0){
            $.each(divs, function(id, div) {
                ds_name = $(this).data('data-source');
                metric_name = $(this).data('metric');
                /* this is a typical check, should be moved to a generic funct*/
                DS = Report.getDataSourceByName(ds_name);
                if (DS === null) return;
                if (DS.getData().length === 0) return; /* no data for data source*/

                loadTimeZonesData(ds_name,
                    function(){
                        displayTimeZones(div, ds_name, metric_name);
                        });
            });
        }
    };

    function loadTimeZonesData (ds_name, cb) {
        suffix = ds_name.toLowerCase();
        var json_file = "data/json/" + suffix + "-timezone.json";
        $.when($.getJSON(json_file)
                ).done(function(json_data) {
                data_tz = json_data;
                cb();
        }).fail(function() {
            console.log("Time zone widget disabled. Missing " + json_file);
        });
    }

    function displayTimeZones (div, ds_name, metric_name) {
        var data;
        // we get the HTML with bootstrap
        var html = HTMLTimezones(ds_name, metric_name);
        if (!div.id) div.id = "Parsed" + getRandomId();
        $("#"+div.id).append(html);
        //we call the Viz method to plot the chart
        var mark = "TimeZones";
        var divs = $("."+mark);
        if (divs.length > 0) {
            var unique = 0;
            $.each(divs, function(id, div) {
                div.id = mark + (unique++);
                var ds = $(this).data('data-source');
                if (ds === undefined) return;
                var metric = $(this).data('metric');
                labels = data_tz.tz;
                data = data_tz[metric];
                Viz.displayTimeZone(div.id, labels, data, metric);
            });
        }
    }

    function HTMLTimezones (ds_name, metric_name){
        var html = '<div class="row">';
        html += '<div class="col-md-12"><div class="well">';
        html +='<div class="TimeZones" style="height: 150px"';
        html += 'data-metric="'+metric_name+'" data-data-source="'+ds_name+'"></div>';
        html += '</div></div></div>';
        return html;
    }

    function getRandomId() {
        return Math.floor(Math.random()*1000+1);
    }

})();

Loader.data_ready(function() {
    Timezones.widget();
});

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
 *   Luis Cañas-Díaz <lcanas@bitergia.com>
 *
 */

var Resolved = {};

(function() {

    var data_tz = false;

    Resolved.chart_widget = function(){    // General config for metrics viz
        var config_metric = {};

        config_metric.show_desc = false;
        config_metric.show_title = true;
        config_metric.show_labels = true;

        var config = Report.getVizConfig();
        if (config) {
            $.each(config, function(key, value) {
                config_metric[key] = value;
            });
        }
        var div_param = "MetricsEvolResolved";
        var divs = $("." + div_param);
        if (divs.length > 0) {
            $.each(divs, function(id, div) {
                var config_viz = {};
                $.each(config_metric, function(key, value) {
                    config_viz[key] = value;
                });
                $(this).empty();
                var metrics = $(this).data('metrics');
                var ds = $(this).data('data-source');
                //FIXME title is duplicated with custom-title
                config_viz.title = $(this).data('title');
                var DS = Report.getDataSourceByName(ds);
                if (DS === null) return;

                config_viz = loadHTMLEvolParameters(div, config_viz);

                div.id = metrics.replace(/,/g,"-")+"-"+ds+"-metrics-evol-"+this.id;
                div.id = div.id.replace(/\n|\s/g, "");
                loadResolvedData(
                    function(){
                        DS.displayMetricsEvol(metrics.split(","),div.id,
                        config_viz, $(this).data('convert'));
                    });
            });
        }
    };

    Resolved.top_widget = function(){
        var div_id_top = "TopResolved";
        var divs = $("." + div_id_top);
        var DS, ds;
        if (divs.length > 0) {
            var unique = 0;
            $.each(divs, function(id, div) {
                $(this).empty();
                ds = $(this).data('data-source');
                DS = Report.getDataSourceByName(ds);
                if (DS === null) return;
                if (DS.getData().length === 0) return;
                div.id = div_id_top + (unique++);
                loadResolversData(function(){
                    DS.displayTop(div, false, "resolvers", "all", true,
                                  "", 10, true, false, undefined);
                });
            });
        }
    };

    function loadResolvedData (cb) {
        var json_file = "data/json/" + "its-changes.json",
            a,
            b;
        DS = Report.getDataSourceByName('its');
        $.when($.getJSON(json_file)
                ).done(function(json_data) {
                DS.data.its_resolved = json_data.Resolved;
                DS.data.its_resolvers = json_data.resolvers;
                a = json_data.Resolved;
                b = DS.getData()['its_closed'];
                DS.data.its_closed_plus_resolved = a.SumArray(b);
                DS.basic_metrics.its_closed_plus_resolved = {
                    "name" : "Resolved & Closed tickets"
                };
                cb();
        }).fail(function() {
            console.log("**** widget disabled. Missing " + json_file);
        });
    }

    function loadResolversData (cb) {
        var json_file = "data/json/" + "its-changers.json",
            all = {},
            month = {},
            year = {};
        DS = Report.getDataSourceByName('its');
        $.when($.getJSON(json_file)
                ).done(function(json_data) {

                all.resolved = json_data['resolvers.'].changes;
                all.resolvers = json_data['resolvers.'].name;
                all.id = json_data['resolvers.'].uuid;
                DS.global_top_data['resolvers.'] = all;

                month.resolved = json_data['resolvers.last month'].changes;
                month.resolvers = json_data['resolvers.last month'].name;
                month.id = json_data['resolvers.last month'].uuid;
                DS.global_top_data['resolvers.last month'] = month;

                year.resolved = json_data['resolvers.last year'].changes;
                year.resolvers = json_data['resolvers.last year'].name;
                year.id = json_data['resolvers.last year'].uuid;
                DS.global_top_data['resolvers.last year'] = year;

                cb();
        }).fail(function() {
            console.log("**** widget disabled. Missing " + json_file);
        });
    }

    function getRandomId() {
        return Math.floor(Math.random()*1000+1);
    }

    function loadHTMLEvolParameters(htmldiv, config_viz){
        /*var metrics = $(htmldiv).data('metrics');
        var ds = $(htmldiv).data('data-source');
        var DS = Report.getDataSourceByName(ds);
        if (DS === null) return;*/
        config_viz.help = true;
        var help = $(htmldiv).data('help');
        if (help !== undefined) config_viz.help = help;
        config_viz.show_legend = false;
        if ($(htmldiv).data('frame-time'))
            config_viz.frame_time = true;
        config_viz.graph = $(htmldiv).data('graph');
        if ($(htmldiv).data('min')) {
            config_viz.show_legend = false;
            config_viz.show_labels = true;
            config_viz.show_grid = true;
            // config_viz.show_mouse = false;
            config_viz.help = false;
        }
        if ($(htmldiv).data('legend'))
            config_viz.show_legend = true;
        config_viz.ligth_style = false;
        if ($(htmldiv).data('light-style')){
            config_viz.light_style = true;
        }
        if ($(htmldiv).data('custom-title')){
            config_viz.custom_title = $(htmldiv).data('custom-title');
        }
        if (config_viz.help && $(htmldiv).data('custom-help')){
            config_viz.custom_help = $(htmldiv).data('custom-help');
        } else {
            config_viz.custom_help = "";
        }
        // Repository filter used to display only certain repos in a chart
        if ($(htmldiv).data('repo-filter')){
            config_viz.repo_filter = $(htmldiv).data('repo-filter');
        }
        // In unixtime
        var start = $(htmldiv).data('start');
        if (start) config_viz.start_time = start;
        var end = $(htmldiv).data('end');
        if (end) config_viz.end_time = end;

        var remove_last_point = $(htmldiv).data('remove-last-point');
        if (remove_last_point) config_viz.remove_last_point = true;

        return config_viz;
    }
})();

Array.prototype.SumArray = function (arr) {
    var sum = [];
    if (arr !== null && this.length === arr.length) {
        for (var i = 0; i < arr.length; i++) {
            sum.push(this[i] + arr[i]);
            }
        }
    return sum;
};

Loader.data_ready(function() {
    Resolved.chart_widget();
    Resolved.top_widget();
});

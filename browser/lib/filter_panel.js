/*
 * Copyright (C) 2015 Bitergia
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

var Filter = {};

(function() {

    var evo_data = undefined;
    var static_data = undefined;

    function getParameter(param){
        if ($.urlParam(param) === null) return false;
        return $.urlParam(param);
    }

    function filterEnabled(ds_name,filter){
        var mele = Report.getMenuElements();
        myfilter= ds_name + ':' + filter;
        if ( mele['filter'].indexOf(myfilter) >= 0)
            return true;
        return false;
    }

    /*
    * Returns object created from data filtered using the metric names
    * and the filter object
    * @param {object()} data - Object with all the metrics in nested arrays
    * @param {string[]} metric_names - Array with metric names
    * @param {object()} filter - Object with data used to filter the content
    */
    function filterMetrics(data, metric_names, filter){ //}, items, convert, start, end){
        // the data about DataProcess could be instering here:
        // convert, filterDates, frame_time, etc ..

        // filter by regexp
        var selected_filters = [];
        $.each(data.filter, function(id,value){
            if(value.indexOf(filter.regexp) === 0){
                selected_filters[selected_filters.length] = id;
            }
        });

        var selected_data = {};
        selected_data.filter = [];
        $.each(metric_names, function(id, mname){
            selected_data[mname] = [];
        });

        $.each(selected_filters, function(id, global_pos){
            //global_pos = 1 , 2, 4, 5, 6, 10
            selected_data.filter[selected_data.filter.length] = data.filter[global_pos];
            $.each(metric_names, function(id, mname){
                var aux_len = selected_data[mname].length;
                selected_data[mname][aux_len] = data[mname][global_pos];
            });
        });

        // we need always unixtime
        selected_data['unixtime'] = data['unixtime'];
        selected_data.strdate = data.date;
        return selected_data;
    }

    /*
    * Returns sorted array using the second item of the nested array
    * @param {integer[]} bi_array - Array of integer
    */
    function sortBiArray(bi_array){
        bi_array.sort(function(a, b) {
            return (a[1] < b[1] || a[1] === undefined)?1:-1;
        });
        return bi_array;
    }

    /*
    * Retuns array of sorted items (the key we'll use to sort the data object)
    * sorted by order_by
    * @param {string} order_by - Metric name
    */
    function getSortedItemsBy(order_by){
        var item_value = [];
        var sorted = [];
        $.each(static_data.filter, function(id, f){
            var mylen = item_value.length;
            var metric_value = static_data[order_by][id]
            item_value[mylen] = [f,metric_value];
        });
        item_value = sortBiArray(item_value); //sorted filters [[filter,unit]]
        $.each(item_value, function(id,value){
            sorted[sorted.length] = value[0];
        });
        return sorted
    }

    /*
    * Order the metrics in the data object using order_by. Returns a new object
    * @param {object()} data - object with nested arrays
    * @param {string} order_by - Metric name
    * @param {string[]} metric_names - Array of metric names
    */
    function orderDataBy(data, order_by, metric_names){
        var sorted_data = {};
        var items_sorted = getSortedItemsBy(order_by);

        //we initialize the new object
        sorted_data.filter = [];
        sorted_data.strdate = data.strdate;
        sorted_data.unixtime = data.unixtime;
        $.each(metric_names, function(id, name){
            sorted_data[name] = [];
        });

        $.each(items_sorted, function(id, value){
            var pos = data.filter.indexOf(value);
            var newpos = sorted_data.filter.length;
            if (pos < 0){return;}
            sorted_data.filter[newpos] = value;
            $.each(metric_names, function(subid, name){
                sorted_data[name][newpos] = data[name][pos];
            });
        });
        return sorted_data;
    };

    /*
    * Main function
    */
    Filter.widget = function(){
        var divs = $(".List2Timeseries");
        if (divs.length > 0){
            $.each(divs, function(id, div) {
                /* FIXME sanity checks for all this variables */
                ds_name = getParameter('filter_ds_name');
                aux_mn = getParameter('filter_metric_names');
                metric_names = aux_mn.split('+');
                filter_names = getParameter('filter_names');
                order_by = getParameter('filter_order_by');
                filter_by = getParameter('filter_by_item');
                fiitem = getParameter('filter_item');
                fiitem = fiitem.replace('%20',' '); //FIXME awful hack!!!!

                DS = Report.getDataSourceByName(ds_name);
                if (DS === null) return;
                if (DS.getData().length === 0) return; /* no data for data source*/

                /*check if filter is available*/
                if (!div.id) div.id = "Parsed" + getRandomId();
                if (filterEnabled(ds_name, filter_names)){
                    //$("#"+div.id).append("<p>The page you request is available</p>");
                    loadData(ds_name, filter_names,
                        function(){
                            displayList(div,evo_data,metric_names, fiitem, order_by);
                        });
                    }
                else{
                    $("#"+div.id).append("<p>The page you request is not available</p>");
                }
            });
        }
    }

    /*
    * Loads two json files and store its value in evo_data and static_data
    * @param {string} ds_name - Data source name
    * @param {string} filter_names - Filter name (ex: company+country)
    * @param {function()} cb - Callback function
    */
    function loadData (ds_name, filter_names, cb) {
        filter_names = filter_names.replace('company','com').replace('country','cou');
        var evo_json_file = "data/json/" + ds_name + '-' + filter_names + "-all-evolutionary.json";
        var static_json_file = "data/json/" + ds_name + '-' + filter_names + "-all-static.json";
        $.when($.getJSON(evo_json_file),$.getJSON(static_json_file)
                ).done(function(evo_json_data,static_json_data) {
                evo_data = evo_json_data[0];
                static_data = static_json_data[0];
                cb();
        }).fail(function() {
            console.log("Filter " + filter_names + " widget disabled for "
                        + ds_name + ". Check these files exit: "
                        + evo_json_file + ',' + static_json_file);
        });
    }

    /*
    * @param {string} div - Document object with the div to display the list
    * @param {string[]} metric_names - Array of metric names
    * @param {string} filter_name - Value of the filter to be applied to data
    * @param {string} order_by - Metric name
    */
    function displayList(div, data, metric_names, filter_item, order_by){
        var history = {};

        var filter = {};
        filter.convert = false;
        filter.startdate = undefined;
        filter.regexp = filter_item + '_'; //Liferay_

        var data_filtered = filterMetrics(data, metric_names, filter);
        var data_filtered = orderDataBy(data_filtered, order_by, metric_names);
        if (!div.id) div.id = "Parsed" + getRandomId();

        $.each(data_filtered.filter, function(id,value){
            var rowid = getRandomId();
            var counter = id + 1;
            if(id === 0){ //if first
                $("#"+div.id).append('<table class="table table-hover">');
            }
            var aux_str = value.split('_').join('').replace(filter_item,'');
            $("#" + div.id + ' table').append(HTMLli(aux_str, metric_names,
                                                rowid, counter));
            /*if(id === (data_filtered.filter.length - 1)){ //if last
                $("#"+div.id).append('</table>');
            }*/

            $.each(metric_names, function(subid, mname){
                data_chart = {};
                data_chart.unixtime = data_filtered.unixtime;
                data_chart.strdate = data_filtered.strdate;
                data_chart.lines_data = [];
                data_chart.lines_data[0] = data_filtered[mname][id];

                var div_name = 'tschart' + mname + rowid;
                var newdiv = $('#'+ div_name)[0];
                Charts.plotLinesChart(newdiv.id, [mname], data_chart);//, config_metric);
            });
        });
    }

    /*
    * Returns HTML for a list with two time serie metrics and a row name
    * @param {string} filter_name - Name of the filter (name of a country, company ..)
    * @param {string[]} metric_names - Names of the metrics
    * @param {integer} rowid - Integer used to display charts
    * @param {integer} counter - Integer to display the number of rows
    */
    function HTMLli(filter_name, metric_names, rowid, counter){
        var html = '<tr class="row">';
        html += '<td class="col-md-2"><p class="text-left">#'+counter;
        html += '&nbsp;<strong>' + filter_name + '</strong></p></td>';
        html += '<td class="col-md-5"><div id="tschart' + metric_names[0];
        html += rowid + '" style="height: 100px;"></div></td>';
        html += '<td class="col-md-5"><div id="tschart' + metric_names[1];
        html += rowid + '" style="height: 100px;"></div></td>';
        html += '</tr>';
        return html;
    }

    function getRandomId() {
        return Math.floor(Math.random()*100000+1);
    }

})();

Loader.data_ready(function() {
    Filter.widget();
});

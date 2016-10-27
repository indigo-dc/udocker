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

var ProjectsComparison = {};

( function() {

    var ts_project = {},
        top_project = {},
        static_project = {},
        max_metrics = {},
        compare_func = function(a, b){return a-b;};

    /*
    * Store max of metrics from both projects in max_metrics
    */
    function getMaxMetrics(metrics){
        var aux = [],
            temp_max = [];

        $.each(metrics, function(id, m){
            temp_max = [];
            $.each(Object.keys(ts_project), function(subid, p){
                aux = ts_project[p][m].slice(); // we have to copy the array
                temp_max[temp_max.length] = aux.sort(compare_func)[aux.length-1];
            });
            max_metrics[m] = temp_max.sort(compare_func)[temp_max.length-1];
        });
    }

    ProjectsComparison.Title = function(){
        var divs = $(".ProjectComparisonTitle");
        if (divs.length > 0){
            $.each(divs, function(id, div) {
                projects_aux = Report.getParameterByName('projects');
                projects = projects_aux.split(',');
                var aux_obj = {'project_a': projects[0], 'project_b': projects[1]};
                html = '<div class="row">'+
                    '<div class="col-md-6 text-left"><div class="well">' +
                    '<strong>&nbsp;Project name: {project_a}</strong></div></div>' +
                    '<div class="col-md-6 text-left"><div class="well">' +
                    '<strong>&nbsp;Project name: {project_b}</strong></div></div>' +
                    '</div>';
                $(div).append(html.supplant(aux_obj));
            });
        }
    };

    ProjectsComparison.SummaryNumbersWidget = function(){
        var divs = $(".ProjectComparisonTotalNumbers");
        if (divs.length > 0){
            $.each(divs, function(id, div) {
                projects_aux = Report.getParameterByName('projects');
                projects = projects_aux.split(',');

                // I need to get the 4 HTML charts before calling Viz ..
                getDataFor('ProjectComparisonTotalNumbers', 'scm', projects).done(function(p1,p2){
                    static_project[projects[0]] = p1[0];
                    static_project[projects[1]] = p2[0];
                    displayProjectsComparisonTotalNumbers(div, DS, ds_name, projects);
                }).fail(function(){
                    console.log('Error loading data from ProjectsComparisonTS widget');
                });
            });
        }
    };


    ProjectsComparison.TSwidget = function(){
        var divs = $(".ProjectsComparisonTS");
        if (divs.length > 0){
            $.each(divs, function(id, div) {
                ds_name = $(this).data('data-source');
                ts_metrics_aux = $(this).data('ts-metrics');
                ts_metrics = ts_metrics_aux.split(',');
                projects_aux = Report.getParameterByName('projects');
                projects = projects_aux.split(',');
                //metric_name = $(this).data('metric');
                /* this is a typical check, should be moved to a generic funct*/
                DS = Report.getDataSourceByName(ds_name);
                if (DS === null) return;
                if (DS.getData().length === 0) return; /* no data for data source*/

                // I need to get the 4 HTML charts before calling Viz ..
                getDataFor('ProjectsComparisonTS', ds_name, projects).done(function(p1,p2,p3,p4){
                    ts_project[projects[0]] = p1[0];
                    ts_project[projects[1]] = p2[0];
                    static_project[projects[0]] = p3[0];
                    static_project[projects[1]] = p4[0];
                    getMaxMetrics(ts_metrics);
                    displayProjectsComparison(div, DS, ds_name, ts_metrics, projects);
                }).fail(function(){
                    console.log('Error loading data from ProjectsComparisonTS widget');
                });
            });
        }
    };

    ProjectsComparison.Topwidget = function(){
        var divs = $(".ProjectsComparisonTop");
        if (divs.length > 0){
            $.each(divs, function(id, div) {
                var ds_name = $(this).data('data-source');
                var metric = $(this).data('metric');
                var period = $(this).data('period');
                if (period === undefined) {period = 'all';}
                projects_aux = Report.getParameterByName('projects');
                projects = projects_aux.split(',');
                //metric_name = $(this).data('metric');
                /* this is a typical check, should be moved to a generic funct*/
                DS = Report.getDataSourceByName(ds_name);
                if (DS === null) return;
                if (DS.getData().length === 0) return; /* no data for data source*/

                // I need to get the 4 HTML charts before calling Viz ..

                getDataFor('ProjectsComparisonTop', ds_name, projects).done(function(p1,p2){
                    top_project[projects[0]] = p1[0];
                    top_project[projects[1]] = p2[0];
                    displayProjectsComparisonTop(div, DS, ds_name, metric,
                        projects, period);}
                ).fail( function() {
                    console.log('Error loading data from ProjectsComparisonTop widget');
                });
            });
        }
    };

    ProjectsComparison.TopOrgWidget = function (){
        var divs = $(".ProjectsComparisonTopOrgs");
        if (divs.length > 0){
            $.each(divs, function(id, div) {
                var ds_name = $(this).data('data-source');
                var metric = $(this).data('metric');
                var period = $(this).data('period');
                if (period === undefined) {period = 'all';}
                projects_aux = Report.getParameterByName('projects');
                projects = projects_aux.split(',');

                //metric_name = $(this).data('metric');
                /* this is a typical check, should be moved to a generic funct*/
                DS = Report.getDataSourceByName(ds_name);
                if (DS === null) return;
                if (DS.getData().length === 0) return; /* no data for data source*/

                // We need the same code used by widget ProjectsComparisonTopOrg
                getDataFor('ProjectsComparisonTop', ds_name, projects).done(function(p1,p2){
                    top_project[projects[0]] = p1[0];
                    top_project[projects[1]] = p2[0];
                    displayProjectsComparisonTopOrg(div, ds_name, metric, projects);}
                ).fail( function() {
                    console.log('Error loading data from ProjectsComparisonTopOrg widget');
                });
            });
        }
    };

    function getPrjEvo(pname, suffix){
        var json_file_a = "data/json/" + pname + '-' + suffix + "-prj-evolutionary.json";
        return $.getJSON(json_file_a);
    }

    function getPrjTop (pname, suffix){
        var json_file= "data/json/" + pname + '-' + suffix + "-prj-top-authors.json";
        return $.getJSON(json_file);
    }

    function getPrjStatic (pname, suffix){
        var json_file= "data/json/" + pname + '-' + suffix + "-prj-static.json";
        return $.getJSON(json_file);
    }

    function getDataFor (widget_name, ds_name, projects){
        switch(widget_name){
            case 'ProjectsComparisonTS':
                suffix = ds_name.toLowerCase();
                return $.when(getPrjEvo(projects[0],suffix),getPrjEvo(projects[1],suffix),
                            getPrjStatic(projects[0],suffix),getPrjStatic(projects[1],suffix));
            case 'ProjectsComparisonTop':
                suffix = ds_name.toLowerCase();
                return $.when(getPrjTop(projects[0],suffix),getPrjTop(projects[1],suffix));
            case 'ProjectComparisonTotalNumbers':
                suffix = ds_name.toLowerCase();
                return $.when(getPrjStatic(projects[0],suffix),getPrjStatic(projects[1],suffix));
        }

    }

    function displayProjectsComparisonTop(div, DS, ds_name, metric, projects, period){
        var html = HTMLPrjComparisonTop(ds_name, projects, metric);
        if (!div.id) div.id = "Parsed69";
        $("#"+div.id).append(html);

        $.each(projects, function(id, pro){

            var class_name = pro + metric;
            class_name = class_name.toLowerCase().replace(/\s+/g, '');
            var divs = $("#Top" + class_name);
            if (divs.length > 0) {
                $.each(divs, function(id, div2) {
                    limit = 10;
                    people_links = true;
                    var desc_metrics = DS.getMetrics();
                    // metric, class_name, links_enabled, limit, period, ds_name
                    var opts = {'metric': metric, 'class_name': class_name,
                            'links_enabled': people_links, 'limit': limit,
                            'period': period, 'ds_name': ds_name,
                            'desc_metrics': desc_metrics};
                    Table.displayTopTable(div2, top_project[pro], opts);
                    /*Table.displayTopTable(div2, ds_name, top_project[pro], metric, limit,
                                        desc_metrics, people_links, period, class_name);*/
                });
            }
            var script = "<script>$('#myTab a').click(function (e) {e.preventDefault();$(this).tab('show');});</script>";
            $("#"+div.id).append(script);
        });
    }

    function displayProjectsComparisonTopOrg(div, ds_name, metric, projects){
        var html = HTMLPrjComparisonTopOrg(ds_name, projects, metric);
        if (!div.id) div.id = "Parsed69";
        $("#"+div.id).append(html);
        $.each(projects, function(id, pro){
            var class_name = pro + metric + 'org';
            class_name = class_name.toLowerCase().replace(/\s+/g, '');
            var divs = $("#Top" + class_name);
            if (divs.length > 0) {
                $.each(divs, function(id, div2) {
                    Table.simpleTable(div2, top_project[pro], ['Companies','Commits'], ['name','company_commits']);
                });
            }
        });
    }

    function displayProjectsComparisonTotalNumbers(div, DS, ds_name, projects){
        var html = HTMLPrjComparisonTN(projects);
        if (!div.id) div.id = "Parsed";
        $("#"+div.id).append(html);
    }

    function HTMLPrjComparisonTN(projects){
        var html = '<span class="row">';
        $.each(projects, function(id, myprj){
            var html_table;
            html_table = '<div class="col-md-6"><table class="table table-striped">';
            html_table += '<tr class="row"><td class="col-md-6">Number of repositories: {repositories}</td><td class="col-md-6">Total number of code developers: {authors}</td></tr>';
            html_table += '<tr class="row"><td class="col-md-6">Active code developers last year: {authors_365}</td><td class="col-md-6">New code developers last year: {newauthors_365}</td></tr>';
            html_table += '<tr class="row"><td class="col-md-6">Active code developers last month: {authors_30}</td><td class="col-md-6">New code developers last month: {newauthors_30}</td></tr>';
            html_table += '</table></div>';
            html += html_table.supplant(static_project[myprj]);
        });
        html += '</html>';
        return html;
    }

    function HTMLPrjComparisonTop(ds_name, projects, metric){
        var html = '<div class="row">';
        $.each(projects, function(id, pro){
            class_name = pro + metric;
            class_name = class_name.toLowerCase().replace(/\s+/g, '');
            html += '<div class="col-md-6"><div class="well">';
            html += '<div id="Top' +class_name+'">';
            html += '</div></div></div>';
        });
        html += '</div>';
        return html;
    }

    function HTMLPrjComparisonTopOrg(ds_name, projects, metric){
        var html = '<div class="row">';
        $.each(projects, function(id, pro){
            class_name = pro + metric + 'org';
            class_name = class_name.toLowerCase().replace(/\s+/g, '');
            html += '<div class="col-md-6"><div class="well">';
            html += '<div id="Top' +class_name+'">';
            html += '</div></div></div>';
        });
        html += '</div>';
        return html;
    }

    function displayProjectsComparison(div, DS, ds_name, metrics, projects){
        // 1. we get the HTML with bootstrap
        var html = HTMLTSComparison(ds_name, projects, metrics);
        if (!div.id) div.id = "Parsed";
        $("#"+div.id).append(html);

        $.each(metrics, function(id, metric){
            $.each(projects, function(id, pro){
                class_name = pro + metric;
                class_name = class_name.toLowerCase().replace(/\s+/g, '');
                var divs = $("#" + class_name);
                if (divs.length > 0) {
                    $.each(divs, function(id, div2) {
                        // we need always unixtime
                        selected_data = {};
                        selected_data.unixtime = ts_project[pro].unixtime;
                        selected_data.strdate = ts_project[pro].date;
                        selected_data.lines_data = [];
                        selected_data.lines_data[0] = ts_project[pro][metric];
                        if (Object.keys(max_metrics).indexOf(metric) >= 0){
                            selected_data.max = max_metrics[metric];
                            // we increase it for the Y axis
                            selected_data.max = selected_data.max +
                                                selected_data.max * 0.3;
                        }
                        Charts.plotLinesChart(div2.id, [metric], selected_data);//ts_project[pro]);
                    });
                }
            });
        });
    }

    function HTMLTrend(data, metric){
        //get metric from data
        //show_name
        var html = '<span class="row">';
        $.each([365,30,7], function(index, period) {

            var aux_obj = {'orientation': undefined, 'class': undefined,
                            'percent': undefined, 'value': undefined,
                            'period': period, 'netvalue': undefined};

            aux_obj.value = data[metric+"_"+period];
            aux_obj.netvalue = data["diff_net"+metric+"_"+period];
            aux_obj.percent = data["percentage_"+metric+"_"+period];
            aux_obj.percent = Math.round(aux_obj.percent*10)/10; // round "original" to 1 decimal

            var str_percentagevalue = '';
            if (aux_obj.percent === 0){
                aux_obj.orientation = 'right';
                aux_obj.class = 'zeropercent';
            }else if (aux_obj.netvalue > 0 ){
                aux_obj.orientation = 'up';
                aux_obj.class = 'pospercent';
            }else if (aux_obj.netvalue < 0){
                aux_obj.orientation = 'down';
                aux_obj.class = 'negpercent';
            }

            var aux_html = '<span class="col-md-4 text-center"><span class="dayschange">Last {period} days:</span> {value}<br>';
            aux_html += '<i class="fa fa-arrow-circle-{orientation}"></i> <span class="{class}">&nbsp;{percent}%</span>&nbsp;';
            aux_html += '</span><!--col-xs-4-->';
            html += aux_html.supplant(aux_obj);
        });
        html += '</span>';
        return html;
    }

    function HTMLTSComparison(ds_name, projects, metrics){
        var html,
            aux_html,
            aux_obj;
        html = '<div class="row">';

        $.each(metrics, function(id, metric){
            $.each(projects, function(id, pro){
                class_name = pro + metric;
                class_name = class_name.toLowerCase().replace(/\s+/g, '');
                aux_html = '';
                aux_obj = {'class_name':class_name};

                aux_html += '<div class="col-md-6"><div class="well">';
                aux_html += '<div id="{class_name}" style="height: 100px;">';
                aux_html += '</div>';
                aux_html += HTMLTrend(static_project[pro], metric); //trends
                aux_html += '</div></div>';

                html += aux_html.supplant(aux_obj);
            });
        });
        html += '</div>';

        return html;
    }

    function getRandomId() {
        return Math.floor(Math.random()*1000+1);
    }

})();

Loader.data_ready(function() {
    ProjectsComparison.TSwidget();
    ProjectsComparison.Topwidget();
    ProjectsComparison.SummaryNumbersWidget();
    ProjectsComparison.Title();
    ProjectsComparison.TopOrgWidget();
});

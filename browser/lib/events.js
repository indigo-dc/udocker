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
 *
 */

var Events = {};

(function() {

    Events.events = {};
    var data_callbacks = [];

    Events.data_ready = function(callback) {
        data_callbacks.push(callback);
    };

    Events.widget = function(){
        var divs = $(".Events");
        if (divs.length > 0){
            $.each(divs, function(id, div) {
                ds_name = $(this).data('data-source');
                event_ = $(this).data('event');
                /* this is a typical check, should be moved to a generic funct*/
                DS = Report.getDataSourceByName(ds_name);
                if (DS === null) return;
                if (DS.getData().length === 0) return; /* no data for data source*/

                loadEventsData(ds_name,
                    function(){
                        displayEvents(div, ds_name, event_);
                        });
            });
        }
        var divs = $(".Scout");
        if (divs.length > 0){
            $.each(divs, function(id, div) {
                loadScoutEventsData(
                    function(){
                        displayEventsScout(div);
                    });
            });
        }
    };

    function loadScoutEventsData (cb) {
        var json_file = "data/json/scout.json";
        $.when($.getJSON(json_file)
                ).done(function(json_data) {
                Events.scout = json_data;
                cb();
                for (var j = 0; j < data_callbacks.length; j++) {
                    if (data_callbacks[j].called !== true) data_callbacks[j]();
                    data_callbacks[j].called = true;
                }
        }).fail(function() {
            console.log("Events widget disabled. Missing " + json_file);
        });
    }

    function loadEventsData (ds_name, cb) {
        suffix = ds_name.toLowerCase();
        var json_file = "data/json/" + suffix + "-events.json";
        $.when($.getJSON(json_file)
                ).done(function(json_data) {
                Events.events[suffix] = json_data;
                cb();
                for (var j = 0; j < data_callbacks.length; j++) {
                    if (data_callbacks[j].called !== true) data_callbacks[j]();
                    data_callbacks[j].called = true;
                }
        }).fail(function() {
            console.log("Events widget disabled. Missing " + json_file);
        });
    }

    function displayEvents (div, ds_name, event_) {
        // var html = HTMLEvents(ds_name, event_);
        // if (!div.id) div.id = "Parsed" + getRandomId();
        // $("#"+div.id).append(html);
        show_timeline(ds_name, event_);
    }

    function displayEventsScout (div) {
        // var html = HTMLEvents(ds_name, event_);
        // if (!div.id) div.id = "Parsed" + getRandomId();
        // $("#"+div.id).append(html);
        show_timeline_scout();
    }

    function HTMLEvents (ds_name, event_){
        var html = '<div class="row">';
        html += '<div class="col-md-12"><div class="well">';
        $.each(Events.events[ds_name][event_].uid, function(i, value) {
            // date, email, name, uid
            name = Events.events[ds_name][event_].name[i];
            first_date = Events.events[ds_name][event_].date[i];
            email = Events.events[ds_name][event_].email[i];
            html += "<div id =event-uid-'"+value+"' class='alert alert-success'>";
            html += "New code developer: " + name + "<br>" + first_date;
            html += "</div>";
        });
        html += '</div></div></div>';
        return html;
    }


    show_timeline = function(ds_name, event_) {
        var data = {
            "events":[]
        };

        // var newcomers = {"date": ["2015-01-14 13:57:23", "2015-01-05 12:46:02", "2014-10-24 15:42:35", "2014-10-24 09:00:36", "2014-10-02 21:08:59", "2014-08-11 11:39:13", "2014-06-11 11:19:23", "2014-06-06 11:30:46", "2014-05-26 00:23:42", "2014-05-08 05:07:36", "2014-01-23 21:26:56", "2013-12-23 11:00:16", "2013-10-21 20:39:52", "2013-10-16 12:23:01", "2013-10-14 16:11:52", "2013-09-09 18:16:51", "2013-09-02 11:51:21", "2013-08-13 08:02:34", "2013-07-09 19:36:28", "2013-06-10 22:37:22", "2013-05-29 01:17:02", "2013-05-29 01:17:02", "2013-05-15 11:20:48", "2013-03-13 20:48:44", "2013-02-19 22:31:58", "2013-01-17 11:39:39", "2012-11-28 16:48:09", "2012-09-20 14:38:54", "2012-09-20 14:38:54", "2012-09-10 16:57:43", "2012-08-31 17:01:09", "2012-08-17 17:29:59", "2012-07-11 03:20:39", "2012-07-11 03:20:39", "2011-11-03 17:24:54", "2011-08-19 12:40:45", "2011-07-04 17:10:25", "2011-06-01 13:01:42", "2009-09-21 07:05:32", "2009-08-10 10:03:16", "2009-08-10 10:03:16", "2009-02-19 15:31:16", "2008-10-10 10:35:12", "2008-10-10 10:35:12", "2008-07-22 13:12:43", "2008-03-04 00:04:02", "2008-02-19 10:32:45", "2008-02-19 10:32:45", "2007-08-29 18:35:25", "2007-08-29 18:35:25", "2007-08-29 18:35:25", "2007-08-29 18:35:25", "2007-08-29 18:35:25", "2007-08-29 18:35:25", "2007-07-31 11:41:26", "2007-07-31 11:41:26", "2007-04-11 17:14:52", "2007-04-11 17:14:52", "2007-04-11 17:14:52", "2007-03-27 10:27:28", "2007-01-23 18:21:09", "2007-01-23 18:21:09", "2007-01-23 18:21:09", "2007-01-23 18:21:09", "2007-01-23 18:21:09", "2007-01-23 18:21:09", "2007-01-18 18:07:19", "2007-01-18 15:17:55", "2006-12-02 17:18:18", "2006-12-02 17:18:18", "2006-12-02 17:18:18", "2006-11-13 19:19:56", "2006-11-13 19:19:56", "2006-11-13 19:19:56", "2006-11-13 19:19:56", "2006-07-08 15:44:09", "2006-07-08 12:03:48"], "email": ["alberto.martin@bitergia.com", "alberto.martin@imdea.org", "owl@atari.bitergia.net", "jsmanrique@gmail.com", "rodrigokuroda@users.noreply.github.com", "jsmanrique@bitergia.com", "mikael.niemela@tut.fi", "joku@osoite.fi", "vsacct@dashboard.eclipse.org", "justin@gluster.org", "lin.zhp@gmail.com", "www-data@bitergia.com", "chilli@chilli-K55VM.(none)", "feinomenon@gmail.com", "sumanah@panix.com", "jdworakowski@uwaterloo.ca", "tthebosss@hotmail.com", "owl@acsblog.es", "mark.donohoe@hp.com", "linzhp@lzp-Linux.(none)", "info@bitergia.com", "owlbot@bitergia.com", "mdoriagcortazar@gmail.com", "ishakhat@mirantis.com", "andygrunwald@gmail.com", "himself@maelick.net", "adina.barham@yahoo.com", "dicortazar@gmail.com", "dicortazar@gmail.com", "fontanon@emergya.es", "lchow@redhat.com", "companheiro.vermelho@gmail.com", "lcanas@bitergia.com", "lcanas@bitergia.com", "glimmer_phoenix@yahoo.es", "tom.mens@umons.ac.be", "dneary@maemo.org", "paulo@softwarelivre.org", "frivas@libresoft.es", "gpoo@calcifer.org", "gpoo@gnome.org", "sduenas@gsyc.es", "jfcogato@libresoft.es", "jfcogato@libresoft.es", "lilitovar@libresoft.es", "sduenas@gsyc.escet.urjc.es", "lcanas@gsyc.es", "lcanas@libresoft.es", "dizquierdo@bitergia.com", "dizquierdo@bitergia.com", "dizquierdo@libresoft.es", "dizquierdo@gsyc.escet.urjc.es", "dizquierdo@gsyc.es", "dizquierdo@libresoft.es", "sduenas@libresoft.es", "sduenas@bitergia.com", "carlosgc@gsyc.escet.urjc.es", "carlosgc@gnome.org", "carlosgc@libresoft.es", "randradas@libresoft.es", "acs@acsblog.es", "acs@bitergia.com", "acs@bitergia.com", "acs@bitergia.com", "acs@barrapunto.com", "acs@gsyc.es", "jgascon@gsyc.es", "lcanas@libresoft.es", "jgb@libresoft.es", "jgb@bitergia.com", "jgb@gsyc.es", "israel.herraiz@gmail.com", "herraiz@gsyc.escet.urjc.es", "herraiz@hardy.caminos.upm.es", "herraiz@gsyc.es", "grex@libresoft.es", "anavarro@gsyc.es"], "name": ["albertinisg", "Alberto Mart\u00edn", "Automator owl", "Manrique Lo\u0301pez", "Rodrigo Kuroda", "jsmanrique", "Mikael Niemel\u00e4", "Pertti", "vsacct", "Justin Clift", "Zhongpeng Lin (\u6797\u4e2d\u9e4f)", "www-data", "Carlos Gonzalez", "Fei Dong", "Sumana Harihareswara", "iKuba", "tthebosss", "Owl Bot Automator", "Mark Donohoe", "Zhongpeng Lin", "Owl Bot", "Owl Bot", "softmarina", "Ilya Shakhat", "Andy Grunwald", "Ma\u00eblick Claes", "adinabarham", "Daniel Izquierdo", "Daniel Izquierdo Cortazar", "J. F\u00e9lix Onta\u00f1\u00f3n", "Chow Loong Jin", "companheiro.vermelho@gmail.com", "Luis Ca\u00f1as D\u00edaz", "Luis Ca\u00f1as-D\u00edaz", "Felipe Ortega", "Tom Mens", "Dave Neary", "Paulo Meirelles", "Francisco Rivas", "Germ\u00e1n P\u00f3o-Caama\u00f1o", "Germ\u00e1n P\u00f3o-Caama\u00f1o", "Santiago Due\u00f1as Dom\u00ednguez", "Juan Francisco Gato Luis", "Jos\u00e9 Francisco Gato", "Liliana Tovar", "Santiago Due\u00f1as Dominguez", "Luis Ca\u00f1as D\u00edaz", "Luis Ca\u00f1as D\u00edaz", "Daniel Izquierdo Cortazar", "Daniel Izquierdo", "Daniel Izquierdo", "Daniel Izquierdo Cortazar", "Daniel Izquierdo Cortazar", "Daniel Izquierdo Cortazar", "Santiago Due\u00f1as", "Santiago Due\u00f1as", "Carlos Garcia Campos", "Carlos Garcia Campos", "Carlos Garcia Campos", "Roberto Andradas", "alvaro del castillo", "Alvaro del Castillo San Felix", "Alvaro del Castilo", "Alvaro del Castillo", "Alvaro del Castillo", "Alvaro del Castillo", "Jorge Gasc\u00f3n", "Luis Ca\u00f1as", "Jesus M. Gonzalez-Barahona", "Jesus M. Gonzalez-Barahona", "Jesus M. Gonzalez-Barahona", "Israel Herraiz", "Israel Herraiz", "Israel Herraiz", "Israel Herraiz", "Gregorio Robles", "Alvaro Navarro"], "uid": [204, 67, 16, 22, 52, 66, 51, 50, 20, 60, 32, 19, 49, 76, 77, 75, 12, 11, 10, 33, 9, 9, 8, 48, 31, 34, 74, 7, 7, 59, 58, 47, 5, 5, 46, 64, 56, 63, 72, 44, 44, 70, 29, 29, 41, 25, 21, 21, 6, 6, 6, 6, 6, 6, 4, 4, 23, 23, 23, 54, 1, 1, 1, 1, 1, 1, 53, 30, 3, 3, 3, 37, 37, 37, 37, 36, 35]};
        var events = Events.events[ds_name][event_];

        $.each(events.date, function(index){
            data.events.push({"uid":events.uid[index],"name":events.name[index], 
                              "email":events.email[index], 
                              "timestamp":events.date[index], 
                              "event_text": "Has become a new member"});
        });

        $.each(data.events, function(index, event){
            event.timestamp = moment(event.timestamp, "YYYY-MM-DD hh:mm:ss").fromNow();
        });

        var template = $('#template').html();

        Mustache.parse(template);
        var rendered = Mustache.render(template, data);
        $('#target').html(rendered);
    };

    function get_event_type(type, data_source) {
        // Translare event code to human language
        var human_type = type;
        if (data_source === "github") {
            if (type == "CreateEvent") {
                human_type = "new repository";
            }
        }
        else if (data_source === "stackoverflow") {
            if (type === 1) {
                human_type = "new question";
            } else if (type == 2) {
                human_type = "new answer";
            } else if (type == 3) {
                human_type = "new comment";
            }
        }
        else if (data_source === "mail") {
            human_type = "mail sent";
        }
        return human_type;
    }

    function get_event(data, index, fields, data_source) {
        // Create a dict with event data
        event = {};
        $.each(fields, function(i) {
            var val = undefined;
            if (data[fields[i]] !== undefined) {
                val = data[fields[i]][index];
            }
            event[fields[i]] = val;
            if (fields[i] === "type") {
                event[fields[i]] = get_event_type(val, data_source);
            }
        });
        if (data_source === "mail") {
            // mail events do not include type
            event.type = "email sent";
        }
        return event;
    }

    function events_sort(events,  field) {
        // All events include a date field
        function compare(event1, event2) {
            var res;

            date1 = Date.parse(event1.date.replace(/-/g,"/"));
            date2 = Date.parse(event2.date.replace(/-/g,"/"));

            if (date1<date2) {
                res = 1;
            }
            else if (date1>date2) {
                res = -1;
            }
            else {
                res = 0;
            }
            return res;
        }
        events.sort(compare);
        return events;
    }

    show_timeline_scout = function(ds_name, event_) {
        var events_ds = Events.scout;
        var timeline_events = []; // All events to be shown in the timeline

        // First, create the common time series format: [date:[d1,d2, ...], event:[e1,e2, ...]]
        $.each(events_ds, function(data_source, events){
            fields = Object.keys(events);
            $.each(events.date, function(i){
                event = get_event(events, i, fields,data_source);
                event[data_source] = 1;
                event.timestamp = moment(event.date, "YYYY-MM-DD hh:mm:ss").fromNow();
                timeline_events.push(event);
            });
        });
        // Order events in time to build a common time line with the events from all data sources
        timeline_events = events_sort(timeline_events);

        var template = $('#template_scout').html();

        Mustache.parse(template);
        var rendered = Mustache.render(template,
                {"events":timeline_events,
                 "limitLength" : function() {
                     var limit = 80;
                     return function(text, render) {
                         var r = render(text);
                         var keyword = 'centos';
                         var n = r.search(new RegExp(keyword, "i"));
                         var out = '';
                         if (n>-1) {
                             if (n-limit>0) {
                                 out = "..." + r.substr(n-limit,limit);
                             }
                             out += "<b>"+r.substr(n,keyword.length)+"</b>";
                             out += r.substr(n+keyword.length,limit) +'...';
                         } else {
                             out = r.substr(0,80) + '...';
                         }
                         return out;
                     };
                 }
                });
        $('#target').html(rendered);
    };

    function getRandomId() {
        return Math.floor(Math.random()*1000+1);
    }

})();

Loader.data_ready(function() {
    Events.widget();
});

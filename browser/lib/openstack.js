var Openstack = {};

(function() {
    var data_loaded = false;

    function orderCompanies(ds, metric) {
        var global_data = Openstack.companies.global[ds];
        var company_metric = [];
        var order = [];

        $.each(global_data, function(name, value) {
            company_metric.push([name, global_data[name][metric]]);
        });

        company_metric.sort(function(a, b) {return b[1] - a[1];});

        $.each(company_metric, function(id, value) {
            order.push(value[0]);
        });
        return order;
    }

    function createViz(divid, ds, file, metric, config, show_others, evol) {
        var order = orderCompanies(ds, metric);
        if (evol) {
            var evol_data = Openstack.companies.evol[ds];
            Viz.displayMetricCompanies(metric, evol_data, divid, config, null, null, order);
        }
        else {
            var global_data = Openstack.companies.global[ds];
            Viz.displayMetricSubReportStatic(metric, global_data, order, divid, config);
        }
    }

    function displayCompaniesList() {
        var json_file = Report.getDataDir() + '/scm-companies.json';

        $.getJSON(json_file, null, function(data) {
            var count = 0;
            var links = "";

            $.each(data, function(index, company) {
                if (count == 10) return false;
                if (company === "Others") return true;
                if (company.match("^\-")) return true;

                link = '<a href="company.html?company=' + company +
                       '&data_dir=' + Report.getDataDir() + '">' + company + '</a> | ';
                links = links + link;

                ++count;
            });

            $("#" + "companies_links").append(links);

        });
    }

    function displayCompaniesSummary(divid, ds, file, metric, config, show_others, evol) {
        config.show_title = false;
        if (data_loaded === true && false) {
            createViz(divid, file, metric, config, show_others, evol);
        }
        var data_dir = Report.getDataDir();
        // var json_file = "data/json/"+file;
        var json_file = data_dir +"/"+file;
        var marks = ['unixtime','week','id','date'];
        $.getJSON(json_file, null, function(data) {
            $.each(data, function(field, values) {
                if ($.inArray(field, marks) == -1) {
                    Openstack.addCompanyEvol(ds, field, metric, values);
                }
                else {
                    Openstack.addDatesField(ds, field, values);
                }
            });
            Openstack.addDatesCompanies(ds);
            Openstack.buildCompaniesGlobal(ds, metric);
            createViz(divid, ds, file, metric, config, show_others, evol);
            data_loaded = true;
        });
    }

    function convertCompaniesSummary() {
        var div_summary = "CompaniesSummary";
        divs = $("."+div_summary);
        if (divs.length > 0) {
            $.each(divs, function(id, div) {
                ds = $(this).data('data-source');
                if (ds === null) return;
                var evol = $(this).data('evol');
                var metric = $(this).data('metric');
                var config = {};
                div.id = div_summary + "-" + metric + "-" + evol;
                file = $(this).data('file');
                var stacked = false;
                if ($(this).data('graph')) stacked = true;
                if ($(this).data('stacked')) stacked = true;
                config.lines = {stacked : stacked};
                config.graph = $(this).data('graph');
                var show_others = $(this).data('show-others');
                config.show_legend = $(this).data('legend');
                if ($('#'+$(this).data('legend-div')).length>0) {
                    config.legend = {
                    container: $(this).data('legend-div')};
                } else config.legend = {container: null};
                displayCompaniesSummary(div.id, ds, file, metric, config, show_others, evol);
            });

            displayCompaniesList();
        }
    }

    // Sum evolution date to compute total (global) data
    Openstack.buildCompaniesGlobal = function(ds, metric) {
        $.each(Openstack.companies.evol[ds], function(company, values) {
            var total = 0;
            for (var i=0; i<values[metric].length; i++) {
                total += values[metric][i];
            }
            if (!Openstack.companies.global[ds])
                Openstack.companies.global[ds] = {};
            Openstack.companies.global[ds][company] = {};
            Openstack.companies.global[ds][company][metric] = total;
        });
    };

    Openstack.addDatesField = function(ds, field, values) {
        if (!Openstack.dates[ds])
            Openstack.dates[ds] = {};
        Openstack.dates[ds][field] = values;
    };

    Openstack.addCompanyEvol = function(ds, name, field, values) {
        if (!Openstack.companies.evol[ds])
            Openstack.companies.evol[ds] = {};
        Openstack.companies.evol[ds][name] = {};
        Openstack.companies.evol[ds][name][field] = values;
    };

    Openstack.addDatesCompanies = function(ds) {
        $.each(Openstack.companies.evol[ds], function(company, values) {
            $.each(Openstack.dates[ds], function(mark, stamps) {
                Openstack.companies.evol[ds][company][mark] = stamps;
            });
        });
    };

    Openstack.build = function() {
        Openstack.companies = {global:{},evol:{}};
        Openstack.dates = {};
        convertCompaniesSummary();
    };
})();

Loader.data_ready_global(function() {
    Openstack.build();
});

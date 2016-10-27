var vizjsDoc = {};

(function() {

    var div_sectios, div_display, div_syntax, div_params;

    // Items to show as example. Depends on tests data to be available.
    var upeople_id = "13";
    // var filter = "repos";
    var filter = "companies";
    // var item = "DonationInterface.git";
    var item = "users";

    function getMethodDesc(method_name) {
        var method_desc;
        $.each(vizjsDoc.API.sections, function(section, contents) {
            $.each(contents, function(method, desc) {
                if (method_name === method) method_desc = desc;
            });
        });
        return method_desc;
    }

    // Fills params with default values
    function addParamsDiv(divid, params) {
        var contents = "<ul>";
        $.each(params, function(param, desc) {
            contents += "<li>"+param;
            if (desc.help) contents += ": "+desc.help;
            contents += "</li>";
            if (param === "data-source")
                $("#"+divid).attr("data-"+param,"scm");
            if (param === "data-source" && divid === "TimeTo")
                $("#"+divid).attr("data-"+param,"its");
            if (param === "radius")
                $("#"+divid).attr("data-"+param,"0.5");
            if (param === "file" && divid === "Treemap")
                $("#"+divid).attr("data-"+param,"treemap.json");
            if (param === "metric")
                $("#"+divid).attr("data-"+param,"scm_commits");
            if (param === "metric" && divid === "FilterItemTop")
                $("#"+divid).attr("data-"+param,"scm_authors");
            if (param === "metric" && divid === "Top")
                $("#"+divid).attr("data-"+param,"authors");
            if (param === "metrics")
                $("#"+divid).attr("data-"+param,"scm_commits,scm_authors");
            if (param === "period")
                $("#"+divid).attr("data-"+param,"Year");
            if (param === "period" && (divid === "Top" || divid === "FilterItemTop"))
                $("#"+divid).attr("data-"+param,"last year");
            if (param === "period" && divid === "Demographics")
                $("#"+divid).attr("data-"+param,"0.25");
            if (param === "field")
                $("#"+divid).attr("data-"+param,"scm_commits");
            if (param === "type")
                $("#"+divid).attr("data-"+param,"fix");
            if (param === "type" && divid === "Demographics")
            $("#"+divid).attr("data-"+param,"aging");
            if (param === "quantil")
                $("#"+divid).attr("data-"+param,"X0.99,X0.95");
            if (param === "person_id")
                $("#"+divid).attr("data-"+param, upeople_id);
            if (param === "filter")
                $("#"+divid).attr("data-"+param, filter);
            if (param === "page")
                $("#"+divid).attr("data-"+param,"1");
            if (param === "item")
                $("#"+divid).attr("data-"+param,item);
            if (param === "graph")
                $("#"+divid).attr("data-"+param,"bars");
            if (param === "people_links")
                $("#"+divid).attr("data-"+param,"false");
        });
        contents += "</ul>";
        $("#"+div_params).append(contents);
    }

    function htmlEscape(str) {
        return String(str)
                .replace(/&/g, '&amp;')
                .replace(/"/g, '&quot;')
                .replace(/'/g, '&#39;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;');
    }

    // Build a new div with method info and convert it
    vizjsDoc.showDiv = function(method) {
        var desc = getMethodDesc(method);
        var new_div = "<div";
        new_div += " id='"+method+"'";
        new_div += " class='"+method;
        if (desc.classCSS) new_div += " " + desc.classCSS;
        new_div += "'></div>";
        var convertFn = Convert["convert"+method];
        if (!convertFn) return;
        $("#"+div_params).empty();
        $("#"+div_display).empty();
        $("#"+div_syntax).empty();
        $("#"+div_syntax_help).empty();
        $("#"+div_display).append(new_div);
        if (desc.help) {
            $("#"+div_syntax_help).append(desc.help);
        }
        if (desc.params) {
            $("#"+method).addClass(method);
            addParamsDiv(method, desc.params);
        }
        $("#"+div_syntax).append(htmlEscape($("#"+method).parent().html()));
        // Some widgets needs data to be loaded first
        if (method === "PersonMetrics" || method === "PersonSummary")
            Convert.convertPeople(upeople_id)
        else if (method.indexOf("FilterItems") === 0)
            Convert.convertFilterStudy(filter);
        else if (method.indexOf("FilterItem") === 0) {
            Convert.convertFilterStudyItem(filter, item);
            // Temporal hack because FilterItem functions are called one time
            convertFn(filter, item);
        }
        else if (method.indexOf("Microdash") === 0) {
            convertFn();
            Convert.convertMetricsEvol();
        }
        else
            convertFn();
    };

    vizjsDoc.build = function() {
        var sections = "";
        $.each(vizjsDoc.API.sections, function(section, contents) {
            sections += "<h4>"+section+"<h4>";
            $.each(contents, function(method, method_desc) {
                sections += "<button onClick='";
                sections += "vizjsDoc.showDiv(\""+method+"\")";
                sections += "' class='btn'>"+method+"</button>";
            });
        });
        $("#"+div_sections).append(sections);
    };

    vizjsDoc.show = function(divid, divdisplay, divSyntax, 
            divSyntaxHelp, divParams) {
        div_sections = divid;
        div_display = divdisplay;
        div_syntax = divSyntax;
        div_syntax_help = divSyntaxHelp;
        div_params = divParams;
        $.getJSON("vizjsapi2.json", null, function(apidata) {
            vizjsDoc.API = apidata;
            vizjsDoc.build();
        });
    };
})();

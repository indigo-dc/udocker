# Grimoire dash configuration file

```
{
    "menu":{
	"scm": [
            "companies",
            "companies-summary",
            "contributors",
            "countries",
            "domains",
            "projects",
            "repos"
	],
	"mls": [
            "companies",
            "contributors",
            "countries",
            "domains",
            "projects",
            "repos"
	],
	"qaforums": [
            "contributors"
	],
	"irc": [
            "contributors",
            "repos"
	],
	"studies": [
            "demographics"
	],
	"its": [
            "companies",
            "contributors",
            "countries",
            "domains",
            "projects",
            "repos",
            "states"
	],
	"scr": [
            "companies",
            "companies-summary",
            "countries",
            "projects",
            "repos"
	],
	"downloads": [],
	"forge": [],
	"wiki": [],
	"extra": [
	    ["Link 1", "http://bitergia.com"],
	    ["Link 2", "https://twitter.com/bitergia"],
	    ["Link 2", "https://twitter.com/flossmetrics"]
	],
```
studies_extra will link ad-hoc studies

```
    "studies_extra": [
        ["pepe","./project_comparison.html?projects=OpenShift%20v2,OpenShift%20v3"]
    ],
```
sometimes is easier to rename the section instead of deleting it
```
	"project_map-OFF": [],
```
filter: List of double filters with data source like scm:company+country
```
    "filter": ["scm:company+country","its:company+country"],
```
filter_companies: List of companies will show only these companies
```
    "filter_companies":["Liferay","non Liferay"]
    },
    "releases":[],
```
threads_site: Web site to be appended to search URL
```
    "threads_site":"https://groups.google.com/"
}
```

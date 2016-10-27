# Jasmine tests for Bitergia dashboards

## Software
* tests use jasmine 1.3, in order to get some information about it you can
visit http://jasmine.github.io/1.3/introduction.html
* if you want to use the command line tests you need jasmine-headless-webkit
but its installation is a bit tricky and it's deprecated.

## Usage
* command line tests:
 ```
 make test
 ```
* web tests: visit the root of the dashboard with /test, if you are running your dash
 at localhost/dash/browser, visit
 ```
 localhost/dash/test/jasmine/
 ```

## Modify them
Test are defined in the file vizgrimoireSpec.js. The best starting point
is to have a look at the ones for the "upate time", which are very basic.
```
describe("Updated Data: ", function() {
    var max_days_old = 4; // Change it to your project expected update time
    var now = new Date();
    var day_mseconds = 60*60*24*1000;

    function isDSUpdated(ds_name) {
        if(isDSEnabled(ds_name) == false ) return true;
        var update = null;
        $.each(data_sources, function(index, DS) {
            if (DS.getName() === ds_name) {
                update = DS.getGlobalData()['last_date'];
                return false;
            }
        });
        var update_time = new Date(update+"T00:00:00.000Z");
        var days_old = parseInt(
            (now.getTime()-update_time.getTime())/(day_mseconds),null);
            expect(days_old).toBeLessThan(max_days_old+1, ds_name + " data is not updated.");
    }

    it("Data Sources are not updated", function() {
        $.each(data_sources, function(index, DS) {
            isDSUpdated(DS.getName());
        });
    });
});
```

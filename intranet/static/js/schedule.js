$(document).ready(function() {

    function scheduleBind() {
        $(".schedule-outer .schedule-left").click(function(event) {
            event.preventDefault();
            scheduleView(-1);
        });

        $(".schedule-outer .schedule-right").click(function(event) {
            event.preventDefault();
            scheduleView(1);
        });
    };

    function genOrigSearch() {        
        var qs = location.search.substring(1);
        var osearch = "";
        var searchparts = qs.split("&");
        for (var i in searchparts) {
            console.debug(searchparts[i]);
            if (searchparts[i].length > 0 && searchparts[i].substring(0, 5) !== "date=") {
                osearch += searchparts[i] + "&";
            }
        }
        return osearch;
    };

    window.osearch = genOrigSearch();
    console.info("osearch:", window.osearch);

    function scheduleView(reldate) {
        $sch = $(".schedule");
        var endpoint = $sch.attr("data-endpoint");
        var prev = $sch.attr("data-prev-date");
        var next = $sch.attr("data-next-date")
        if (reldate === 1) {
            date = next;
        } else if (reldate === -1) {
            date = prev;
        } else {
            date = reldate;
        }

        if (history.pushState) {
            var url = "?"+window.osearch+"date="+date;
            console.debug(url);
            history.pushState(null, null, url);
        }

        $.get(endpoint, {"date": date, "no_outer": true}, function(d) {
            $(".schedule-outer").html(d);
            scheduleBind();
        });
    };

    scheduleBind(); 
});

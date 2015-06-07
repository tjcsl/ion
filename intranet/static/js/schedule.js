$(document).ready(function() {

    scheduleBind = function() {
        $(".schedule .schedule-left").click(function() {
            event.preventDefault();
            scheduleView(-1);
        });

        $(".schedule .schedule-right").click(function() {
            event.preventDefault();
            scheduleView(1);
        });
    }
    window.osearch = null;
    scheduleView = function(reldate) {
        $sch = $(".schedule");
        var endpoint = $sch.attr("data-endpoint");
        var prev = $sch.attr("data-prev-date");
        var next = $sch.attr("data-next-date")
        if(reldate == 1) date = next;
        else if(reldate == -1) date = prev;
        else date = reldate;

        if(history.pushState) {
            if(window.osearch == null) {
                qs = location.search.substring(1);
                osearch = "";
                for(i in searchparts=qs.split("&")) {
                    console.debug(searchparts[i])
                    if(searchparts[i].length > 0 && searchparts[i].substring(0, 5) != "date=") {
                        osearch += searchparts[i] + "&";
                    }
                }
                window.osearch = osearch;
                console.info("osearch:", window.osearch)
            }
            var url = "?"+window.osearch+"date="+date
            console.debug(url);
            history.pushState(null, null, url);
        }

        $.get(endpoint, {"date": date}, function(d) {
            $(".schedule-outer").html(d);
            scheduleBind();
        });
    }

    $(".logo").click(function() {
        location.href = '';
    })

    scheduleBind(); 
});
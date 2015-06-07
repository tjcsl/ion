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

    scheduleView = function(reldate) {
        $sch = $(".schedule");
        var endpoint = $sch.attr("data-endpoint");
        var prev = $sch.attr("data-prev-date");
        var next = $sch.attr("data-next-date")
        if(reldate == 1) date = next;
        else if(reldate == -1) date = prev;
        else date = reldate;

        if(window.history.pushState) window.history.pushState(null, null, "?date="+date);

        $.get(endpoint, {"date": date}, function(d) {
            $(".schedule-outer").html(d);
            scheduleBind();
        });
    }

    scheduleBind(); 
});
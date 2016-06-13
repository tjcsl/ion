/* global $ */
$(function() {
    $(".eighth-widget .block-header").click(function() {
        var link = $("a", $(this));
        if (link.length > 0) location.href = link.attr("href");
    });

    $(".sponsor-widget .block-header").click(function() {
        var link = $("a", $(this));
        if (link.length > 0) location.href = link.attr("href");
    });

    sponsor_schedule_jump = function(date) {
        var endpoint = $(".sponsor-widget").attr("data-endpoint");
        console.info("Sponsor schedule jump to", date);

        $.get(endpoint, {
            "date": date
        }, function(d) {
            $(".sponsor-widget-outer").html($(".sponsor-widget", $(d)));
            sponsor_schedule_bind();
        });
    }

    sponsor_schedule_pushstate = function(date) {
        if (typeof window.osearch !== 'undefined' && history.pushState) {
            var nosearch = genOrigSearch("sponsor_date");
            var url = "?" + nosearch + "sponsor_date=" + date;
            console.debug(url);
            history.pushState(null, null, url);
        }
    }

    sponsor_schedule_bind = function() {
        $(".sponsor-widget #eighth-sponsor-left").click(function() {
            var date = $(".sponsor-widget").attr("data-prev-date");
            sponsor_schedule_jump(date);
            sponsor_schedule_pushstate(date);
        });

        $(".sponsor-widget #eighth-sponsor-right").click(function() {
            var date = $(".sponsor-widget").attr("data-next-date");
            sponsor_schedule_jump(date);
            sponsor_schedule_pushstate(date);
        });
    }

    sponsor_schedule_bind();
});
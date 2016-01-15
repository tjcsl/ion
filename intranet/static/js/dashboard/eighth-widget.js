$(document).ready(function() {
    $(".eighth-widget .block-header").click(function() {
        var link = $("a", $(this));
        if(link.length > 0) {
            location.href = link.attr("href");
        }
    });

    $(".sponsor-widget .block-header").click(function() {
        var link = $("a", $(this));
        if(link.length > 0) {
            location.href = link.attr("href");
        }
    });

    sponsor_schedule_jump = function(date) {
        var endpoint = $(".sponsor-widget").attr("data-endpoint");
        console.info("Sponsor schedule jump to "+date);
        $.get(endpoint, {"date": date}, function(d) {
            $(".sponsor-widget-outer").html(d);
            sponsor_schedule_bind();
        });
    }

    sponsor_schedule_bind = function() {
        $(".sponsor-widget #eighth-sponsor-left").click(function() {
            sponsor_schedule_jump($(".sponsor-widget").attr("data-prev-date"));
        });

        $(".sponsor-widget #eighth-sponsor-right").click(function() {
            sponsor_schedule_jump($(".sponsor-widget").attr("data-next-date"));
        });
    }

    sponsor_schedule_bind();
});

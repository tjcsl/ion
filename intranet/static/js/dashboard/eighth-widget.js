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

    $(".sponsor-widget #eighth-sponsor-left").click(function() {
        console.log("sponsor left");
    });

    $(".sponsor-widget #eighth-sponsor-right").click(function() {
        console.log("sponsor right");
    });
});

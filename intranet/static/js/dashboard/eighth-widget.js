$(document).ready(function() {
    $(".eighth-widget .block-header").click(function() {
        var link = $("a.block-signup-change", $(this));
        if(link.length > 0) {
            location.href = link.attr("href");
        }
    });

    $(".sponsor-widget .block-header").click(function() {
        var link = $("a.block-attendance-take", $(this));
        if(link.length > 0) {
            location.href = link.attr("href");
        }
    });
});
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
});

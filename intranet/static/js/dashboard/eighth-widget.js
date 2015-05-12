$(document).ready(function() {
    $(".eighth-widget .block-header").click(function() {
        console.log($("a.block-signup-change", $(this)));
        location.href = $("a.block-signup-change", $(this)).attr("href");
    });

    $(".attendance-widget .block-header").click(function() {
        console.log($("a.block-attendance-take", $(this)));
        location.href = $("a.block-attendance-take", $(this)).attr("href");
    });
});
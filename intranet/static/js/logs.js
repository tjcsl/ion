$(function() {
    $("tr.shade:even").css("background-color", "#e7e7e7");
    $(".raw-json-header, .iframe-container-header").click(function () {
        $(this).next().slideToggle("fast");
        $(this.children[1]).toggleClass("fa-angle-up fa-angle-down");
    });
});

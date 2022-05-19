$(function() {
    $(".attend-button").click(function() {
        var eventid = $(this).attr("data-form-attend");
        $("form[data-form-attend=" + eventid + "]").submit();
    });
    $(".no-attend-button").click(function() {
        var eventid = $(this).attr("data-form-no-attend");
        $("form[data-form-no-attend=" + eventid + "]").submit();
    });
});

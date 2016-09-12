/* global $ */
$(function() {
    var $memb = $("#member_search");
    var $inp = $memb.find("input[name='search']");
    var $clear = $memb.find("a#clear");
    var $search_stu = $memb.find("#search_students");
    $search_stu.click(function() {
        var noparam = window.location.href.split("?")[0];
        window.location = noparam + "?q=" + encodeURIComponent($inp.val());
    });
    $inp.on('keydown', function(event) {
        if(event.which == 13) {
            $search_stu.click();
        }
    });

    // Error prone
    var dec = decodeURIComponent(window.location.href.split("?q=")[1]);
    if(dec != "undefined") { $inp.val(dec); }
    $clear.click(function() {
        window.location = window.location.href.split("?")[0];
    });
});

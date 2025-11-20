/* global $ */
$(function() {
    var $memb = $("#member_search");
    var $inp = $memb.find("input[name='search']");
    var $clear = $memb.find("a#clear");
    var $searchStu = $memb.find("#search_students");
    $searchStu.click(function() {
        var noparam = window.location.href.split("?")[0];
        window.location = noparam + "?q=" + encodeURIComponent($inp.val());
    });
    $inp.on("keydown", function(event) {
        if(event.which === 13) {
            $searchStu.click();
        }
    });

    // Error prone
    var dec = window.location.href.split("?q=")[1];
    if(dec) { $inp.val(decodeURIComponent(dec)); }
    $clear.click(function() {
        window.location = window.location.href.split("?")[0];
    });
});

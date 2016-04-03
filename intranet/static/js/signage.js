/* global $ */

$(document).ready(function() {
    var clicked = false, clickY;
    var updateScrollPos = function(e) {
        $("#activity-list").scrollTop($("#activity-list").scrollTop() + (clickY - e.pageY));
    }
    $(document).on({
        'mousemove': function(e) {
            clicked && updateScrollPos(e);
            clickY = e.pageY;
        },
        'mousedown': function(e) {
            clicked = true;
            clickY = e.pageY;
        },
        'mouseup': function() {
            clicked = false;
            $('html').css('cursor', 'auto');
        }
    });
});

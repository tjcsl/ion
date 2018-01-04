/* global $ */
$(function() {
    $('.dash-warning').click(function (e) {
        $(this).toggleClass('collapsed');
    });
    $('.widget.extra-widgets-show').click(function() {
        $('body').addClass('show-extra-widgets');
    });
});

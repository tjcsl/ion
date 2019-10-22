/* global $ */
$(function() {
    $('.dash-warning').click(function (e) {
        $(this).toggleClass('collapsed');
    });
    $('.widget.extra-widgets-show').click(function() {
        $('body').addClass('show-extra-widgets');
    });
    $(".new-feature-close").click(function(e) {
        $(e.target).closest(".new-feature").hide("slow");
    });
});

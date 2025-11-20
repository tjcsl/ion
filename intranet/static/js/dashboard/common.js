/* global $ */
$(function() {
    $('.widget.extra-widgets-show').click(function() {
        $('body').addClass('show-extra-widgets');
    });
    $(".new-feature-close").click(function(e) {
        $(e.target).closest(".new-feature").hide("slow");
    });
});

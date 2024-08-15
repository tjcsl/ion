/* global $ */
$(function() {
    $('.widget.extra-widgets-show').on("click", function() {
        $('body').addClass('show-extra-widgets');
    });

    $(".new-feature-close").on("click", function(e) {
        $(e.target).closest(".new-feature").hide("slow");
    });

    $("body").on("keydown", function(e) {
        if(e.keyCode === 9) {
            e.preventDefault();
        }
        if(!$(".dashboard-textinput").is(":focus")) {
            $("#searchbox").focus();
        }
    });
});

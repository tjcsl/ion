/* Common JS */

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

$.ajaxSetup({
    crossDomain: false,
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type)) {
            xhr.setRequestHeader("X-CSRFToken", $.cookie("csrftoken"));
        }
    }
});




// UI Stuff
function initUIElementBehavior () {
    // Call this function whenever relevant UI elements are dynamically added to the page
    $("button, .button, input[type='button'], input[type='submit'], input[type='reset']").mouseup(function() {
        $(this).blur();
    });
}

$(function() {
    initUIElementBehavior()

    $(".nav a").click(function(event) {
        if (event.metaKey) return;

        $(".nav .selected").removeClass("selected");
        $(this).parent().addClass("selected");
    });

    $(".header h1").click(function() {
        if (event.metaKey) return;

        $(".nav .selected").removeClass("selected");
        $(".nav li").slice(0,1).addClass("selected");
    });


    /* Fix submit button bug with Selectize.js where
     * form will not submit if the enter button is pressed
     * while a form field is selected. */
/*
    $(".selectize-control").each(function() {
        $(this).parent().bind("keypress", function() {

        });
    });*/

});

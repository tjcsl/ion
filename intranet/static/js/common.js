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
$(function() {
    $("button, .button, input[type='button'], input[type='submit'], input[type='reset']").mouseup(function() {
        $(this).blur();
    })

    $("input.datepicker").datepicker();
});

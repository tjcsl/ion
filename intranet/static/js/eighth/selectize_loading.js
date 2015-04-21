$(function() {
    // It should be possible to do $(...).selectize(), but this seems to be a bug in Selectize.js
    $("select[multiple=multiple]").each(function(i, el){$(el).selectize({
        plugins: ["remove_button"],
    })});
    $("select[multiple!=multiple]").each(function(i, el){$(el).selectize({})})
    $(".selectize-loading").remove()
    $("input.datepicker, input[name=date]").datepicker();


    // Set up dashboard links dependent on the status of <select> inputs
    $(".dynamic-link").each(function() {
        var $anchor = $(this);
        var $select = $("#" + $anchor.data("select"));
        var hrefPattern = $anchor.data("href-pattern");

        var update = function(e) {
            if ($select.val().length) {
                var href = hrefPattern.replace(window.urlIDPlaceholder, $select.val());
                $anchor.attr("href", href);
            } else {
                $anchor.removeAttr("href")
            }
        }

        $select.on("change", update);
        update();
    });
})

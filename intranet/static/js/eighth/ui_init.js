$(function() {
    // It should be possible to do $(...).selectize(), but this seems to be a bug in Selectize.js
    $("select[multiple=multiple]").not(".remote-source").each(function(i, el){$(el).selectize({
        plugins: ["remove_button"],
    })});
    $("select[multiple!=multiple]").not(".remote-source").each(function(i, el){$(el).selectize({})})

    $("select.remote-rooms").each(function(i, el){$(el).selectize({
        plugins: ["remove_button"],
        valueField: "id",
        labelField: "description",
        searchField: "description",
        load: function(query, callback) {
            callback(window.all_rooms);
        }
    })});

    $("select.remote-sponsors").each(function(i, el){$(el).selectize({
        plugins: ["remove_button"],
        valueField: "id",
        labelField: "full_name",
        searchField: "full_name",
        load: function(query, callback) {
            callback(window.all_sponsors);
        }
    })});

    $(".selectize-loading").remove();

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

/* global $ */
$(function() {
    selectizeIDScore = function(search) {
        var ths = $(this)[0];
        var score = this.getScoreFunction(search);
        return function(item) {
            return (parseInt(item.value) === parseInt(ths.lastQuery)) ? 10000 : score(item);
        };
    };

    $("select#activity-select").each(function(i, el) {
        $(el).selectize({
            score: selectizeIDScore,
            labelField: 'data-name',
            searchField: ['data-name'],
            maxOptions: 99999
        });
    });

    $("select#block-select").each(function(i, el) {
        $(el).selectize({
            score: selectizeIDScore,
            maxOptions: 99999
        });
    });

    // It should be possible to do $(...).selectize(), but this seems to be a bug in Selectize.js
    $("select[multiple=multiple]").not(".remote-source").each(function(i, el) {
        $(el).selectize({
            plugins: ["remove_button"],
            maxOptions: 99999
        });
    });

    $("select[multiple!=multiple]").not(".remote-source").each(function(i, el) {
        $(el).selectize({
            maxOptions: 99999
        });
    });

    $("select[multiple='']").not(".remote-source").each(function(i, el) {
        $(el).selectize({
            maxOptions: 99999
        });
    });

    var safeFieldRenderer = function(field) {
        return function(data, escape) {
            return "<div>" + data[field] + "</div>";
        }
    }

    $("select.remote-rooms").each(function(i, el) {
        $(el).selectize({
            plugins: ["remove_button"],
            valueField: "id",
            labelField: "description",
            searchField: "description",
            sortField: "description",
            options: window.all_rooms,
            load: function(query, callback) {
                callback(window.all_rooms);
            }
        });
    });

    $("select.remote-sponsors").each(function(i, el) {
        $(el).selectize({
            plugins: ["remove_button"],
            valueField: "id",
            labelField: "full_name",
            searchField: "full_name",
            sortField: "full_name",
            options: window.all_sponsors,
            load: function(query, callback) {
                callback(window.all_sponsors);
            },
            render: {
                item: safeFieldRenderer("full_name"),
                option: safeFieldRenderer("full_name")
            }
        });
    });

    // scroll to top on key down
    $(".selectize-input > input").on("keydown", function() {
        $(".selectize-dropdown-content", $(this).parent()).scrollTo();
    });

    $(".selectize-loading").remove();

    $("input.datepicker, input[name=date]").datepicker({
        dateFormat: 'yy-mm-dd'
    });


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
});

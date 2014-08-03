$(function() {
    $("select").selectize({});
    $("input.datepicker").datepicker();


    $(".dynamic-link").each(function() {
        var $anchor = $(this);
        var $select = $("#" + $anchor.data("select"));
        var hrefPattern = $anchor.data("href-pattern");

        var update = function(e) {
            var href = hrefPattern.replace(window.urlIDPlaceholder, $select.val());
            $anchor.attr("href", href);
        }

        $select.on("change", update);
        update();
    });

});

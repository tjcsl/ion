$(function() {
    $("select").selectize({});
    $("input.datepicker, input[name=date]").datepicker();


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


    var getParams = function(url) {
        var params = {};

        if (url.indexOf("?") < 0)
            return params;

        var paramStrings = url.split("?").pop().split("&");
        for (var p=0; p < paramStrings.length; ++p) {
            var paramString = paramStrings[p];
            if (paramString.indexOf("=") < 0) {
                params[paramString] = "";
            } else {
                var parts = paramString.split("=");
                params[parts[0]] = parts[1];
            }
        }

        return params;
    };

    var updateParam = function(url, key, value) {
        var params = getParams(url);
        params[key] = value;

        return url.split("?")[0] + "?" + $.param(params);
    }


    $(".schedule-activity-select")[0].selectize.setValue(-1);
    $(".schedule-activity-select").on("change", function() {
        var url = updateParam(document.URL, "activity", $(this).val());
        location.href = url;
    })

});

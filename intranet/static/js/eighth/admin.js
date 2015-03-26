$(function() {
    $("select[multiple=multiple]").selectize({
        plugins: ["remove_button"],
    });
    $("select[multiple!=multiple]").selectize({});
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


    // Utility functions for manipulating GET parameters
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

    $("select.url-param-selector").each(function(index, element) {
        if (!($(element).data("param") in getParams(document.URL))) {
            element.selectize.setValue(-1);
        }
    });

    $("select.url-param-selector").on("change", function() {
        var url = updateParam(document.URL, $(this).data("param"), $(this).val());
        location.href = url;
    })


    // Set up checkboxes on activity scheduling page
    var $selectAllBlocksCheckbox = $(".schedule-activity-grid thead input[type='checkbox']")
    var $blockCheckboxes = $(".schedule-activity-grid tbody input[type='checkbox']");

    var updateSelectAllCheckbox = function() {
        var numChecked = $blockCheckboxes.filter(":checked").length;
        if (numChecked == $blockCheckboxes.length) {
            $selectAllBlocksCheckbox.prop("checked", true);
            $selectAllBlocksCheckbox.prop("indeterminate", false);
        } else if (numChecked == 0) {
            $selectAllBlocksCheckbox.prop("checked", false);
            $selectAllBlocksCheckbox.prop("indeterminate", false);
        } else {
            $selectAllBlocksCheckbox.prop("checked", false);
            $selectAllBlocksCheckbox.prop("indeterminate", true);
        }
    }

    var updateBlockCheckboxes = function() {
        $blockCheckboxes.prop("checked", $(this).prop("checked"));
    }

    $selectAllBlocksCheckbox.click(updateBlockCheckboxes);
    $blockCheckboxes.click(updateSelectAllCheckbox);
    updateSelectAllCheckbox();

    // Set up select blocks popover
    $(".select-blocks-popover-toggle").click(function() {
        var $popover = $(".select-blocks-popover");
        var $toggle = $(".select-blocks-popover-toggle");

        $popover.toggleClass("closed");

        if ($popover.hasClass("closed")) {
            $toggle.html("Select All <i class=\"fa fa-caret-down\"></i>")
        } else {
           $toggle.html("Select All <i class=\"fa fa-caret-up\"></i>")
        }
    });

    // Returns a function that filters rows based on whether
    // they represent a block of the given type
    var blockTypeRowFilter = function(blockType) {
        return function(index, element) {
            var blockName = $(element).children(".block-name").text();
            return blockName.indexOf(blockType) == 0;
        };
    };

    $(".select-blocks-popover a.block-type").click(function() {
        var blockType = $(this).text();

        var blockTypeFilter = blockTypeRowFilter(blockType);
        $("tr.form-row").each(function() {
            var $blocksOfType = $(this).filter(blockTypeFilter);
            $blocksOfType.find("input[type='checkbox']").prop("checked", true);
        })

        updateSelectAllCheckbox();
    });

    // Disable *_allowed form elements if Restricted isn't checked
    var updateRestrictedFormFields = function() {
        var restricted = $("#id_restricted").prop("checked");
        $("#id_restricted").parents("tr").nextAll().slice(0, -1).each(function(index, tr) {
            $(tr).find("input").attr("disabled", !restricted);
            $(tr).find("select").each(function(index, select) {
                if (restricted) {
                    select.selectize.enable();
                } else {
                    select.selectize.disable();
                }
            });
        });

    }

    $("#id_restricted").click(updateRestrictedFormFields);
    updateRestrictedFormFields()

    $("#only-show-overbooked").click(function() {
        $("tr.underbooked").toggle();
    })

});

/* global $ */
$(function() {
    // Utility functions for manipulating GET parameters
    var getParams = function(url) {
        var params = {};

        if (url.indexOf("?") < 0)
            return params;

        var paramStrings = url.split("?").pop().split("&");
        for (var p = 0; p < paramStrings.length; ++p) {
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
        var val = $(this).val();
        console.debug("param-selector value:", val);

        if (val) {
            var url = updateParam(document.URL, $(this).data("param"), val);
            location.href = url;
        }
    });


    // Set up checkboxes on activity scheduling and other pages
    var $selectAllBlocksCheckbox = $(".checkboxes-grid thead input[type='checkbox']");
    var $blockCheckboxes = $(".checkboxes-grid tbody td.block-checkbox input[type='checkbox']");

    var updateSelectAllCheckbox = function() {
        var numChecked = $blockCheckboxes.filter(":checked").length;

        if (numChecked === $blockCheckboxes.length) {
            $selectAllBlocksCheckbox.prop("checked", true);
            $selectAllBlocksCheckbox.prop("indeterminate", false);
        } else if (numChecked === 0) {
            $selectAllBlocksCheckbox.prop("checked", false);
            $selectAllBlocksCheckbox.prop("indeterminate", false);
        } else {
            $selectAllBlocksCheckbox.prop("checked", false);
            $selectAllBlocksCheckbox.prop("indeterminate", true);
        }
    }

    var updateBlockCheckboxes = function() {
        var chk = $(this).prop("checked");
        $blockCheckboxes.prop("checked", chk);

        try {
            if (chk) {
                $blockCheckboxes.parent().parent().removeClass("hidden");
                $blockCheckboxes.parent().parent().data("hidden", false);
            } else {
                $blockCheckboxes.parent().parent().addClass("hidden");
                $blockCheckboxes.parent().parent().data("hidden", true);
            }
        } catch (e) {}
    }

    $selectAllBlocksCheckbox.click(updateBlockCheckboxes);
    $blockCheckboxes.click(updateSelectAllCheckbox);
    updateSelectAllCheckbox();

    // Set up select blocks popover
    $(".select-blocks-popover-toggle").click(function() {
        var $popover = $(".select-blocks-popover"),
            $toggle = $(".select-blocks-popover-toggle");

        $popover.toggleClass("closed");

        if ($popover.hasClass("closed")) {
            $toggle.html("Select All <i class=\"fas fa-caret-down\"></i>");
        } else {
            $toggle.html("Select All <i class=\"fas fa-caret-up\"></i>");
        }
    });

    // Returns a function that filters rows based on whether
    // they represent a block of the given type
    var blockTypeRowFilter = function(blockType) {
        return function(index, element) {
            var blockName = $(element).children(".block-name").text();
            return blockName.indexOf(blockType) !== -1;
        };
    };

    $(".select-blocks-popover a.block-type").click(function() {
        var blockType = $(this).text();

        var blockTypeFilter = blockTypeRowFilter(blockType);
        $("tr.form-row").each(function() {
            var $blocksOfType = $(this).filter(blockTypeFilter);
            var $checkboxes = $blocksOfType.find("input[type='checkbox']");

            // Ignore special and unschedule checkbox
            $checkboxes.each(function() {
                if (!$(this).is(".special, .administrative, .restricted, .sticky, .unschedule, .both_blocks")) {
                    $(this).prop("checked", true);
                }
            });

            $blocksOfType.removeClass("hidden");
        });

        updateSelectAllCheckbox();
    });

    // Disable *_allowed form elements if Restricted isn't checked
    var updateRestrictedFormFields = function() {
        var restricted = $("#id_restricted").prop("checked");
        $("#id_restricted").parents("tr").nextAll().slice(0, -1).each(function(index, tr) {
            $(tr).find("input").attr("readonly", !restricted);
            $(tr).find("select").each(function(index, select) {
                if (restricted) {
                    select.selectize.enable();
                } else {
                    select.selectize.disable();
                }
            }).attr('disabled', false);
        });

        // Blacklist should be always enabled
        $("#id_users_blacklisted").parent("td").find("input").attr("readonly", false);
        var select = $("#id_users_blacklisted").parent("td").find("select")[0].selectize.enable();
    }

    $("#id_restricted").click(updateRestrictedFormFields);

    if ($("#id_restricted").length > 0) {
        updateRestrictedFormFields();
    }

    $("#only-show-overbooked").click(function() {
        $("tr.underbooked").toggle();
    });

    $("#hide-administrative").click(function() {
        $("tr.administrative").toggle();
    });
});

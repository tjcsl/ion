/* global $ */
$(function() {
    //$("select").selectize({});
    $("input.datepicker, input[name=date]").datepicker();

    // Set up checkboxes on attendance pages
    var $selectAllMembersCheckbox = $(".take-attendance-roster thead input[type='checkbox']")
    var $membersCheckboxes = $(".take-attendance-roster tbody input[type='checkbox']");

    var updateSelectAllCheckbox = function() {
        var numChecked = $membersCheckboxes.filter(":checked").length;
        if (numChecked === $membersCheckboxes.length) {
            $selectAllMembersCheckbox.prop("checked", true);
            $selectAllMembersCheckbox.prop("indeterminate", false);
        } else if (numChecked === 0) {
            $selectAllMembersCheckbox.prop("checked", false);
            $selectAllMembersCheckbox.prop("indeterminate", false);
        } else {
            $selectAllMembersCheckbox.prop("checked", false);
            $selectAllMembersCheckbox.prop("indeterminate", true);
        }
    }

    var updateBlockCheckboxes = function() {
        $membersCheckboxes.prop("checked", $(this).prop("checked"));
    }

    $selectAllMembersCheckbox.click(updateBlockCheckboxes);
    $membersCheckboxes.click(updateSelectAllCheckbox);
    updateSelectAllCheckbox();

    // Set up accept pass links
    $(".pass-form-submit-link").click(function() {
        var form = document.forms[$(this).data("form")];
        form.status.value = $(this).data("status");

        form.submit();
    })
});
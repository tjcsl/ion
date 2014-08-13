$(function() {
    $("select").selectize({});
    $("input.datepicker, input[name=date]").datepicker();

    // Set up checkboxes on attendance pages
    // var $selectAllBlocksCheckbox = $(".schedule-activity-grid thead input[type='checkbox']")
    // var $blockCheckboxes = $(".schedule-activity-grid tbody input[type='checkbox']");

    // var updateSelectAllCheckbox = function() {
    //     var numChecked = $blockCheckboxes.filter(":checked").length;
    //     if (numChecked == $blockCheckboxes.length) {
    //         $selectAllBlocksCheckbox.prop("checked", true);
    //         $selectAllBlocksCheckbox.prop("indeterminate", false);
    //     } else if (numChecked == 0) {
    //         $selectAllBlocksCheckbox.prop("checked", false);
    //         $selectAllBlocksCheckbox.prop("indeterminate", false);
    //     } else {
    //         $selectAllBlocksCheckbox.prop("checked", false);
    //         $selectAllBlocksCheckbox.prop("indeterminate", true);
    //     }
    // }

    // var updateBlockCheckboxes = function() {
    //     $blockCheckboxes.prop("checked", $(this).prop("checked"));
    // }

    // $selectAllBlocksCheckbox.click(updateBlockCheckboxes);
    // $blockCheckboxes.click(updateSelectAllCheckbox);
    // updateSelectAllCheckbox();
});

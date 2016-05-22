/* global $ */
$(function() {
    $(".boardpost-delete-comment").click(function() {
        if (!confirm("Are you sure you want to delete this comment?")) return;
        var dataView = $(this).attr("data-view");
        $.post($(this).attr("data-endpoint"), {"confirm": true}, function(res) {
            location.href = dataView;
        });
    });
})

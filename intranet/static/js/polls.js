var default_question = {
    "pk": null,
    "fields": {
        "question": "",
        "max_choices": 1,
        "type": "STD"
    }
};

$(function() {
    var questionTemplate = _.template($("#question-template").html());

    $("select#id_groups").selectize({
        plugins: ["remove_button"],
        placeholder: "Everyone"
    });
    $("#id_start_time, #id_end_time").datetimepicker({
        lazyInit: true,
        format: "Y-m-d H:i:s"
    });
    poll_questions.sort(function(a, b) {
        return a.fields.num - b.fields.num;
    });
    $.each(poll_questions, function(k, v) {
        $("#questions").append(questionTemplate(v));
    });
    $("#questions .type").selectize();
    $("#add_question").click(function(e) {
        e.preventDefault();
        var new_question = $(questionTemplate(default_question));
        new_question.appendTo("#questions").hide().slideDown("fast");
        new_question.find(".type").selectize();
    });
    $("#questions").on("click", ".question .fa.fa-arrow-up", function(e) {
        var ele = $(this).closest(".question");
        ele.insertBefore(ele.prev());
        e.preventDefault();
    });
    $("#questions").on("click", ".question .fa.fa-arrow-down", function(e) {
        var ele = $(this).closest(".question");
        ele.insertAfter(ele.next());
        e.preventDefault();
    });
    $("#questions").on("click", ".question .fa.fa-times", function(e) {
        $(this).closest(".question").slideUp("fast", function() {
            $(this).remove();
        });
        e.preventDefault();
    });
});

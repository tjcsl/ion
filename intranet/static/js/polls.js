var default_question = {
    "pk": null,
    "fields": {
        "question": "",
        "max_choices": 1,
        "type": "STD"
    }
};

var default_choice = {
    "pk": null,
    "fields": {
        "info": ""
    }
};

$(function() {
    var questionTemplate = _.template($("#question-template").html());
    var choiceTemplate = _.template($("#choice-template").html());

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
    poll_choices.sort(function(a, b) {
        return a.fields.num - b.fields.num;
    });
    $.each(poll_questions, function(k, v) {
        $("#questions").append(questionTemplate(v));
    });
    $.each(poll_choices, function(k, v) {
        $("#questions .question[data-id='" + v.pk + "']").find(".choices").append(choiceTemplate(v));
    });
    $("#questions .type").selectize();
    $("#add_question").click(function(e) {
        e.preventDefault();
        var new_question = $(questionTemplate(default_question));
        new_question.appendTo("#questions").hide().slideDown("fast");
        new_question.find(".type").selectize();
    });
    $("#questions").on("click", ".add_choice", function(e) {
        e.preventDefault();
        var new_choice = $(choiceTemplate(default_choice));
        new_choice.appendTo($(this).closest(".question").find(".choices")).hide().slideDown("fast");
    });
    $("#questions").on("click", ".question > .actions .fa.fa-arrow-up", function(e) {
        var ele = $(this).closest(".question");
        ele.insertBefore(ele.prev());
        e.preventDefault();
    });
    $("#questions").on("click", ".question > .actions .fa.fa-arrow-down", function(e) {
        var ele = $(this).closest(".question");
        ele.insertAfter(ele.next());
        e.preventDefault();
    });
    $("#questions").on("click", ".question .choice .actions .fa.fa-arrow-up", function(e) {
        var ele = $(this).closest(".choice");
        ele.insertBefore(ele.prev());
        e.preventDefault();
    });
    $("#questions").on("click", ".question .choice .actions .fa.fa-arrow-down", function(e) {
        var ele = $(this).closest(".choice");
        ele.insertAfter(ele.next());
        e.preventDefault();
    });
    $("#questions").on("click", ".question > .actions .fa.fa-times", function(e) {
        $(this).closest(".question").slideUp("fast", function() {
            $(this).remove();
        });
        e.preventDefault();
    });
    $("#questions").on("click", ".question .choice .actions .fa.fa-times", function(e) {
        $(this).closest(".choice").slideUp("fast", function() {
            $(this).remove();
        });
        e.preventDefault();
    });
});

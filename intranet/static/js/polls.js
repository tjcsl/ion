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

function addInline(item) {
    CKEDITOR.inline(item, {
        floatSpaceDockedOffsetY: 10,
        autoParagraph: false,
        enterMode: CKEDITOR.ENTER_BR
    });
}

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
        $("#questions .question[data-id='" + v.fields.question + "']").find(".choices").append(choiceTemplate(v));
    });
    $("#questions .type").selectize();
    $("#questions [contenteditable='true']").each(function(k, v) {
        addInline(v);
    });
    $("#poll-form").submit(function() {
        var out = [];
        $("#questions .question").each(function() {
            var q = {
                "question": $(this).find(".text").html(),
                "type": $(this).find(".type").val(),
                "max_choices": $(this).find(".max").val(),
                "choices": []
            };
            if ($(this).attr("data-id")) {
                q["pk"] = $(this).attr("data-id");
            }
            $(this).find(".choices .choice").each(function() {
                var c = {
                    "info": $(this).find(".info").html()
                };
                if ($(this).attr("data-id")) {
                    c["pk"] = $(this).attr("data-id");
                }
                q["choices"].push(c);
            });
            out.push(q);
        });
        $("#id_question_data").val(JSON.stringify(out));
        return true;
    });
    $("#add_question").click(function(e) {
        e.preventDefault();
        var new_question = $(questionTemplate(default_question));
        new_question.appendTo("#questions").hide().slideDown("fast");
        new_question.find(".type").selectize();
        addInline(new_question.find("[contenteditable='true']")[0]);
    });
    $("#questions").on("click", ".add_choice", function(e) {
        e.preventDefault();
        var new_choice = $(choiceTemplate(default_choice));
        new_choice.appendTo($(this).closest(".question").find(".choices")).hide().slideDown("fast");
        addInline(new_choice.find("[contenteditable='true']")[0]);
    });
    $("#questions").on("click", ".question > .actions .fas.fa-arrow-up", function(e) {
        var ele = $(this).closest(".question");
        ele.insertBefore(ele.prev());
        e.preventDefault();
    });
    $("#questions").on("click", ".question > .actions .fas.fa-arrow-down", function(e) {
        var ele = $(this).closest(".question");
        ele.insertAfter(ele.next());
        e.preventDefault();
    });
    $("#questions").on("click", ".question .choice .actions .fas.fa-arrow-up", function(e) {
        var ele = $(this).closest(".choice");
        ele.insertBefore(ele.prev());
        e.preventDefault();
    });
    $("#questions").on("click", ".question .choice .actions .fas.fa-arrow-down", function(e) {
        var ele = $(this).closest(".choice");
        ele.insertAfter(ele.next());
        e.preventDefault();
    });
    $("#questions").on("click", ".question > .actions .fas.fa-times", function(e) {
        $(this).closest(".question").slideUp("fast", function() {
            $(this).remove();
        });
        e.preventDefault();
    });
    $("#questions").on("click", ".question .choice .actions .fas.fa-times", function(e) {
        $(this).closest(".choice").slideUp("fast", function() {
            $(this).remove();
        });
        e.preventDefault();
    });
});

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

    $("#import_from_csv").on("click", async function (e) {
        e.preventDefault();
        $("#csv_input").trigger("click");
    });

    $("#csv_input").on("change", function (e) {
        e.preventDefault();
        let file = $("#csv_input").prop("files")[0];
        let file_reader = new FileReader();
        file_reader.onload = async function (e) {
            // csv should have the following headers
            // name, position, platform, slogan
            let csv_data = $.csv.toArrays(file_reader.result);
            if (csv_data.length === 0) {
                $("#csv_error").text("Empty CSV");
                return;
            }

            let required_labels = ["position", "name", "platform", "slogan"]
            let labels = csv_data[0].map(l => l.toLowerCase());
            if (!required_labels.every(l => labels.includes(l))) {
                let missing_labels = required_labels.filter(l => !labels.includes(l))
                $("#csv_error").text(`Missing required label(s): ${missing_labels.join(", ")}`)
                return;
            }
            $("#csv_error").text("");

            let content = csv_data.slice(1);
            let map = {}; // (position) -> (name, platform, slogan)
            for (let line of content) {
                let position = line[labels.indexOf("position")];
                let name = line[labels.indexOf("name")];
                let platform = line[labels.indexOf("platform")];
                let slogan = line[labels.indexOf("slogan")];

                if (!(position in map)) {
                    map[position] = [];
                }
                map[position].push([name, platform, slogan]);
            }

            let sleep = async () => { await new Promise(resolve => setTimeout(resolve, 0)); };

            for (let [position, choices] of Object.entries(map)) {
                $("#add_question").trigger("click");
                let question_element = $("#questions .question:last-child");
                await sleep();

                // set position, type, and max choices of question
                question_element.find(".text").html(position);
                question_element.find(".type").data('selectize').setValue("RAN");
                question_element.find(".max").val(`${Math.min(choices.length, 3)}`);

                for (let choice of choices) {
                    let [name, platform, slogan] = choice;

                    question_element.find(".add_choice").trigger("click");
                    await sleep();

                    let text_field = question_element.find(".choices .choice:last-child .info");
                    let text = $(`<a href="${platform}">${name} | ${slogan}</a>`)
                    text_field.html(text);
                }
            }
        };
        file_reader.readAsText(file);
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

    $("#add_question").on("click", function(e) {
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

    $("#questions").on("change", "select.type", function(e) {
        e.preventDefault();
        $("select.type").each(function() {
            if($(this).val() === "RAN") {
                $(this).parent().next().next().next().next().show("fast");
            }
            else {
                $(this).parent().next().next().next().next().hide("fast");
            }
        });
    });
});

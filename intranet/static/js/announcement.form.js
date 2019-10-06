/* global $ */
$(function() {
    $("select#id_groups").selectize({
        plugins: ["remove_button"],
        placeholder: "Everyone"
    });

    var reset = $("#id_expiration_date").val() !== "3000-01-01 00:00:00";
    $("#id_expiration_date").datetimepicker({
        lazyInit: true,
        format: "Y-m-d H:i:s"
    });

    // for approval page
    $("select#id_teachers_requested").selectize({
        plugins: ["remove_button"],
        maxItems: 2
    });

    $("form#announcement_form").bind("submit", function (e) {
        if($("#id_notify_email_all").prop("checked")) {
            if(!confirm("This will send an email to ALL users who can see this post. If you have not selected a group, this will email the entire school. Are you sure you want to do this?")) {
                e.preventDefault();
            }
        }

        if($("#id_title").val().match(/\bION\b/) || editor.getData().match(/\bION\b/)) {
            // People frequently write "ION" instead of the correct spelling, "Ion." See https://github.com/tjcsl/ion/issues/805
            Messenger().error('We have detected the use of "ION" in all caps in your announcement. Please correct it to use "Ion", <a href="/docs/terminology" style="color:#7F7FFF">the official name</a>.');
            e.preventDefault();
            return;
        }

        var button = $("button#submit_announcement");
        button.click(function(ev) { ev.preventDefault(); })
        button.append(" <i class=\"fas fa-spinner fa-spin\" aria-hidden=\"true\"></i>");

        if ($("input#id_title").val() === "") {
            button.prop("disabled", false);
        }
    });

    // name of <textarea> is content
    var editor = CKEDITOR.replace("content", {
        width: "600px"
    });
    var end_index = 0;

    editor.on("instanceReady", function () {
        // TODO: Don't duplicate this function. Bad!
        var text = editor.getData();
        dates = chrono.parse(text)
            .sort(function (a, b) {
                var a_date = a.end ? a.end.date() : a.start.date();
                var b_date = b.end ? b.end.date() : b.start.date();
                return b_date.getTime() - a_date.getTime();
            })
            .filter(function (val, ind, ary) {
                if (ind) {
                    var a_date = val.end ? val.end.date() : val.start.date();
                    var b_date = ary[ind - 1].end ? ary[ind - 1].end.date() : ary[ind - 1].start.date();
                    return !ind || a_date.getTime() != b_date.getTime();
                } else {
                    return true;
                }
            });
        $(".exp-list").empty();
        if (dates.length > 0)
            $(".exp-header").css("display", "block");
        else
            $(".exp-header").css("display", "none");
        for (var i = 0; i < dates.length; i++) {
            var use_date = dates[i].end ? dates[i].end.date() : dates[i].start.date();
            $(".exp-list").append(`<li><a class='exp-suggest-item' data-date='${use_date}'>"${dates[i].text}" - ${use_date}</a></li>`);
        }
    });

    editor.on("change", function () {
        // TODO: Optimize by only parsing on new spaces
        var text = editor.getData();
        dates = chrono.parse(text)
            .sort(function (a, b) {
                var a_date = a.end ? a.end.date() : a.start.date();
                var b_date = b.end ? b.end.date() : b.start.date();
                return b_date.getTime() - a_date.getTime();
            })
            .filter(function (val, ind, ary) {
                if (ind) {
                    var a_date = val.end ? val.end.date() : val.start.date();
                    var b_date = ary[ind - 1].end ? ary[ind - 1].end.date() : ary[ind - 1].start.date();
                    return !ind || a_date.getTime() != b_date.getTime();
                } else {
                    return true;
                }
            });
        $(".exp-list").empty();
        if (dates.length > 0)
            $(".exp-header").css("display", "block");
        else
            $(".exp-header").css("display", "none");
        for (var i = 0; i < dates.length; i++) {
            var use_date = dates[i].end ? dates[i].end.date() : dates[i].start.date();
            $(".exp-list").append(`<li><a class='exp-suggest-item' data-date='${use_date}'>"${dates[i].text}" - ${use_date}</a></li>`);
        }
    });
});

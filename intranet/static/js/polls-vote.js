$(function() {
    $(".candidate-info-header, .rank-q-header, .expand-collapse-all").click(function() {
        $(this).next().toggle("fast");
        $(this.children[1]).toggleClass("fa-angle-up fa-angle-down");
    });

    $(".expand-collapse-all").data("expanded", true).click(function() {
        var expanded = $(this).data("expanded");
        var elements = $(".candidate-info-header, .rank-q-header, .expand-collapse-all");
        if (expanded) {
            $(elements).next().show("fast");
            $(elements).children("i").removeClass("fa-angle-down").addClass("fa-angle-up");
        }
        else {
            $(elements).next().hide("fast");
            $(elements).children("i").removeClass("fa-angle-up").addClass("fa-angle-down");
        }
        $(this).data("expanded", !expanded);
        $(this.children[0]).text(!expanded ? "Expand All" : "Collapse All");
    });

    $(".question-clear-action").change(function() {
        let chk = $(this).prop("checked");
        let ul = $(this).parent().parent();

        ul.children().each(function() {
            let li = $("input", $(this));
            if(!li.hasClass("question-clear-action")) {
                li.prop("checked", false);
                li.attr("disabled", chk);
            }
        });
    });

    $("select").on("change", function(e) {
        let name = $(this).attr("name");
        let prev = $(this).data("previous");
        let value = $(this).val();

        $(this).data("previous", value);
        $("select[name=" + name +"]").not(this).find("option[value='" + prev + "'][class='choice-option']").show();
        $("select[name=" + name +"]").not(this).find("option[value='" + value + "'][class='choice-option']").hide();
    });

    $(".candidate-info ul li a").each(function() {
        $(this).text($(this).text().replace("|", "—"));
    });
});
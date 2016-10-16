$(document).ready(function() {
    $.get("https://homecoming.tjhsst.edu/api/", function(data) {
        $("#score-senior").text(data.senior_total);
        $("#score-sophomore").text(data.sophomore_total);
        $("#score-junior").text(data.junior_total);
        $("#score-freshman").text(data.freshman_total);
        giveRibbons();
        $("#hoco-scores").fadeIn();
    });
});
function giveRibbons() {
    var arr = [];
    $("#hoco-scores .box").each(function() {
        var score = parseFloat($(this).find(".score").text());
        arr.push([$(this), score]);
    });
    arr.sort(function(a, b) {
        return b[1] - a[1];
    });
    var place = 0;
    $.each(arr, function(k, v) {
        if (k > 0 && arr[k - 1][1] != v[1]) {
            place += 1;
        }
        if (place == 0) {
            v[0].find(".corner-ribbon").addClass("gold").text("1st");
        }
        else if (place == 1) {
            v[0].find(".corner-ribbon").addClass("silver").text("2nd");
        }
        else if (place == 2) {
            v[0].find(".corner-ribbon").addClass("bronze").text("3rd");
        }
    });
}

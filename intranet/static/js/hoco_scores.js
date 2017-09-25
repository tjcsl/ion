$(document).ready(function() {
    console.log('hello');
    $.get("https://homecoming.tjhsst.edu/api/", function(data) {
        console.log(data.senior_total ? data.senior_total : 0);
        $("#score-senior").text(data.senior_total ? data.senior_total : 0);
        $("#score-sophomore").text(data.sophomore_total ? data.sophomore_total : 0);
        $("#score-junior").text(data.junior_total ? data.junior_total : 0);
        $("#score-freshman").text(data.freshman_total ? data.freshman_total : 0);
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

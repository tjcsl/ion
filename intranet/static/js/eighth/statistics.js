/* global $ */
$(document).ready(function() {
    if (Object.keys(raw_data).length > 0) {
        $("#members-chart").show();
        var canvas = $("#members-chart")[0];
        var parsed_data = [];
        $.each(raw_data, function(k, v) {
            parsed_data.push([Date.parse(k, "YYYY-MM-DD"), v]);
        });
        parsed_data = parsed_data.sort(function(a, b) {
            if (a[0] < b[0]) return -1;
            if (a[0] > b[0]) return 1;
            return 0;
        });
        var data = {
            labels: $.map(parsed_data, function(v) { return v[0]; }),
            datasets: [
                {
                    label: "A Block",
                    backgroundColor: "rgba(151,187,205,0.5)",
                    data: $.map(parsed_data, function(v) { return "A" in v[1] ? v[1]["A"] : 0; })
                },
                {
                    label: "B Block",
                    backgroundColor: "rgba(205,187,151,0.5)",
                    data: $.map(parsed_data, function(v) {  return "B" in v[1] ? v[1]["B"] : 0; })
                }
            ]
        };
        var stepSize = 1;
        if (capacity >= 20) {
            stepSize = 5;
        }
        else if (capacity >= 100) {
            stepSize = 10;
        }
        chart = new Chart(canvas.getContext("2d"), {
            type: "line",
            data: data,
            options: {
                maintainAspectRatio: true,
                responsive: false,
                scales: {
                    yAxes: [{
                        type: "linear",
                        scaleLabel: {
                            display: true,
                            labelString: "Signups"
                        },
                        ticks: {
                            beginAtZero: true,
                            stepSize: stepSize,
                            suggestedMax: capacity
                        }
                    }],
                    xAxes: [{
                        type: "time",
                        time: {
                            tooltipFormat: "MM/DD/YYYY"
                        },
                        scaleLabel: {
                            display: true,
                            labelString: "Dates"
                        }
                    }]
                }
            }
        });
    }
    if ($("#members-table tbody tr").length >= 2) {
        $("#members-table thead").append("<th></th>");
        var max = parseInt($("#members-table tbody tr:first-child td:nth-child(2)").text(), 10);
        $("#members-table tbody tr").each(function() {
            var child = $(this).find("td:nth-child(2)");
            var val = parseInt(child.text(), 10);
            $(this).append("<td><div class='sparkline' style='width:" + Math.round(100 * val / max) + "px'></div></td>");
        });
    }
});

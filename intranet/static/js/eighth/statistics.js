/* global $ */
$(document).ready(function() {
    if (Object.keys(raw_data).length > 0) {
        var chartElement = $("#members-chart");
        chartElement.show();
        var canvas = chartElement[0];
        var parsedData = [];
        $.each(raw_data, function(k, v) {
            parsedData.push([moment(k, "YYYY-MM-DD"), v]);
        });
        parsedData = parsedData.sort(function(a, b) {
            if (a[0] < b[0]) {
                return -1;
            }
            if (a[0] > b[0]) {
                return 1;
            }
            return 0;
        });
        parsedData = {
            labels: $.map(parsedData, function(v) { return v[0]; }),
            datasets: [
                {
                    label: "A Block",
                    backgroundColor: "rgba(151,187,205,0.5)",
                    data: $.map(parsedData, function(v) { return "A" in v[1] ? v[1].A : 0; })
                },
                {
                    label: "B Block",
                    backgroundColor: "rgba(205,187,151,0.5)",
                    data: $.map(parsedData, function(v) { return "B" in v[1] ? v[1].B : 0; })
                }
            ]
        };
        var signupChart = new Chart(canvas.getContext("2d"), {
            type: "line",
            data: parsedData,
            options: {
                maintainAspectRatio: true,
                scales: {
                    yAxes: [{
                        type: "linear",
                        scaleLabel: {
                            display: true,
                            labelString: "Signups"
                        },
                        ticks: {
                            beginAtZero: true,
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
    var tableRows = $("#members-table tbody tr");
    if (tableRows.length >= 2) {
        $("#members-table thead").append("<th></th>");
        var max = parseInt($("#members-table tbody tr:first-child td:nth-child(2)").text(), 10);
        tableRows.each(function() {
            var child = $(this).find("td:nth-child(2)");
            var val = parseInt(child.text(), 10);
            $(this).append("<td><div class='sparkline' style='width:" + Math.round(100 * val / max) + "px'></div></td>");
        });
    }
});

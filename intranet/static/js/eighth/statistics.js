$(document).ready(function() {
    if (raw_data.keys.length > 0) {
        $("#members-chart").show();
        var canvas = $("#members-chart")[0];
        var data = {
            labels: raw_data.keys,
            datasets: [
                {
                    label: "Signups",
                    backgroundColor: "rgba(151,187,205,0.5)",
                    hoverBackgroundColor: "rgba(151,187,205,0.75)",
                    data: raw_data.values
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
                        type: "category",
                        scaleLabel: {
                            display: true,
                            labelString: "Blocks"
                        }
                    }]
                },
                legend: {
                    display: false
                }
            }
        });
    }
    if ($("#members-table tbody tr").length >= 2) {
        $("#members-table thead").append("<th></th>");
        var max = parseInt($("#members-table tbody tr:first-child td:nth-child(2)").text());
        $("#members-table tbody tr").each(function(k, v) {
            var child = $(this).find("td:nth-child(2)");
            var val = parseInt(child.text());
            $(this).append("<td><div class='sparkline' style='width:" + Math.round(100*val/max) + "px'></div></td>");
        });
    }
});

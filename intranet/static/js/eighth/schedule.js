/* global $ */
/* global activitySticky */
$(function() {
    var toggleRow = function(tr) {
        var i = 0;
        var cb = $("input.scheduled[type=checkbox]", tr);
        var checked = cb.prop("checked");
        $("td", tr).each(function() {
            if (i > 1) {
                var t = $(tr);
                if (checked) {
                    //$(this).css("opacity", 1);
                    t.removeClass("hidden");
                    t.data("hidden", false);
                } else {
                    //$(this).css("opacity", 0.7);
                    t.addClass("hidden");
                    t.data("hidden", true);
                }
            }
            i++;
        });
    };

    $(".schedule-activity-grid tbody tr.form-row").each(function() {
        var cb = $("input.scheduled[type=checkbox]", this);
        var checked = cb.prop("checked");
        // var bt = $("td.block-name a", this).text().trim();

        if (!checked) toggleRow($(this));

        $(cb).click(function() {
            toggleRow($(this).parent().parent());
        });
    });

    $("select.remote-rooms").change(function(e) {
        var $select = $(e.target);

        var capacitySum = 0;
        var val = $select.val();
        if (val !== null) {
            val.forEach(function(roomID) {
                var c = all_rooms_lookup[roomID].capacity;
                if (c === -1) c = Infinity;
                capacitySum += c;
            });
        }

        if (capacitySum === Infinity) capacitySum = -1;
        var $capacityInput = $("input.capacity", $select.parent().parent());
        // var defaultActivityCapacity = $capacityInput.data("activity-default-capacity");
        var defaultCapacity = $capacityInput.data("default-capacity");
        $capacityInput.attr("placeholder", capacitySum === 0 ? defaultCapacity : capacitySum);
    });

    window.propagate_direction = "both";
    window.propagate_method = "only_new";

    window.updatePropagateDirection = function(opt) {
        window.propagate_direction = opt;

        var classes = ["fa-arrows-v", "fa-long-arrow-up", "fa-long-arrow-down"];
        if (opt === "both") {
            $(".propagate > i").removeClass(classes[1] + " " + classes[2])
                .addClass(classes[0]);
        } else if (opt === "up") {
            $(".propagate > i").removeClass(classes[0] + " " + classes[2])
                .addClass(classes[1]);
        } else if (opt === "down") {
            $(".propagate > i").removeClass(classes[0] + " " + classes[1])
                .addClass(classes[2]);
        }
    }

    window.updatePropagateMethod = function(opt) {
        window.propagate_method = opt;
    }

    $(".propagate").click(function() {
        var field = $(this).attr("data-field"),
            input = $(this).attr("data-input");
        var el = $("#" + input);

        var rows = $(".schedule-activity-grid tr.form-row");
        var row;
        var currentRow;
        if (window.propagate_direction && window.propagate_direction === "down") {
            currentRow = el.parent().parent();
            rows = [];
            row = currentRow;
            while (row && row.length > 0) {
                row = row.next();
                if (row.hasClass("form-row")) {
                    rows.push(row[0]);
                }
            }
            rows = $(rows);
        }

        if (window.propagate_direction && window.propagate_direction === "up") {
            currentRow = el.parent().parent();
            rows = [];
            row = currentRow;
            while (row && row.length > 0) {
                row = row.prev();
                if (row.hasClass("form-row")) {
                    rows.push(row[0]);
                }
            }
            rows = $(rows);
        }

        if (window.propagate_method && window.propagate_method === "only_new") {
            var new_rows = [];
            for (var i = 0; i < rows.length; i++) {
                var rw = $(rows[i]);
                if (!rw.hasClass("scheduled")) {
                    new_rows.push(rows[i]);
                }
            }
            rows = $(new_rows);
        }

        if (el.hasClass("selectized")) {
            var sel = el[0].selectize;
            var modItems = sel.items;

            rows.each(function() {
                var ntd = $("td[data-field='" + field + "']", $(this));
                var ninp = $("input, select", ntd);
                var nsel = ninp[0].selectize;
                var o_items = nsel.items;
                nsel.setValue(modItems);
            });
        } else {
            var modVal;
            if (el.attr("type") === "checkbox") {
                modVal = el.prop("checked");
                rows.each(function() {
                    var ntd = $("td[data-field='" + field + "']", $(this));
                    var ninp = $("input", ntd);
                    ninp.prop("checked", modVal);
                });
            } else {
                modVal = el.val();
                console.info("New value:", modVal);

                rows.each(function() {
                    var ntd = $("td[data-field='" + field + "']", $(this));
                    var ninp = $("input, select, textarea", ntd);
                    ninp.val(modVal);
                });
            }
        }
    });

    $(".selectized").each(function() {
        var sel = $(this)[0].selectize;
        if (sel) {
            sel.on('item_add', function() {
                sel.close();
            });
        }
    });
    $(".schedule-form input[type='submit']").click(function(e) {
        var activities = "";
        $("tr.form-row:not(.hidden)").each(function(i, el) {
            var inputWrapper = $("td[data-field='sponsors'] .selectize-input", el);
            if (!inputWrapper.hasClass("has-items") && inputWrapper.find("input").attr('placeholder') == "No default") {
                if(!$("input[type='checkbox'].unschedule", el).prop("checked")) {
                    activities += "\n    " + $(".block-name a.ui-link", el).text().trim();
                }
            }
        });
        if (activities !== "" && !confirm("Are you sure you want to add the following activities without a sponsor?\n" + activities)) {
            e.preventDefault();
        }
        var stickyCancel = "";
        $("tr.form-row.scheduled").each(function() {
            var scheduledField = $(this).find("td[data-field='scheduled'] input[type='checkbox']");
            var stickyField = $(this).find("td[data-field='sticky'] input[type='checkbox']");
            if (!scheduledField.prop("checked")) {
                if(stickyField.prop("checked") || activitySticky) {
                    stickyCancel += "\n    " + $(this).find(".block-name a.ui-link").text().trim();
                }
            }
        });
        if (stickyCancel !== "" && !confirm("Cancelling the following 'sticky' activities will allow students to switch out of them. Are you sure?\n" + stickyCancel)){
            e.preventDefault();
        }
    });
});

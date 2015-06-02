$(function() {
    toggleRow = function(tr) {
        var i = 0;
        var cb = $("input[type=checkbox]", tr);
        var checked = cb.prop("checked");
        $("td", tr).each(function() {
            if(i > 1) {
                if(checked) {
                    //$(this).css("opacity", 1);
                    $(tr).removeClass("hidden");
                    $(tr).data("hidden", false);
                } else {
                    //$(this).css("opacity", 0.7);
                    $(tr).addClass("hidden");
                    $(tr).data("hidden", true);
                }
            }
            i++;
        });
    }
    $(".schedule-activity-grid tbody tr.form-row").each(function() {
        var cb = $("input[type=checkbox]", this);
        var checked = cb.prop("checked");
        var bt = $("td.block-name a", this).text().trim();
        if(!checked) {
            toggleRow($(this));
        }
        $(cb).click(function() {
            toggleRow($(this).parent().parent());
        });
    });

    $("select.remote-rooms").change(function(e) {
        var $select = $(e.target);

        var capacitySum = 0;
        var val = $select.val();
        if(val !== null) {
            val.forEach(function(roomID) {
                var c = all_rooms_lookup[roomID].capacity;
                if (c == -1) c = Infinity;
                capacitySum += c;
            });
        }

        if (capacitySum == Infinity) capacitySum = -1;
        var $capacityInput = $("input.capacity", $select.parent().parent());
        var defaultCapacity = $capacityInput.data("default-capacity");
        $capacityInput.attr("placeholder", capacitySum == 0 ? defaultCapacity : capacitySum);
    });

    window.propagate_direction = "both";
    window.updatePropagate = function(opt) {
        window.propagate_direction = opt;
        console.info("New propagate direction:", opt)

        var classes = ["fa-arrows-v", "fa-long-arrow-up", "fa-long-arrow-down"];
        if(opt == "both") {
            $(".propagate > i").removeClass(classes[1]).removeClass(classes[2])
                               .addClass(classes[0]);
        } else if(opt == "up") {
            $(".propagate > i").removeClass(classes[0]).removeClass(classes[2])
                               .addClass(classes[1]);
        } else if(opt == "down") {
            $(".propagate > i").removeClass(classes[0]).removeClass(classes[1])
                               .addClass(classes[2]);
        }
    }

    $(".propagate").click(function() {
        var field = $(this).attr("data-field");
        var input = $(this).attr("data-input");
        var el = $("#" + input);
        console.debug("Propagate", field, input, el.length > 0);

        var rows = $(".schedule-activity-grid tr.form-row");
        if(window.propagate_direction && window.propagate_direction == "down") {
            var current_row = el.parent().parent();
            var rows = [];
            var row = current_row;
            while(row && row.length > 0) {
                row = row.next();
                if(row.hasClass("form-row")) {
                    rows.push(row[0]);
                }
            }
            rows = $(rows);
        }

        if(window.propagate_direction && window.propagate_direction == "up") {
            var current_row = el.parent().parent();
            var rows = [];
            var row = current_row;
            while(row && row.length > 0) {
                row = row.prev();
                if(row.hasClass("form-row")) {
                    rows.push(row[0]);
                }
            }
            rows = $(rows);
        }

        if(el.hasClass("selectized")) {
            console.info("Selectized element");
            var sel = el[0].selectize;
            mod_items = sel.items;
            console.info("New value:", mod_items);

            rows.each(function() {
                var ntd = $("td[data-field='" + field + "']", $(this));
                var ninp = $("input, select", ntd);
                var nsel = ninp[0].selectize;
                var o_items = nsel.items;
                nsel.setValue(mod_items);
                console.debug("items: ", o_items, "=>", nsel.items);

            });
        } else {
            mod_val = el.val();
            console.info("New value:", mod_val);

            rows.each(function() {
                var ntd = $("td[data-field='" + field + "']", $(this));
                var ninp = $("input, select, textarea", ntd);

                ninp.val(mod_val);
            });

        }

    })
});
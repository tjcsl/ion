/* global $ */
$(function() {
    $(".select-all").change(function() {
        var chk = $(this).prop("checked");
        var name = $(this).attr("data-name");
        console.debug(chk, name);

        $(".user-item").each(function() {
            if ($(this).attr("name") === name) {
                $(this).prop("checked", chk);
            }
        });
    });

    $(".user-item").change(function() {
        var chk = $(this).prop("checked");
        var name = $(this).attr("name");
        var num_checked = 0;
        var $checkboxes = $(".user-item[name='" + name + "']");

        $checkboxes.each(function() {
            if ($(this).prop("checked")) {
                num_checked++;
            }
        });

        $e = $(".select-all[data-name='" + name + "']");
        if (num_checked === 0) {
            $e.prop("checked", false);
            $e.prop("indeterminate", false);
        } else if (num_checked === $checkboxes.length) {
            $e.prop("checked", true);
            $e.prop("indeterminate", false);
        } else {
            $e.prop("checked", false);
            $e.prop("indeterminate", true);
        }
    });

    distribute = function() {
        var acts = [],
            act_names = [];
        var $salls = $(".select-all");

        $salls.each(function() {
            acts.push($(this).attr("data-name"));
            act_names.push($(this).parent().text());
        });

        var $rows = $("tr.user-row");
        var max = Math.floor($rows.length / $salls.length);
        console.debug("max:", max);
        var rowi = 0,
            acti = 0,
            curi = 0,
            done = 0;
        var maxi = acts.length;
        var sus = {};

        $rows.each(function() {
            var act = acts[acti];
            $("input", $(this)).prop("checked", false);
            $("input[name='" + act + "']", $(this)).prop("checked", true);
            curi++;
            done++;
            if (curi >= max && (acti + 1) < acts.length) {
                sus[acti] = curi;
                acti++;
                curi = 0;
            }
        });

        sus[acti] = curi;
        console.debug(sus);

        var msg = "";
        for (su in sus) {
            if (sus.hasOwnProperty(su) && sus[su] > 0) {
                msg += sus[su] + " students were placed into: " + act_names[su] + "\n";
            }
        }

        msg += "\nTo apply these changes, press the Finish button below.";
        alert(msg);
    }
});
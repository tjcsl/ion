/* global $ */
$(function() {
    $(".select-all").on("click", function(e) {
        e.stopPropagation();
    });

    $(".select-all").on("change", function() {
        let chk = $(this).prop("checked");
        let name = $(this).attr("data-name");

        console.debug(chk, name);

        $(".user-item").each(function() {
            if ($(this).attr("name") === name) {
                $(this).prop("checked", chk).trigger("change");
            }
        });
    });

    $(".user-item").on("change", function() {
        let $box = $(this);
        let chk = $box.prop("checked");
        let name = $box.attr("name");
        let value = $box.attr("value");

        if (chk) {
            let $adjacent = $(`.user-item[value="${value}"]`);
            $adjacent.each(function() {
                let $adj = $(this);
                if ($adj.attr("name") !== $box.attr("name") && $adj.prop("checked")) {
                    $adj.prop("checked", false).trigger("change");
                }
            });
        }

        updateCheckboxes(name);
    });

    function updateCheckboxes(name) {
        let num_checked = 0;
        let $checkboxes = $(".user-item[name='" + name + "']");
        let $e = $(".select-all[data-name='" + name + "']");

        $checkboxes.each(function() {
            if ($(this).prop("checked")) {
                num_checked++;
            }
        });

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
    }

    distribute = function() {
        let totalCapacity = 0;
        let allowExceed = $("input[name=allow-exceed]").prop("checked");
        let acts = [],
            act_names = [];
        let $salls = $(".select-all");
        let $rows = $("tr.user-row");
        let $capacities = $(".remaining-capacity");
        let max = Math.floor($rows.length / $salls.length);
        let rem = $rows.length % $salls.length;
        let sus = {};

        $salls.each(function() {
            acts.push($(this).attr("data-name"));
            act_names.push($(this).parent().text());
        });

        if (!allowExceed) {
            $rows.each(function() {
                $("input", $(this)).prop("checked", false);
            });
            $capacities.each(function() {
                totalCapacity += Number($(this).text());
            });

            let count = 0;
            let count2 = 0;
            let start = 0;
            let sortedCapacities = $capacities.get().sort((a, b) => {
                return Number(a.innerText) - Number(b.innerText);
            });
            let groups = $salls.get().map((group, i) => {
                let available = Number(sortedCapacities[i].innerText);
                let name = sortedCapacities[i].getAttribute("data-name");
                count2++;
                if (max > available) {
                    if ($salls.length - count2 > 0) {
                        max = Math.floor(($rows.length - available) / ($salls.length - count2));
                        rem = ($rows.length - available) % ($salls.length - count2);
                    }
                    return { num: available, act: name };
                } else if (max < available) {
                    count++;
                    return { num: max + (count <= rem ? 1 : 0), act: name };
                } else {
                    return { num: max, act: name };
                }
            });
            let finalGroups = $salls.get().map((finalGroup) => {
                return groups.find(group => group.act === finalGroup.getAttribute("data-name")).num;
            });

            console.debug("Groups:", finalGroups);

            finalGroups.forEach((group, j) => {
                for (let i = start; i < start + group; i++) {
                    let $row = $rows.eq(i);
                    let act = acts[j];
                    $("input", $row).prop("checked", false);
                    $("input[name='" + act + "']", $row).prop("checked", true);
                }
                start += group;
                sus[j] = group;
            });
        } else {
            let groups = [...Array($salls.length)].map((group, i) => {
                if (i < rem) {
                    return max + 1;
                }
                return max;
            });

            console.debug("Groups:", groups);

            let acti = 0,
                curi = 0;

            $rows.each(function() {
                let act = acts[acti];
                $("input", $(this)).prop("checked", false);
                $("input[name='" + act + "']", $(this)).prop("checked", true);
                curi++;
                if (curi >= groups[acti] && (acti + 1) < acts.length) {
                    sus[acti] = curi;
                    acti++;
                    curi = 0;
                }
            });

            sus[acti] = curi;
            console.debug(sus);
        }

        let msg = "";
        for (su in sus) {
            if (sus.hasOwnProperty(su) && sus[su] > 0) {
                msg += sus[su] + " students were placed into: " + act_names[su] + "\n";
            }
        }

        acts.forEach(name => updateCheckboxes(name));

        msg += "\nTo apply these changes, press the Finish button below.";
        alert(msg);
    }
});

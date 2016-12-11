var type_student = false;
var type_attendance = false;

function refreshList() {
    $("#account-list .account").remove();
    if (!$("#account-list .loading").length) {
        $("#account-list").append("<div class='loading'><i class=' fa fa-cog fa-spin fa-3x'></i></div>");
    }
    $.get(list_endpoint + "?type=" + (type_attendance ? "attendance" : (type_student ? "student" : "teacher")), function(data) {
        var adata = data.accounts;
        var output = "";
        $.each(adata, function(k, v) {
            output += "<div class=\"account\" data-id=\"" + v.id + "\"><b>" + v.name  + "</b> (" + v.id + ")</div>";
        });
        $("#account-list").append(output);
        $("#account-list-search").trigger("change");
    }).fail(function() {
        Messenger().error("Failed to load account list.");
    }).always(function() {
        $("#account-list .loading").remove();
    });
}
function loadAccount(id) {
    $("#delete-teacher, #create-notif").toggle(!!id);
    $("#generate-id, #default-fields").toggle(!id);
    $("#ldap-iodineUidNumber").prop("readonly", !!id);
    var type_word = (type_attendance ? "Attendance User" : (type_student ? "Student" : "Teacher"));
    $("#edit-teacher").text((id ? "Edit " : "Create ") + type_word);
    $("#edit-title").text(id ? ("Edit " + type_word +  " Account - " + id) : ("Create " + type_word + " Account"));
    $("#student-fields").toggle(type_student);
    $(".ldap-field").val("");
    $(".ldap-field").attr("data-original", "");
    $("#additional-fields").empty();
    if (id) {
        $("#ldap-loading").show();
        $.get(list_endpoint + "?id=" + encodeURIComponent(id), function(data) {
            $.each(data.account, function(k, v) {
                var ele = $("#ldap-" + k + ".ldap-field");
                if (ele.length) {
                    ele.val(v);
                    ele.attr("data-original", v);
                }
                else if (k !== "objectClass") {
                    $("#additional-fields").append("<div class='form-group'><label><b>Additional Field</b> (" + k + ")</label><input readonly class='ldap-field' id='ldap-" + k + "' type='text' value='" + v.toString().replace("'", "\\'") + "' /></div>");
                }
            });
        }).fail(function() {
            Messenger().error("Failed to retrieve account information.");
        }).always(function() {
            $("#ldap-loading").hide();
        });
    }
}
$(document).ready(function() {
    refreshList();
    $(window).resize(function() {
        $("#account-list").css("height", ($(window).height() - $("#account-list").offset().top - 10) + "px");
        $("#edit-area").css("height", ($(window).height() - $("#edit-area").offset().top - 10) + "px");
    });
    $(window).resize();
    $("#account-list-search").on("change keyup paste", function() {
        var term = $(this).val().toLowerCase();
        $("#account-list .account").each(function() {
            var contains = $(this).text().toLowerCase().indexOf(term) !== -1;
            $(this).toggle(contains);
        });
    });
    $("#account-list").keydown(function(e) {
        var ele = null;
        if (e.which === 38) {
            ele = $(".account.selected").prevAll(":visible").first();
        }
        else if (e.which === 40) {
            ele = $(".account.selected").nextAll(":visible").first();
        }
        if (ele && ele.length && !ele.hasClass("selected")) {
            ele.click();
            var $tl = $("#account-list");
            $tl.scrollTop($tl.scrollTop() + ele.position().top - $tl.height()/2 + ele.height()/2);
            e.preventDefault();
        }
    });
    $("#account-list").on("click", ".account", function() {
        if ($(this).hasClass("selected")) {
            $(this).removeClass("selected");
            loadAccount(false);
        }
        else {
            $(".account").removeClass("selected");
            $(this).addClass("selected");
            loadAccount($(this).attr("data-id"));
            $("#account-list").focus();
        }
    });
    $("#edit-teacher").click(function(e) {
        e.preventDefault();
        var fields = {};
        $(".ldap-field").each(function() {
            fields[$(this).attr("id").substring(5)] = $(this).val();
        });
        fields["objectClass"] = (type_attendance ? "tjhsstUser" : (type_student ? "tjhsstStudent" : "tjhsstTeacher"));
        $.post(modify_endpoint, fields, function(data) {
            if (data.success) {
                Messenger().success((type_attendance ? "Attendance" : (type_student ? "Student" : "Teacher"))+ " account '" + data.id + "' " + (fields["dn"] ? "modified" : "created") + "!");
                loadAccount(data.id);
                refreshList();
            }
            else {
                Messenger().error("Failed to " + (fields["dn"] ? "modify" : "create") + " account." + (data.error ? "<br /><b>Error:</b> " + data.error : "") + (data.details ? "<br /><b>Details</b>: " + data.details : ""));
            }
        });
    });
    $("#type-switch").click(function(e) {
        e.preventDefault();
        var nextType = $(".reverse-account-type").text();
        type_student = nextType == "Student" ? !type_student: (nextType == "Teacher" || nextType == "Attendance" ? false: type_student);
        type_attendance =  nextType == "Attendance" ? !type_attendance: (nextType == "Teacher" || nextType == "Student" ? false: type_attendance);
        $(".account-type").text((type_attendance ? "Attendance": (type_student ? "Student": "Teacher")));
        $(".reverse-account-type").text((type_attendance ? "Teacher": (type_student ? "Attendance": "Student")));
        loadAccount(false);
        refreshList();
    });
    $("#generate-id").click(function(e) {
        e.preventDefault();
        $.get(next_id_endpoint + "?type=" + (type_attendance ? "attendance" : (type_student ? "student" : "teacher")), function(data) {
            $("#ldap-iodineUidNumber").val(data.id);
        }).fail(function() {
            Messenger().error("Failed to generate ID.");
        });
    });
    $("#delete-teacher").click(function(e) {
        e.preventDefault();
        $("#delete-fullname").text($("#ldap-cn").attr("data-original"));
        $("#delete-username").text($("#ldap-iodineUid").attr("data-original"));
        $("#delete-modal-background").fadeIn("fast");
        $("#delete-modal-cancel").focus();
    });
    $("#delete-modal-cancel").click(function(e) {
        e.preventDefault();
        $("#delete-modal-background").fadeOut("fast");
    });
    $("#delete-modal-confirm").click(function(e) {
        e.preventDefault();
        $("#delete-modal-background").fadeOut("fast");
        $.post(delete_endpoint, { "dn": $("#ldap-dn").val() }, function(data) {
            if (data.success) {
                Messenger().success((type_attendance ? "Attendance" : (type_student ? "Student" : "Teacher")) + " account '" + $("#ldap-cn").attr("data-original") + "' deleted!");
                loadAccount(false);
                refreshList();
            }
            else {
                Messenger().error("Failed to delete " + (type_attendance ? "attendance" : (type_student ? "student" : "teacher")) + " account." + (data.error ? "<br /><b>Error:</b> " + data.error : "") + (data.details ? "<br /><b>Details</b>: " + data.details : ""));
            }
        });
    });
});

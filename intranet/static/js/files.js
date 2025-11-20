/* global $ */
$(function() {
    // check for drop support, file support, and file upload support
    if (Modernizr.draganddrop && window.File && window.FormData) {
        $("#additional-upload-option").addClass("visible");
        var endpoint = $("#directory-list").attr("data-endpoint");
        // dragover event must be cancelled to drop
        $(window).on({
            "dragover": function(e) {
                e.originalEvent.dataTransfer.dropEffect = "copy";
                e.preventDefault();
            },
            "dragenter": function(e) {
                var flag = false;
                var dt = e.originalEvent.dataTransfer;
                if (dt.types) {
                    for (var i = 0; i < dt.types.length; i++) {
                        if (dt.types[i] === "Files") {
                            flag = true;
                            break;
                        }
                    }
                }

                if (flag) $("#upload-overlay").fadeIn(150);
            },
            "drop": function(e) {
                $("#upload-overlay").stop().fadeOut(150);
                var dt = e.originalEvent.dataTransfer;
                if (dt) {
                    if (dt.files.length) {
                        var count = dt.files.length;
                        $.each(dt.files, function(index, file) {
                            var safeName = $("<div>").text(file.name).html();
                            var message = Messenger().post({
                                "message": "Uploading <b>" + safeName + "</b>",
                                "type": "info"
                            });
                            var fd = new FormData();
                            fd.append("file", file);
                            fd.append("csrfmiddlewaretoken", $.cookie("csrftoken"));
                            $.ajax({
                                url: endpoint,
                                type: "POST",
                                contentType: false,
                                processData: false,
                                cache: false,
                                data: fd,
                                success: function(data) {
                                    message.update({
                                        "message": "<b>" + safeName + "</b> uploaded",
                                        "type": "success"
                                    });

                                    count--;

                                    if (count <= 0) {
                                        if ($("#directory-list").length) {
                                            var dirList = $("#directory-list", $(data)).html();
                                            $("#directory-list").html(dirList);
                                            $("time").timeago();
                                        }
                                    }
                                },
                                error: function(xhr, stat, err) {
                                    message.update({
                                        "message": "Failed to upload <b>" + safeName + "</b>",
                                        "type": "error"
                                    });
                                }
                            });
                        });
                        e.preventDefault();
                    }
                }
            }
        });

        $("#upload-overlay").on("dragleave", function(e) {
            $("#upload-overlay").stop().fadeOut(150);
        });
    }

    zip_folder = function(item) {
        var name = $(item).attr("data-name");
        var safeName = $("<div>").text(name).html();
        var c = confirm('Are you sure you want to download "' + safeName + '"?');
        if (!c) return false;

        Messenger().post({
            "message": "Generating archive for <b>" + safeName + "</b>",
            "type": "info"
        });

        return true;
    }
});

$(document).ready(function() {
    // check for drop support, file support, and file upload support
    if (Modernizr.draganddrop && window.File && window.FormData) {
        $("#additional-upload-option").show();
        var endpoint = $("#directory-list").attr("data-endpoint");
        // dragover event must be cancelled to drop
        $(window).on("dragover", function(e) {
            e.originalEvent.dataTransfer.dropEffect = "copy";
            e.preventDefault();
        });
        $(window).on("drop", function(e) {
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
                                count -= 1;
                                // page reloads when all requests are done
                                // this could be made better if a notification could
                                // be displayed and the list of files could be refreshed
                                if (count <= 0) {
                                    message.update({
                                        "message": "Upload succeeded.",
                                        "type": "info"
                                    });
                                    
                                    var dirList = $("#directory-list", $(data)).html();
                                    $("#directory-list").html(dirList);
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
        });
    }


    zip_folder = function() {
        var c = confirm('Are you sure you want to download this folder?');
        if(!c) return false;
        Messenger().post({
            "message": "Generating archive for <b>" + $(this).attr("data-name") + "</b>",
            "type": "info"
        });
        return true;
    }
});

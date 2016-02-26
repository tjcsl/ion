$(document).ready(function() {
    // check for drop support, file support, and file upload support
    if (Modernizr.draganddrop && window.File && window.FormData) {
        $("#additional-upload-option").show();
        var params = {};
        window.location.search.replace(/[?&]+([^=&]+)=([^&]*)/gi,function(str,key,value){params[key] = value;});
        var dir = params["dir"];
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
                        Messenger().post({
                            "message": "Uploading <b>" + safeName + "</b>",
                            "type": "info"
                        });
                        var fd = new FormData();
                        fd.append("file", file);
                        fd.append("csrfmiddlewaretoken", $.cookie("csrftoken"));
                        $.ajax({
                            url: "upload?dir=" + encodeURIComponent(dir),
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
                                    window.location.reload();
                                }
                            },
                            error: function(xhr, stat, err) {
                                Messenger().post({
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
});

$(document).ready(function() {

    $("div[data-placeholder]").on("keydown keypress input", function() {
        if(this.textContent) {
            this.dataset.divPlaceholderContent = 'true';
        } else {
            delete(this.dataset.divPlaceholderContent);
        }
    });
});

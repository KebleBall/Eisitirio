jQuery('#flashes li').on('click', function(event) {
    jQuery(event.target).fadeOut(250);
});

jQuery('.message-box.hideable').on('click', function(event) {
    jQuery(event.target).fadeOut(250);
});

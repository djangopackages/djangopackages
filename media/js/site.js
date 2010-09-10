// Ajax submit for the package usage
$(".usage-button a").live('click', function(e) {
    var url = e.target.href,
        container = $(e.target).parent();
    e.target.href = ''; // Disabling the link to hopefully avoid double clicks
    
    $.getJSON(url, function(data) {
        container.html(data.body); // Sets the button to be the rendered template
        // Looking to update the count, the usage count needs to be within the usage-container
        var count_el = container.parent('.usage-container').children('.usage-count');
        if (count_el) {
            count_el.html(parseInt(count_el.html(), 10)+data.change);
        }
    });
    e.preventDefault();
});
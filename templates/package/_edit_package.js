$("#id_title").focus();

var repo_urls = eval({{ repos|safe }})

$("#id_repo").change(function() {
    var url = repo_urls[$('#id_repo').val()]
    $("#id_repo_url").val(url);
    
});

// need to add 'is_other' to repos so we can make this work

String.prototype.starts_with = function(str){
    return (this.indexOf(str) === 0);
}

String.prototype.ends_with = function(str){
    return (this.lastIndexOf(str) === this.length-str.length);
}

$("#id_repo_url").focus();
$("#div_id_repo").hide();

var repo_urls = eval({{ repos|safe }});

pypi_url_g = "http://pypi.python.org/pypi/";

$("#id_pypi_url").val($("#id_pypi_url").val().replace(pypi_url_g,""));

$("#id_pypi_url").change(function(e){
    $("#id_pypi_url").val($("#id_pypi_url").val().replace(pypi_url_g,""));
});

$("#id_repo_url").keyup(function(e) {
    var url = $("#id_repo_url").val();
    return url
});
    
$("#id_repo_url").change(function(e) {
 
    $("#target").text($("#id_repo_url").val());
    
    var url = $("#id_repo_url").val();
    
    // this fixes the problem with trailing slashes
    while (1==1){
            if (url.ends_with('/')){
                url = url.slice(0, url.length-1);
                $("#id_repo_url").val(url);
                }
            else {
                break;
            };
        };
    // for github
    if (url.starts_with('http://github.com')){
        url = url.replace('http://github.com','https://github.com');
        $("#id_repo_url").val(url);
    };
    if (url.starts_with('git@github.com:')){
        url = url.replace("git@github.com:","https://github.com/");
    };
    if (url.starts_with('git://github.com/')){
        url = url.replace("git://github.com/","https://github.com/");
        $("#id_repo_url").val(url);                
    };
    if (url.ends_with('.git')){
        url = url.slice(0, url.length-4);
        $("#id_repo_url").val(url);                
    };
    // for bitbucket
    if (url.starts_with('http://bitbucket.org')){
        url = url.replace('http://bitbucket.org','https://bitbucket.org');
        $("#id_repo_url").val(url);        
    };
    
    var url_array = url.split('/');
    $.each(repo_urls, function(key, value) {
        if (url.starts_with(key)){
            if (url !== key){
                $("#id_repo").val(value);
                if ($("#id_title").val().length === 0) {
                    $("#id_title").val(url_array[url_array.length-1]);
                };
                var slug = DPSlugify(url_array[url_array.length-1]);
                $("#id_slug").val(slug);
                $("#id_pypi_url").val(slug);
                $("#package-form-message").text("Your package is hosted at " + key)
            };
        };
    });
});

$("#package-form").submit(function(e) {
    // hack to get around some database vs front end weirdness
    var pypi_url = $("#id_pypi_url").val();
    if (pypi_url.length > 0){
      $("#id_pypi_url").attr("name", "nuke");
      $("#temp").val(pypi_url_g + pypi_url);
      $("#temp").attr("name", "pypi_url");     
    };
    
    // TODO - make this work off a database change where we add the is_other boolean to repos
    var repo = $("#id_repo").val();
    if (repo.length === 0){
        $("#id_repo").val("4");
    };
    
    return true
});

/*
    gh3.js
    Created : 2012.07.25 by k33g

    TODO :
        - Repositories for an organization
        - Search : http://developer.github.com/v3/search/
        - ...

    History :
        - 2012.07.25 : '0.0.1' : first version
        - 2012.07.26 : '0.0.2' : fixes
        - 2012.07.26 : '0.0.3' : gists pagination
        - 2012.07.28 : '0.0.4' :
            * refactoring : Gh3.Helper
            * gists filtering
            * gist comments filtering
            * file commits filtering
            * commits sorting
            * new Type : Gh3.Repositories (with pagination)
        - 2012.07.29 : '0.0.5' :
            * Gh3.Repositories : add search ability     
            * add Gh3.Users : search user ability
        - 2012.07.29 : '0.0.6' :
            * async.js compliant
        - 2012.08.02 : '0.0.7' :
            * Node compliant for the future ... becareful to dependencies           
*/

(function () {

    //var Gh3 = this.Gh3 = {}
    var root = this
    ,   Gh3
    ,   Kind
    ,   Base64;
    
    if (typeof exports !== 'undefined') {
        Gh3 = exports;
    } else {
        Gh3 = root.Gh3 = {};
    }

    Gh3.VERSION = '0.0.7'; //2012.08.02
    
    //Object Model Tools (helpers) like Backbone
    Kind = function(){};
    
    Kind.inherits = function (parent, protoProps, staticProps) {
        var child
            , ctor = function(){}
            , merge = function (destination, source) {
                for (var prop in source) {
                    destination[prop] = source[prop];
                }
        };
        //constructor ....
        if (protoProps && protoProps.hasOwnProperty('constructor')) {
            child = protoProps.constructor;
        } else {
            child = function(){ parent.apply(this, arguments); };
        }
    
        //inherits from parent
        merge(child, parent);
    
        ctor.prototype = parent.prototype;
        child.prototype = new ctor();
    
        //instance properties
        if(protoProps) merge(child.prototype, protoProps);
    
        //static properties
        if(staticProps) merge(child, staticProps);
    
        // Correctly set child's `prototype.constructor`.
        child.prototype.constructor = child;
    
        // Set a convenience property in case the parent's prototype is needed later.
        child.__super__ = parent.prototype;
    
        return child
    
    };
    Kind.extend = function (protoProps, staticProps) {
        var child = Kind.inherits(this, protoProps, staticProps);
        child.extend = this.extend;
        return child;
    };
    

    Base64 = { //http://www.webtoolkit.info/javascript-base64.html
 
        // private property
        _keyStr : "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=",
         
        // public method for decoding
        decode : function (input) {
            var output = "";
            var chr1, chr2, chr3;
            var enc1, enc2, enc3, enc4;
            var i = 0;
     
            input = input.replace(/[^A-Za-z0-9\+\/\=]/g, "");
     
            while (i < input.length) {
     
                enc1 = this._keyStr.indexOf(input.charAt(i++));
                enc2 = this._keyStr.indexOf(input.charAt(i++));
                enc3 = this._keyStr.indexOf(input.charAt(i++));
                enc4 = this._keyStr.indexOf(input.charAt(i++));
     
                chr1 = (enc1 << 2) | (enc2 >> 4);
                chr2 = ((enc2 & 15) << 4) | (enc3 >> 2);
                chr3 = ((enc3 & 3) << 6) | enc4;
     
                output = output + String.fromCharCode(chr1);
     
                if (enc3 != 64) {
                    output = output + String.fromCharCode(chr2);
                }
                if (enc4 != 64) {
                    output = output + String.fromCharCode(chr3);
                }
     
            }
     
            output = Base64._utf8_decode(output);
     
            return output;
     
        },

        encode : function (input) {
                var output = "";
                var chr1, chr2, chr3, enc1, enc2, enc3, enc4;
                var i = 0;

                input = Base64._utf8_encode(input);

                while (i < input.length) {

                        chr1 = input.charCodeAt(i++);
                        chr2 = input.charCodeAt(i++);
                        chr3 = input.charCodeAt(i++);

                        enc1 = chr1 >> 2;
                        enc2 = ((chr1 & 3) << 4) | (chr2 >> 4);
                        enc3 = ((chr2 & 15) << 2) | (chr3 >> 6);
                        enc4 = chr3 & 63;

                        if (isNaN(chr2)) {
                                enc3 = enc4 = 64;
                        } else if (isNaN(chr3)) {
                                enc4 = 64;
                        }

                        output = output +
                        this._keyStr.charAt(enc1) + this._keyStr.charAt(enc2) +
                        this._keyStr.charAt(enc3) + this._keyStr.charAt(enc4);

                }

                return output;
        },

        // private method for UTF-8 decoding
        _utf8_decode : function (utftext) {
            var string = "";
            var i = 0;
            var c = c1 = c2 = 0;
     
            while ( i < utftext.length ) {
     
                c = utftext.charCodeAt(i);
     
                if (c < 128) {
                    string += String.fromCharCode(c);
                    i++;
                }
                else if((c > 191) && (c < 224)) {
                    c2 = utftext.charCodeAt(i+1);
                    string += String.fromCharCode(((c & 31) << 6) | (c2 & 63));
                    i += 2;
                }
                else {
                    c2 = utftext.charCodeAt(i+1);
                    c3 = utftext.charCodeAt(i+2);
                    string += String.fromCharCode(((c & 15) << 12) | ((c2 & 63) << 6) | (c3 & 63));
                    i += 3;
                }
     
            }
     
            return string;
        },

        // private method for UTF-8 encoding
        _utf8_encode : function (string) {
                string = string.replace(/\r\n/g,"\n");
                var utftext = "";

                for (var n = 0; n < string.length; n++) {

                        var c = string.charCodeAt(n);

                        if (c < 128) {
                                utftext += String.fromCharCode(c);
                        }
                        else if((c > 127) && (c < 2048)) {
                                utftext += String.fromCharCode((c >> 6) | 192);
                                utftext += String.fromCharCode((c & 63) | 128);
                        }
                        else {
                                utftext += String.fromCharCode((c >> 12) | 224);
                                utftext += String.fromCharCode(((c >> 6) & 63) | 128);
                                utftext += String.fromCharCode((c & 63) | 128);
                        }

                }

                return utftext;
        }       
             
    }


    Gh3.Base64 = Base64;

    if (window.XDomainRequest != null) {
        try {
            new XDomainRequest()
            $.support.cors = true
            $.ajaxSetup.xhr = function() { return new XDomainRequest() }
        } catch (e) {}
    }

    Gh3.Helper = Kind.extend({

    },{
        protocol : "https",
        domain : "api.github.com",
        callHttpApi : function (apiParams) {
            apiParams.url = Gh3.Helper.protocol + "://" + Gh3.Helper.domain + "/" + apiParams.service;
            if ($.support.cors) {
                apiParams.headers = { Origin: location.host }
                var success = apiParams.success
                if ($.isFunction(success)) {
                    apiParams.success = function (data, textStatus, jqXHR) {
                        success.call(this, {data: data}, textStatus, jqXHR)
                    }
                }
            } else {
                //delete apiParams.service;
                apiParams.dataType = 'jsonp';
            }

            $.ajax(apiParams);
        }
    });

    Gh3.Users = Kind.extend({

    },{//static members
        users : [],
        search : function (keyword, pagesInfo, callback) {
            Gh3.Users.users = [];
            Gh3.Helper.callHttpApi({
                service : "legacy/user/search/"+keyword,
                data : pagesInfo,
                //beforeSend: function (xhr) { xhr.setRequestHeader ("rel", paginationInfo); },
                success : function(res) {
                    _.each(res.data.users, function (user) {
                        Gh3.Users.users.push(new Gh3.User(user.login, user));
                    });
                    
                    if (callback) callback(null, Gh3.Users);
                },
                error : function (res) {
                    if (callback) callback(new Error(res));
                }
            });

        },
        reverse : function () {
            Gh3.Users.users.reverse();
        },
        sort : function (comparison_func) {
            if (comparison_func) {
                Gh3.Users.users.sort(comparison_func);
            } else {
                Gh3.Users.users.sort();
            }
        },
        getAll : function() { return Gh3.Users.users; },
        getByName : function (name) {
            return _.find(Gh3.Users.users, function (item) {
                return item.name == name;
            });
        },
        each : function (callback) {
            _.each(Gh3.Users.users, function (user) {
                callback(user);
            });
        },
        filter : function (comparator) {
            return _.filter(Gh3.Users.users, comparator);
        }

    });

    Gh3.User = Kind.extend({
    
        constructor : function (login, user_infos) {

            if (user_infos) {
                for(var prop in user_infos) {
                    this[prop] = user_infos[prop];
                }
            }

            if (login) {
                this.login = login; 
            } else { 
                throw "login !";
            }
        },
        fetch : function (callback) {
            var that = this;

            Gh3.Helper.callHttpApi({
                service : "users/"+that.login,
                success : function (res) {
                    for(var prop in res.data) {
                        that[prop] = res.data[prop];
                    }
                    if (callback) callback(null, that);
                },
                error : function (res) {
                    if (callback) callback(new Error(res));
                }
            });
            
        }
        
        
    },{});
    

    /*Gists*/

    Gh3.GistComment = Kind.extend({
        constructor : function (gistCommentData) {
            for(var prop in gistCommentData) {
                this[prop] = gistCommentData[prop];
            }
        }
    },{});

    Gh3.Gist = Kind.extend({
        constructor : function (gistData) {
            for(var prop in gistData) {
                this[prop] = gistData[prop];
            }
        },
        fetchContents : function (callback) {
            var that = this;
            that.files = [];

            Gh3.Helper.callHttpApi({
                service : "gists/"+that.id,
                success : function(res) {

                    for(var file in res.data.files) {
                        that.files.push(res.data.files[file]);
                    }

                    delete res.data.files;

                    for(var prop in res.data) {
                        that[prop] = res.data[prop];
                    }
                    if (callback) callback(null, that);
                },
                error : function (res) {
                    if (callback) callback(new Error(res));
                }
            });


        },
        fetchComments : function (callback) {
            var that = this;
            that.comments = [];


            Gh3.Helper.callHttpApi({
                service : "gists/"+that.id+"/comments",
                success : function(res) {
                    _.each(res.data, function (comment) {
                        that.comments.push(new Gh3.GistComment(comment));
                    });
                    if (callback) callback(null, that);
                },
                error : function (res) {
                    if (callback) callback(new Error(res));
                }
            });
    
        },
        getFileByName : function (name) {
            return _.find(this.files, function (file) {
                return file.filename == name;
            });
        },
        getFiles : function () {
            return this.files;
        },
        eachFile : function (callback) {
            _.each(this.files, function (file) {
                callback(file);

            });
        },
        getComments : function () { return this.comments; },
        eachComment : function (callback) {
            _.each(this.comments, function (comment) {
                callback(comment);
            });
        },
        filterComments : function (comparator) {
            return _.filter(this.comments, comparator);
        }

    },{});

    Gh3.Gists = Kind.extend({//http://developer.github.com/v3/gists/
        constructor : function (ghUser) {
            if (ghUser) this.user = ghUser;
            this.gists = []
        },
        fetch : function (pagesInfo, paginationInfo, callback) {//http://developer.github.com/v3/#pagination
            var that = this;

            Gh3.Helper.callHttpApi({
                service : "users/"+that.user.login+"/gists",
                data : pagesInfo,
                beforeSend: function (xhr) { xhr.setRequestHeader ("rel", paginationInfo); },
                success : function(res) {
                    _.each(res.data, function (gist) {
                        that.gists.push(new Gh3.Gist(gist));
                    });
                    if (callback) callback(null, that);
                },
                error : function (res) {
                    if (callback) callback(new Error(res));
                }
            });

        },

        getGists : function () { return this.gists; },
        eachGist : function (callback) {
            _.each(this.gists, function (gist) {
                callback(gist);
            });
        },
        filter : function (comparator) {
            return _.filter(this.gists, comparator);
        }

    },{});


    Gh3.Commit = Kind.extend({
        constructor : function (commitInfos) {
            this.author = commitInfos.author;
            this.author.email = commitInfos.commit.author.email;
            this.author.name = commitInfos.commit.author.name;
            this.date = commitInfos.commit.author.date;
            this.message = commitInfos.commit.message;
            this.sha = commitInfos.sha;
            this.url = commitInfos.url;
        }
    },{});

    Gh3.ItemContent = Kind.extend({
        constructor : function (contentItem, ghUser, repositoryName, branchName) {
            for(var prop in contentItem) {
                this[prop] = contentItem[prop];
            }
            if (ghUser) this.user = ghUser;
            if (repositoryName) this.repositoryName = repositoryName;
            if (branchName) this.branchName = branchName;
        }

    },{});

    Gh3.File = Gh3.ItemContent.extend({
        constructor : function (contentItem, ghUser, repositoryName, branchName) {
            Gh3.File.__super__.constructor.call(this, contentItem, ghUser, repositoryName, branchName);
        },
        fetchContent : function (callback) {
            var that = this;
            
            Gh3.Helper.callHttpApi({
                service : "repos/"+that.user.login+"/"+that.repositoryName+"/contents/"+that.path,
                success : function(res) {
                    that.content = res.data.content;
                    that.rawContent = Base64.decode(res.data.content);

                    if (callback) callback(null, that);
                },
                error : function (res) {
                    if (callback) callback(new Error(res));
                }
            });

        },
        fetchCommits : function (callback) {//http://developer.github.com/v3/repos/commits/
            var that = this;
            that.commits = [];

            Gh3.Helper.callHttpApi({
                service : "repos/"+that.user.login+"/"+that.repositoryName+"/commits",
                data : {path: that.path },
                success : function(res) {
                    _.each(res.data, function (commit) {
                        that.commits.push(new Gh3.Commit(commit));
                    });
                    if (callback) callback(null, that);
                },
                error : function (res) {
                    if (callback) callback(new Error(res));
                }
            });

        },
        getRawContent : function() { return this.rawContent; },
        getCommits : function () { return this.commits; },
        getLastCommit : function () {
            return this.commits[0];
        },
        getFirstCommit : function () {
            return this.commits[this.commits.length-1];
        },
        eachCommit : function (callback) {
            _.each(this.commits, function (branch) {
                callback(branch);
            });
        },
        filterCommits : function (comparator) {
            return _.filter(this.commits, comparator);
        },
        reverseCommits : function () {
            this.commits.reverse();
        },
        sortCommits: function (comparison_func) {
            if (comparison_func) {
                this.commits.sort(comparison_func);
            } else {
                this.commits.sort();
            }
        }
    },{});


    Gh3.Dir = Gh3.ItemContent.extend({
        constructor : function (contentItem, ghUser, repositoryName, branchName) {
            Gh3.Dir.__super__.constructor.call(this, contentItem, ghUser, repositoryName, branchName);
        },
        fetchContents : function (callback) {
            var that = this;
            that.contents = [];

            Gh3.Helper.callHttpApi({
                service : "repos/"+that.user.login+"/"+that.repositoryName+"/contents/"+that.path,
                data : {ref: that.branchName },
                success : function(res) {
                    _.each(res.data, function (item) {
                        if (item.type == "file") that.contents.push(new Gh3.File(item, that.user, that.repositoryName, that.branchName));
                        if (item.type == "dir") that.contents.push(new Gh3.Dir(item, that.user, that.repositoryName, that.branchName));
                    });
                    if (callback) callback(null, that);
                },
                error : function (res) {
                    if (callback) callback(new Error(res));
                }
            });

        },
        reverseContents : function () {
            this.contents.reverse();
        },
        sortContents : function (comparison_func) {
            if (comparison_func) {
                this.contents.sort(comparison_func);
            } else {
                this.contents.sort();
            }
        },
        getContents : function() { return this.contents; },
        getFileByName : function (name) {
            return _.find(this.contents, function (item) {
                return item.name == name && item.type == "file";
            });
        },
        getDirByName : function (name) {
            return _.find(this.contents, function (item) {
                return item.name == name && item.type == "dir";
            });
        },
        eachContent : function (callback) {
            _.each(this.contents, function (branch) {
                callback(branch);
            });
        },
        filterContents : function (comparator) {
            return _.filter(this.contents, comparator);
        }

    },{});

    Gh3.Branch = Kind.extend({
        constructor : function (name, sha, url, ghUser, repositoryName) {
            if (name) this.name = name;
            if (sha) this.sha = sha;
            if (url) this.url = url;

            if (ghUser) this.user = ghUser;
            if (repositoryName) this.repositoryName = repositoryName;

        },

        fetchContents : function (callback) { //see how to refactor with Gh3.Dir
            var that = this;
            that.contents = [];

            Gh3.Helper.callHttpApi({
                service : "repos/"+that.user.login+"/"+that.repositoryName+"/contents/",
                data : {ref: that.name },
                success : function(res) {
                    _.each(res.data, function (item) {

                        if (item.type == "file") that.contents.push(new Gh3.File(item, that.user, that.repositoryName, that.name));
                        if (item.type == "dir") that.contents.push(new Gh3.Dir(item, that.user, that.repositoryName, that.name));
                    });
                    if (callback) callback(null, that);
                },
                error : function (res) {
                    if (callback) callback(new Error(res));
                }
            });

        },
        reverseContents : function () {
            this.contents.reverse();
        },
        sortContents : function (comparison_func) {
            if (comparison_func) {
                this.contents.sort(comparison_func);
            } else {
                this.contents.sort();
            }
        },
        getContents : function() { return this.contents; },
        getFileByName : function (name) {
            return _.find(this.contents, function (item) {
                return item.name == name && item.type == "file";
            });
        },
        getDirByName : function (name) {
            return _.find(this.contents, function (item) {
                return item.name == name && item.type == "dir";
            });
        },
        eachContent : function (callback) {
            _.each(this.contents, function (branch) {
                callback(branch);
            });
        },
        filterContents : function (comparator) {
            return _.filter(this.contents, comparator);
        }
        
    },{});

    Gh3.Repository = Kind.extend({
        constructor : function (name, ghUser, infos) {

            if (infos) {
                for(var prop in infos) {
                    this[prop] = infos[prop];
                }
            }

            if (name) this.name = name;

            if (ghUser) this.user = ghUser;

        },
        fetch : function (callback) {
            var that = this;
            //TODO test user.login & name

            Gh3.Helper.callHttpApi({
                service : "repos/"+that.user.login+"/"+that.name,
                success : function(res) {
                    for(var prop in res.data) {
                        that[prop] = res.data[prop];
                    }
                    if (callback) callback(null, that);
                },
                error : function (res) {
                    if (callback) callback(new Error(res));
                }
            });

        },
        fetchBranches : function (callback) {
            var that = this;
            that.branches = [];

            Gh3.Helper.callHttpApi({
                service : "repos/"+that.user.login+"/"+that.name+"/branches",
                success : function(res) {
                    _.each(res.data, function (branch) {
                        that.branches.push(new Gh3.Branch(branch.name, branch.commit.sha, branch.commit.url, that.user, that.name));
                    });
                    
                    if (callback) callback(null, that);
                },
                error : function (res) {
                    if (callback) callback(new Error(res));
                }
            });

        },
        getBranches : function () { return this.branches; },
        getBranchByName : function (name) {
            return _.find(this.branches, function (branch) {
                return branch.name == name;
            });
        },
        eachBranch : function (callback) {
            _.each(this.branches, function (branch) {
                callback(branch);
            });
        },
        reverseBranches : function () {
            this.branches.reverse();
        },
        sortBranches : function (comparison_func) {
            if (comparison_func) {
                this.branches.sort(comparison_func);
            } else {
                this.branches.sort();
            }
        }

    },{});

    //TODO: Repositories for an organization
    
    Gh3.Repositories = Kind.extend({//http://developer.github.com/v3/repos/
        constructor : function (ghUser) {

            if (ghUser) this.user = ghUser;

        },
        //List user repositories
        fetch : function (pagesInfoAndParameters, paginationInfo, callback) {
            var that = this;
            that.repositories = [];

            Gh3.Helper.callHttpApi({
                service : "users/"+that.user.login+"/repos",
                data : pagesInfoAndParameters,
                beforeSend: function (xhr) { xhr.setRequestHeader ("rel", paginationInfo); },
                success : function(res) {
                    _.each(res.data, function (repository) {
                        that.repositories.push(new Gh3.Repository(repository.name, that.user));
                    });
                    
                    if (callback) callback(null, that);
                },
                error : function (res) {
                    if (callback) callback(new Error(res));
                }
            });

        },
        reverseRepositories : function () {
            this.repositories.reverse();
        },
        sortRepositories : function (comparison_func) {
            if (comparison_func) {
                this.repositories.sort(comparison_func);
            } else {
                this.repositories.sort();
            }
        },
        getRepositories : function() { return this.repositories; },
        getRepositoryByName : function (name) {
            return _.find(this.repositories, function (item) {
                return item.name == name;
            });
        },

        eachRepository : function (callback) {
            _.each(this.repositories, function (repository) {
                callback(repository);
            });
        },
        filterRepositories : function (comparator) {
            return _.filter(this.repositories, comparator);
        }


    },{//static members
        repositories : [],
        search : function (keyword, pagesInfo, callback) {
            Gh3.Repositories.repositories = [];
            Gh3.Helper.callHttpApi({
                service : "legacy/repos/search/"+keyword,
                data : pagesInfo,
                //beforeSend: function (xhr) { xhr.setRequestHeader ("rel", paginationInfo); },
                success : function(res) {
                    //console.log("*** : ", res);
                    _.each(res.data.repositories, function (repository) {
                        Gh3.Repositories.repositories.push(new Gh3.Repository(repository.name, new Gh3.User(repository.owner), repository));
                        //owner & login : same thing ???
                    });
                    
                    if (callback) callback(null, Gh3.Repositories);
                },
                error : function (res) {
                    if (callback) callback(new Error(res));
                }
            });

        },
        reverse : function () {
            Gh3.Repositories.repositories.reverse();
        },
        sort : function (comparison_func) {
            if (comparison_func) {
                Gh3.Repositories.repositories.sort(comparison_func);
            } else {
                Gh3.Repositories.repositories.sort();
            }
        },
        getAll : function() { return Gh3.Repositories.repositories; },
        getByName : function (name) {
            return _.find(Gh3.Repositories.repositories, function (item) {
                return item.name == name;
            });
        },
        each : function (callback) {
            _.each(Gh3.Repositories.repositories, function (repository) {
                callback(repository);
            });
        },
        filter : function (comparator) {
            return _.filter(Gh3.Repositories.repositories, comparator);
        }
    });


    
}).call(this);
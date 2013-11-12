function SearchCtrl($scope, $http) {
  $scope.model = {};

  $scope.init_search = function(q, url, max_weight){
    // search page initialization
    $scope.model.q = q;
    $scope.max_weight = max_weight;
    $scope.search($scope.model, url);
  };

  $scope.search = function(model, url){
    // core search page search function
    if (model.q.length){
        $http.get(url + '?q='+model.q).success(function(data) {
          $scope.items = data.results;
        });
    } else {
        $scope.items = [];
        
    };
  };

  $scope.get_python3_packages = function(url){
    console.log("what")
    $http.get(url).success(function(data) {
        $scope.python3_packages = data.results;
    });
  };
}

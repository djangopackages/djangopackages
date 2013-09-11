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
    $http.get(url + '?q='+model.q).success(function(data) {
      $scope.items = data.results;
    });
  };
}

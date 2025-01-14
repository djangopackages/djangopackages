function SearchCtrl($scope, $http) {
  $scope.model = {};

  $scope.init_search = function(q, url, max_weight, test_mode){
    // search page initialization
    $scope.model.q = q;
    $scope.max_weight = max_weight;
    $scope.TEST_MODE = test_mode;
    $scope.search($scope.model, url);
  };

  $scope.search = function(model, url){
    // core search page search function
    if (model.q.length){
        $http.get(url + '?q='+model.q).success(function(data) {
          $scope.items = data;
        });
    } else {
        $scope.items = [];
    };
  };

  $scope.get_python3_packages = function(url){
    $http.get(url).success(function(data) {
        $scope.python3_packages = data.results;
    });
  };

  $scope.waffle_flag_is_active = (flagName) => waffle.flag_is_active(flagName);
}

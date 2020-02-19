let app = angular.module("autoProject", []);

app.config(function($interpolateProvider) {
  $interpolateProvider.startSymbol('%%');
  $interpolateProvider.endSymbol('%%');
});

app.run(["$http","$rootScope", function($http, $rootScope) {
  $http({
    method: 'GET',
    url: '/config'
  }).then(function successCallback(response) {
    $rootScope.analysisType = response.data.analysisType;
    if ($rootScope.analysisType == null) {
      $("#modalMainMenu").modal({"show": true});
    } else {
      $("#main").toggleClass("d-none");
    }

  }, function errorCallback(response) {
    //$rootScope.analysisType = null;
    //$("#modalMainMenu").addClass("d-none");
  });

  $rootScope.CAN_SPEED = [10, 20, 50, 100, 125, 250, 500, 800, 1000];
  $rootScope.VEHICLE_TYPE = ["Voiture", "Deux-roues", "Camion", "Bateau","Aéronef"];
}]);

// SocketIO integration
app.factory('socket', function ($rootScope) {
  var socket = io.connect();
  return {
    on: function (eventName, callback) {
      socket.on(eventName, function () {
        var args = arguments;
        $rootScope.$apply(function () {
          callback.apply(socket, args);
        });
      });
    },
    emit: function (eventName, data, callback) {
      socket.emit(eventName, data, function () {
        var args = arguments;
        $rootScope.$apply(function () {
          if (callback) {
            callback.apply(socket, args);
          }
        });
      })
    }
  };
});

app.controller("mainMenuController", function($scope, $rootScope, $http) {
  $scope.display = "mainMenu";
  $scope.vehicleAddTab = 'auto';
  $scope.manufacturers = {}
  $scope.models = [];
  $scope.type = $rootScope.VEHICLE_TYPE[0];

  $scope.autoDetectSpeed = 500;
  $scope.autoDetectType = $rootScope.VEHICLE_TYPE[0];

  $scope.goToMainMenu = function() {
      $scope.display = "mainMenu";
  }

  $scope.showNewVehicleMenu = function() {
    $scope.display = "vehicleOptionMenu";

    $http({
      method: 'GET',
      url: '/loadVehicleOptionsMenu'
    }).then(function successCallback(response) {
      $scope.manufacturers = response.data.manufacturers;
      $scope.brand = [];
      for (let manufacturer in $scope.manufacturers) {
        $scope.brand.push(manufacturer);
      }

      console.log($scope.brand);


    }, function errorCallback(response) {
      console.log(response);
    });
  }
});

app.controller("HelloController", function($scope) {
	console.log("Angular called");
	$scope.helloTo = {};
  $scope.helloTo.title = "AngularJS";
});

let ids = {};
let updateField = function (id, data) {
	for (let i =0; i < 8; i++) {
		if (i < data.length) {
			let hexValue = data[i].toString(16);
			if (hexValue.length < 2) hexValue = "0" + hexValue;
			if (data[i] != ids[id]["prevValue"][i]) {
				hexValue = "<i>0x" + hexValue + "</i>";
				ids[id]["prevValue"][i] = data[i];
			}
			else hexValue = "0x" + hexValue;
			$('#arb'+ id + ' .data'+ i).html( hexValue);
		} else $('#arb'+ id + ' .data'+ i).html("");
	}
};

function isObject(v) {
return '[object Object]' === Object.prototype.toString.call(v);
};

JSON.sort = function(o) {
if (Array.isArray(o)) {
return o.sort().map(JSON.sort);
} else if (isObject(o)) {
return Object
	.keys(o)
.sort()
	.reduce(function(a, k) {
			a[k] = JSON.sort(o[k]);

			return a;
	}, {});
}

return o;
}

$(document).ready(function(){
});

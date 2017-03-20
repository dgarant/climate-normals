var app = angular.module("Normals");

app.directive("singleDistributionVis", [function() {
    function buildVis(scope, element, attrs) {
        // approximating the distribution as a normal
        var dlower = scope.stats.snow_depth_inches_50pctl - scope.stats.snow_depth_inches_25pctl;
        var dupper = scope.stats.snow_depth_inches_75pctl - scope.stats.snow_depth_inches_50pctl;

        var mean = scope.stats.snow_depth_inches_50pctl;
        // Z score of 0.675 is at 75th percentile for standard normal
        var stdDev = (dlower + dupper / 2.0) / 0.675;
        var evalPoints = _.range(mean - 4 * stdDev, mean + 4 * stdDev, 0.1 * stdDev);
        var densityPoints = _.map(evalPoints, function(v) {
            return jStat.normal.pdf(v, mean, stdDev);
        });
        console.log(evalPoints);
        console.log(densityPoints);
    }

    return {
        link : function(scope, element, attrs) {
            scope.$watch("stats", function(newVal, oldVal) {
                if(newVal) {
                    buildVis(scope, element, attrs);
                }
            });
        },
        scope : {
            stats : "="
        }
    }
}]);

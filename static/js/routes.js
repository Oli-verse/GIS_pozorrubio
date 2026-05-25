var activePolylines = [];

function clearRoutes() {
    activePolylines.forEach(function(p) { p.remove(); });
    activePolylines = [];
}

function showRoutes(barangayName) {
    clearRoutes();
    var routes = window.routeData[barangayName];
    if (!routes || routes.length === 0) return;

    var reversed = routes.slice().reverse();
    reversed.forEach(function(route, idx) {
        var actualIdx  = routes.length - 1 - idx;
        var color      = window.routeColors[actualIdx % window.routeColors.length];
        var isShortest = actualIdx === 0;

        var polyline = L.polyline(route.coords, {
            color:     color,
            weight:    isShortest ? 5 : 2.5,
            opacity:   isShortest ? 1.0 : 0.55,
            dashArray: isShortest ? null : '5, 7',
        }).addTo(window._map);

        activePolylines.push(polyline);
    });
}
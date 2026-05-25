document.addEventListener('DOMContentLoaded', function() {
    setTimeout(function() {
        window._map = Object.values(window).find(
            function(v) { return v && v._container && v.setView; }
        );
        if (window._map) {
            window._map.on('click', function(e) {
                if (!e.originalEvent.target.classList.contains('leaflet-interactive')) {
                    clearRoutes();
                }
            });
        }
    }, 500);
});
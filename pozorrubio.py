import folium
import json
import pandas as pd

from data_loader.loader     import load_barangays, load_universities, load_travels, load_geojson
from osrm_client.router     import build_travel_lookup, compute_all_routes
from map_builder.layers     import ROUTE_COLORS, add_boundary, add_university_markers, add_legend
from map_builder.popups     import build_barangay_popup, build_tooltip

'''
Pozorrubio GIS - Interactive Routing Map
AI agents used:
Google Gemini - Research and Implementation
Claude - Logic and debugging
Copilot - Code completion
'''

# -- Data
barangays    = load_barangays()
universities = load_universities()
travels      = load_travels()
geo          = load_geojson()

# -- Routing
travel_lookup = build_travel_lookup(travels, universities)
all_routes    = compute_all_routes(barangays, universities, travel_lookup)

# -- Map
map = folium.Map(location=[16.11, 120.54], zoom_start=13, tiles='CartoDB positron')
add_boundary(map, geo)

# -- Inject static JS files
def inject_js(map, filepath):
    with open(filepath, encoding='utf-8') as f:
        map.get_root().html.add_child(
            folium.Element(f'<script>{f.read()}</script>')
        )

inject_js(map, 'static/js/map_init.js')
inject_js(map, 'static/js/routes.js')

# -- Inject route data
colors_js     = json.dumps(ROUTE_COLORS)
route_js_entries = []
for brgy_name, routes in all_routes.items():
    safe_name = brgy_name.replace("'", "\\'")
    route_js_entries.append(f"  '{safe_name}': {json.dumps(routes)}")

map.get_root().html.add_child(folium.Element(f"""
<script>
window.routeData   = {{\n{chr(44).join(route_js_entries)}\n}};
window.routeColors = {colors_js};
</script>
"""))

# -- Barangay markers
brgy_fg = folium.FeatureGroup(name='Barangays').add_to(map)

for _, row in barangays.iterrows():
    brgy_name = row['origin_barangay']
    routes    = all_routes.get(brgy_name, [])
    safe_name = brgy_name.replace("'", "\\'")

    cm = folium.CircleMarker(
        location=[row['origin_latitude'], row['origin_longitude']],
        radius=7,
        color='#185FA5',
        fill=True,
        fill_color='#378ADD',
        fill_opacity=0.85,
        tooltip=folium.Tooltip(build_tooltip(brgy_name, routes), sticky=True),
        popup=folium.Popup(build_barangay_popup(brgy_name, routes), max_width=340),
    )
    cm.add_to(brgy_fg)

    map.get_root().html.add_child(folium.Element(f"""
    <script>
    (function() {{
        var check = setInterval(function() {{
            if (window._map) {{
                clearInterval(check);
                window._map.eachLayer(function(layer) {{
                    if (layer.getLatLng) {{
                        var ll = layer.getLatLng();
                        if (
                            Math.abs(ll.lat - {row['origin_latitude']}) < 0.0001 &&
                            Math.abs(ll.lng - {row['origin_longitude']}) < 0.0001
                        ) {{
                            layer.on('click', function() {{
                                showRoutes('{safe_name}');
                            }});
                        }}
                    }}
                }});
            }}
        }}, 200);
    }})();
    </script>
    """))

# -- University markers + Legend
add_university_markers(map, universities)
add_legend(map)
folium.LayerControl().add_to(map)

# -- CSV export
csv_records = []
for brgy_name, routes in all_routes.items():
    for r in routes:
        csv_records.append({
            'Barangay':      brgy_name,
            'University':    r['university'],
            'Distance (km)': r['distance_km'],
            'Time (mins)':   r['duration_min'],
            'Rides':         r['travel_label'],
        })

commute_df = pd.DataFrame(csv_records).sort_values(
    by=['Barangay', 'Time (mins)']
).reset_index(drop=True)

commute_df.to_csv('output/pozorrubio_commute_matrix.csv', index=False)
print(f"CSV saved — {len(commute_df)} rows")

map.save('output/pozorrubio_interactive.html')
print("Map saved to 'output/pozorrubio_interactive.html'")
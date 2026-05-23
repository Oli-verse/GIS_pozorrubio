import folium
import pandas as pd
import branca
import requests
import json
import time

'''
Updated map of Pozorrubio, Philippines.
- Hover tooltip shows nearest university instantly
- Click barangay to open scrollable popup (fixed height, all universities)
- All routes drawn on click (driving profile)
- Click map background to clear routes

AI agents used:
Google Gemini - Research and Implementation
Claude - Logic and debugging
Copilot - Code completion
'''

OSRM_BASE = "http://router.project-osrm.org"

# Load Dataframes 

barangays    = pd.read_csv('data/barangay_coords.csv')
universities = pd.read_csv('data/university_coords.csv')
travels = pd.read_csv('data/brgy_univ_matrix_db.csv')

# OSRM helper 

def get_route(origin_lon, origin_lat, dest_lon, dest_lat):
    url = (
        f"{OSRM_BASE}/route/v1/driving/"          
        f"{origin_lon},{origin_lat};{dest_lon},{dest_lat}"
        f"?overview=full&geometries=geojson&steps=false"
    )
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        if data["code"] != "Ok":
            return None, None, None
        leg = data["routes"][0]
        return leg["duration"], leg["distance"], leg["geometry"]["coordinates"]
    except requests.RequestException as e:
        print(f"  OSRM error: {e}")
        return None, None, None

merged = travels.merge(
    universities[['university_id', 'university_name']],
    on='university_id',
    how='left'
)

def label_travel(row):
    if row['travel_count'] == 0:
        return 'Remote'
    elif pd.isna(row['travel_count']):
        return '-'
    else:
        return f"{int(row['travel_count'])} ride{'s' if row['travel_count'] > 1 else ''}"

merged['travel_label'] = merged.apply(label_travel, axis=1)

travel_lookup = {
    (r['barangay_name'], r['university_name']): r['travel_label']
    for _, r in merged.iterrows()
}

# Pre-compute ALL barangay → university routes 

print("Pre-computing all barangay → university routes...")
all_routes = {}

for i, (_, brgy) in enumerate(barangays.iterrows()):
    brgy_name = brgy['origin_barangay']
    print(f"  [{i+1}/{len(barangays)}] {brgy_name}")
    all_routes[brgy_name] = []

    for _, uni in universities.iterrows():
        dur, dist, coords = get_route(
            brgy['origin_longitude'], brgy['origin_latitude'],
            uni['uni_longitude'],    uni['uni_latitude']
        )
        if dur is not None:
            uni_name = uni['university_name']
            all_routes[brgy_name].append({
                'university':   uni['university_name'],
                'duration_min': round(dur / 60, 1),
                'distance_km':  round(dist / 1000, 2),
                'coords':       [[c[1], c[0]] for c in coords],
                'travel_label': travel_lookup.get((brgy_name, uni_name), '-'),
                'is_remote':    travel_lookup.get((brgy_name, uni_name), '-') == 'Remote',
            })
        time.sleep(0.05)

    # Sort by duration so shortest is always first
    all_routes[brgy_name].sort(key=lambda x: x['duration_min'])

print("Routing complete!\n")

# Load and normalize GeoJSON 

def normalize_name(name):
    try:
        return name.encode('latin-1').decode('utf-8')
    except:
        return name

with open('data/bgysubmuns-municity-105530000.0.1.json', encoding='utf-8') as f:
    geo = json.load(f)

for feature in geo['features']:
    feature['properties']['adm4_en'] = normalize_name(feature['properties']['adm4_en'])

# Build map 

ROUTE_COLORS = ['#1D9E75', '#378ADD', '#E06C2B', '#9B59B6',
                '#E74C3C', '#F1C40F', '#1ABC9C', '#E67E22',
                '#2ECC71', '#3498DB', '#9B59B6', '#E91E63',
                '#00BCD4', '#FF5722', '#607D8B', '#795548',
                '#8BC34A', '#FF9800', '#673AB7', '#009688']

map = folium.Map(location=[16.11, 120.54], zoom_start=13, tiles='CartoDB positron')

# Municipality boundary
folium.GeoJson(
    geo,
    name='Pozorrubio boundary',
    style_function=lambda x: {
        'color':       'black',
        'weight':      2,
        'fillColor':   'yellow',
        'fillOpacity': 0.1,
    }
).add_to(map)

# JavaScript 

route_js_entries = []
for brgy_name, routes in all_routes.items():
    routes_json = json.dumps(routes)
    safe_name = brgy_name.replace("'", "\\'")
    route_js_entries.append(f"  '{safe_name}': {routes_json}")

route_data_js  = "{\n" + ",\n".join(route_js_entries) + "\n}"
colors_js      = json.dumps(ROUTE_COLORS)

custom_js = f"""
<script>
var routeData   = {route_data_js};
var routeColors = {colors_js};
var activePolylines = [];

function clearRoutes() {{
    activePolylines.forEach(function(p) {{ p.remove(); }});
    activePolylines = [];
}}

function showRoutes(barangayName) {{
    clearRoutes();
    var routes = routeData[barangayName];
    if (!routes || routes.length === 0) return;

    // Draw ALL routes, shortest on top
    var reversed = routes.slice().reverse();
    reversed.forEach(function(route, idx) {{
        var actualIdx = routes.length - 1 - idx;
        var color     = routeColors[actualIdx % routeColors.length];
        var isShortest = actualIdx === 0;

        var polyline = L.polyline(route.coords, {{
            color:     color,
            weight:    isShortest ? 5 : 2.5,
            opacity:   isShortest ? 1.0 : 0.55,
            dashArray: isShortest ? null : '5, 7',
        }}).addTo(window._map);

        activePolylines.push(polyline);
    }});
}}

document.addEventListener('DOMContentLoaded', function() {{
    setTimeout(function() {{
        window._map = Object.values(window).find(
            v => v && v._container && v.setView
        );
        if (window._map) {{
            window._map.on('click', function(e) {{
                if (!e.originalEvent.target.classList.contains('leaflet-interactive')) {{
                    clearRoutes();
                }}
            }});
        }}
    }}, 500);
}});
</script>
"""

map.get_root().html.add_child(folium.Element(custom_js))

# Barangay markers 

brgy_fg = folium.FeatureGroup(name='Barangays').add_to(map)

for _, row in barangays.iterrows():
    brgy_name = row['origin_barangay']
    routes    = all_routes.get(brgy_name, [])
    safe_name = brgy_name.replace("'", "\\'")

    # ── Tooltip: nearest university on hover ──
    if routes:
        nearest      = routes[0]
        tooltip_text = (
            f"<b>📍 {brgy_name}</b><br>"
            f"Nearest: <b>{nearest['university']}</b><br>"
            f"🚗 {nearest['distance_km']} km · {nearest['duration_min']} min"
        )
    else:
        tooltip_text = f"📍 {brgy_name}"

    # Popup: fixed-size scrollable box, all universities 
    if routes:
        all_rows = ""
        for idx, r in enumerate(routes):
            color     = ROUTE_COLORS[idx % len(ROUTE_COLORS)]
            is_remote = r.get('is_remote', False)
            bg        = "#f9f9f9" if is_remote else ("#f9fffe" if idx == 0 else "white")
            label_color = "#aaa" if is_remote else "#444"

            dist_cell = "—" if is_remote else f"{r['distance_km']} km"
            time_cell = "—" if is_remote else f"{r['duration_min']} min"
            dot_color = "#ccc" if is_remote else color

            all_rows += f"""
            <tr style="border-bottom:1px solid #f0f0f0; background:{bg};">
                <td style="padding:5px 6px; color:{label_color};
                        font-style:{'italic' if is_remote else 'normal'};">
                    <span style="color:{dot_color}; font-size:14px;">●</span>
                    &nbsp;{r['university']}
                </td>
                <td style="padding:5px 8px; text-align:center;
                        white-space:nowrap; color:{label_color};">
                    {dist_cell}
                </td>
                <td style="padding:5px 8px; text-align:center;
                        white-space:nowrap; color:{label_color};">
                    {time_cell}
                </td>
                <td style="padding:5px 8px; text-align:center;
                        white-space:nowrap; color:{label_color}; font-size:11px;">
                    {r['travel_label']}
                </td>
            </tr>
            """

        popup_html = f"""
        <div style="font-family:Arial,sans-serif; width:310px;">

            <!-- Fixed header -->
            <div style="background:#185FA5; color:white;
                        padding:8px 12px; border-radius:4px 4px 0 0;
                        position:sticky; top:0;">
                <b>📍 {brgy_name}</b>
                <span style="font-size:10px; opacity:0.8; float:right;
                             margin-top:2px;">
                    🚗 driving · {len(routes)} universities
                </span>
            </div>

            <!-- Scrollable table -->
            <div style="max-height:220px; overflow-y:auto;
                        border:1px solid #e0e0e0; border-top:none;
                        border-radius:0 0 4px 4px;">
                <table style="border-collapse:collapse;
                              width:100%; font-size:12px;">
                    <thead style="position:sticky; top:0; z-index:1;">
                        <tr style="background:#f0f4f8;">
                            <th style="padding:4px 6px; text-align:left;
                                       font-weight:600; color:#555;
                                       border-bottom:1px solid #ddd;">
                                University
                            </th>
                            <th style="padding:4px 8px; font-weight:600;
                                       color:#555; border-bottom:1px solid #ddd;">
                                km
                            </th>
                            <th style="padding:4px 8px; font-weight:600;
                                       color:#555; border-bottom:1px solid #ddd;">
                                min
                            </th>
                            <th style="padding:4px 8px; font-weight:600;
                                    color:#555; border-bottom:1px solid #ddd;">
                                rides
                            </th>
                        </tr>
                    </thead>
                    <tbody>
                        {all_rows}
                    </tbody>
                </table>
            </div>

            <!-- Footer -->
            <div style="font-size:10px; color:#aaa; padding:5px 6px;
                        text-align:right;">
                ⭐ shortest &nbsp;|&nbsp; scroll for more &nbsp;|&nbsp;
                click map to clear routes
            </div>

        </div>
        """
    else:
        popup_html = f"<b>{brgy_name}</b><br><i>No routes found</i>"

    cm = folium.CircleMarker(
        location=[row['origin_latitude'], row['origin_longitude']],
        radius=7,
        color='#185FA5',
        fill=True,
        fill_color='#378ADD',
        fill_opacity=0.85,
        tooltip=folium.Tooltip(tooltip_text, sticky=True),
        popup=folium.Popup(popup_html, max_width=340),
    )
    cm.add_to(brgy_fg)

    # Per-marker click JS
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

#  University markers 

uni_fg = folium.FeatureGroup(name='Universities').add_to(map)

for _, row in universities.iterrows():
    folium.Marker(
        location=[row['uni_latitude'], row['uni_longitude']],
        tooltip=folium.Tooltip(f"🎓 {row['university_name']}", sticky=True),
        popup=folium.Popup(
            f"<b>🎓 {row['university_name']}</b>", max_width=200
        ),
        icon=folium.Icon(color='red', icon='graduation-cap', prefix='fa'),
    ).add_to(uni_fg)

# Legend 

legend_html = '''
{% macro html(this, kwargs) %}
<div style="position:fixed; bottom:50px; left:50px; width:210px;
     border:1px solid #ccc; z-index:9999; font-size:12px;
     background:white; opacity:0.93; padding:10px 14px;
     border-radius:6px; box-shadow:0 2px 6px rgba(0,0,0,0.15);">
  <b style="font-size:13px;">Legend</b><br><br>
  <i class="fa fa-circle" style="color:#378ADD"></i>
  &nbsp;Barangay<br>
  <span style="font-size:10px; color:#888; margin-left:16px;">
    hover = nearest uni<br>
    <span style="margin-left:2px;">click = all routes</span>
  </span><br><br>
  <i class="fa fa-graduation-cap" style="color:red"></i>
  &nbsp;University<br><br>
  <span style="color:#1D9E75; font-size:15px;">━</span>
  &nbsp;Shortest route ⭐<br>
  <span style="color:#888; font-size:15px; letter-spacing:-1px;">╌</span>
  &nbsp;Other routes<br><br>
  <small style="color:#aaa;">🚗 driving profile</small><br>
  <small style="color:#aaa;">click map to clear routes</small>
</div>
{% endmacro %}
'''

legend = branca.element.MacroElement()
legend._template = branca.element.Template(legend_html)
map.get_root().add_child(legend)

folium.LayerControl().add_to(map)

# Export full commute CSV matrix 

print("Exporting full commute matrix CSV...")

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

commute_df = pd.DataFrame(csv_records)

# Sort by barangay name, then by time ascending
commute_df = commute_df.sort_values(
    by=['Barangay', 'Time (mins)']
).reset_index(drop=True)

commute_df.to_csv('output/pozorrubio_commute_matrix.csv', index=False)

print(f"CSV saved to 'output/pozorrubio_commute_matrix.csv'")
print(f"Total rows: {len(commute_df)} "
      f"({len(barangays)} barangays × {len(universities)} universities)")
print(commute_df.to_string())

map.save('output/pozorrubio_interactive.html')
print("Map saved to 'output/pozorrubio_interactive.html'")
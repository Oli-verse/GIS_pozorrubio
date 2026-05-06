import folium
import pandas as pd
import branca
import json
from math import radians, sin, cos, sqrt, atan2

'''
Pozorrubio GIS - Socioeconomic Overlay Map
Radio button switcher for PSA choropleth layers:
  - Total Population
  - Avg Wealth
  - Pct College Grads
  - Pct Highschool Grads
  - Avg OFW
  - Avg Agri

AI agents used:
Google Gemini - Research and Implementation
Claude - Logic and debugging
Copilot - Code completion
'''

# Load Dataframe 

df = pd.read_csv('data/barangay_with_psa_data.csv')

# Load and normalize GeoJSON for Pozorrubio municipal boundary

def normalize_name(name):
    try:
        return name.encode('latin-1').decode('utf-8')
    except:
        return name

with open('data/bgysubmuns-municity-105530000.0.1.json', encoding='utf-8') as f:
    geo = json.load(f)

for feature in geo['features']:
    feature['properties']['adm4_en'] = normalize_name(
        feature['properties']['adm4_en']
    )

# Attach PSA data to GeoJSON features 

psa_lookup = df.set_index('origin_barangay').to_dict(orient='index')

for feature in geo['features']:
    name = feature['properties']['adm4_en']
    data = psa_lookup.get(name, {})
    feature['properties']['Total_Population']   = int(data.get('Total_Population', 0))
    feature['properties']['Avg_Wealth']         = round(float(data.get('Avg_Wealth', 0)), 4)
    feature['properties']['Pct_College_Grads']  = round(float(data.get('Pct_College_Grads', 0)), 2)
    feature['properties']['Pct_Highschool_Grads'] = round(float(data.get('Pct_Highschool_Grads', 0)), 2)
    feature['properties']['Avg_OFW']            = round(float(data.get('Avg_OFW', 0)), 4)
    feature['properties']['Avg_Agri']           = round(float(data.get('Avg_Agri', 0)), 4)

#  Color scales 

SCALES = {
    'Total_Population':    ['#ffffb2', '#fecc5c', '#fd8d3c', '#f03b20', '#bd0026'],
    'Avg_Wealth':          ['#ffffe5', '#d9f0a3', '#78c679', '#31a354', '#004529'],
    'Pct_College_Grads':   ['#f7fbff', '#c6dbef', '#6baed6', '#2171b5', '#084594'],
    'Pct_Highschool_Grads':['#f7fbff', '#c6dbef', '#6baed6', '#2171b5', '#084594'],
    'Avg_OFW':             ['#f7fcfd', '#bfd3e6', '#8c96c6', '#8856a7', '#810f7c'],
    'Avg_Agri':            ['#fff7ec', '#fdd49e', '#fc8d59', '#d7301f', '#7f0000'],
}

LABELS = {
    'Total_Population':     'Total Population',
    'Avg_Wealth':           'Avg Wealth Index',
    'Pct_College_Grads':    'College Grad Rate (%)',
    'Pct_Highschool_Grads': 'Highschool Grad Rate (%)',
    'Avg_OFW':              'OFW Rate',
    'Avg_Agri':             'Agricultural Dependency',
}

# Compute min/max per column for JS color bar labels
stats = {}
for col in SCALES:
    vals = df[col].dropna()
    stats[col] = {
        'min': round(float(vals.min()), 4),
        'max': round(float(vals.max()), 4),
    }

# Build one Choropleth per column 
# Each gets a unique Folium layer name so JS can find and toggle them

map = folium.Map(
    location=[16.11, 120.54],
    zoom_start=13,
    tiles='CartoDB positron'
)

# Municipality boundary — always visible
folium.GeoJson(
    geo,
    name='boundary',
    style_function=lambda x: {
        'color':       'black',
        'weight':      2,
        'fillColor':   'transparent',
        'fillOpacity': 0,
    }
).add_to(map)

# Build all choropleth layers and track their JS variable names
layer_ids = {}

for col, colors in SCALES.items():
    mn = stats[col]['min']
    mx = stats[col]['max']

    def make_style(column=col, color_list=colors, mn=mn, mx=mx):
        def style_fn(feature):
            value = feature['properties'].get(column, None)
            if value is None or mx == mn:
                fill = '#cccccc'
            else:
                ratio = (value - mn) / (mx - mn)
                idx   = min(int(ratio * len(color_list)), len(color_list) - 1)
                fill  = color_list[idx]
            return {
                'fillColor':   fill,
                'fillOpacity': 0.75,
                'color':       '#444',
                'weight':      0.8,
            }
        return style_fn

    layer = folium.GeoJson(
        geo,
        name=col,
        style_function=make_style(),
        tooltip=folium.GeoJsonTooltip(
            fields=['adm4_en', col],
            aliases=['Barangay:', LABELS[col] + ':'],
            sticky=True,
            style="font-family:Arial,sans-serif; font-size:12px;"
        )
    )
    layer.add_to(map)
    layer_ids[col] = layer.get_name()   # Folium JS variable name e.g. 'geojson_abc123'

# Radio panel + JS 

layer_ids_js = json.dumps(layer_ids)
scales_js    = json.dumps(SCALES)
stats_js     = json.dumps(stats)
labels_js    = json.dumps(LABELS)
cols_js      = json.dumps(list(SCALES.keys()))

radio_options = ""
for i, col in enumerate(SCALES.keys()):
    checked = 'checked' if i == 0 else ''
    radio_options += f"""
    <label style="display:block; margin-bottom:8px; cursor:pointer;">
        <input type="radio" name="overlay" value="{col}" {checked}
               onchange="switchLayer('{col}')"
               style="margin-right:6px;">
        {LABELS[col]}
    </label>
    """

radio_panel = f"""
<div id="overlay-panel" style="
    position: fixed;
    top: 80px;
    right: 10px;
    width: 220px;
    background: white;
    border: 1px solid #ccc;
    border-radius: 6px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.15);
    z-index: 9999;
    font-family: Arial, sans-serif;
    font-size: 13px;
    padding: 12px 14px;">

    <b style="font-size:13px; color:#333;">PSA Overlay</b>
    <hr style="margin:8px 0; border:none; border-top:1px solid #eee;">

    {radio_options}

    <hr style="margin:10px 0; border:none; border-top:1px solid #eee;">

    <!-- Color bar -->
    <div id="colorbar-wrap">
        <div id="colorbar-label"
             style="font-size:10px; color:#888; margin-bottom:4px;"></div>
        <div id="colorbar"
             style="height:10px; border-radius:3px; margin-bottom:4px;"></div>
        <div style="display:flex; justify-content:space-between;
                    font-size:10px; color:#555;">
            <span id="cb-min"></span>
            <span id="cb-max"></span>
        </div>
    </div>

</div>

<script>
var layerIds = {layer_ids_js};
var scales   = {scales_js};
var stats    = {stats_js};
var labels   = {labels_js};
var cols     = {cols_js};

var activeCol = cols[0];

function updateColorBar(col) {{
    var colors = scales[col];
    var mn     = stats[col].min;
    var mx     = stats[col].max;

    document.getElementById('colorbar-label').textContent = labels[col];
    document.getElementById('colorbar').style.background  =
        'linear-gradient(to right, ' + colors.join(',') + ')';
    document.getElementById('cb-min').textContent = mn.toLocaleString();
    document.getElementById('cb-max').textContent = mx.toLocaleString();
}}

function switchLayer(col) {{
    if (!window._map) return;

    // Remove all choropleth layers
    cols.forEach(function(c) {{
        var layerVar = window[layerIds[c]];
        if (layerVar && window._map.hasLayer(layerVar)) {{
            window._map.removeLayer(layerVar);
        }}
    }});

    // Add selected layer
    var target = window[layerIds[col]];
    if (target) {{
        window._map.addLayer(target);
    }}

    activeCol = col;
    updateColorBar(col);
}}

document.addEventListener('DOMContentLoaded', function() {{
    setTimeout(function() {{
        window._map = Object.values(window).find(
            function(v) {{ return v && v._container && v.setView; }}
        );

        if (window._map) {{
            // Remove all layers except the first
            cols.forEach(function(c, i) {{
                var layerVar = window[layerIds[c]];
                if (layerVar && i !== 0) {{
                    window._map.removeLayer(layerVar);
                }}
            }});

            // Initialize color bar with first column
            updateColorBar(cols[0]);
        }}
    }}, 600);
}});
</script>
"""

map.get_root().html.add_child(folium.Element(radio_panel))

map.save('output/pozorrubio_socioeconomic.html')
print("Map saved to 'output/pozorrubio_socioeconomic.html'")
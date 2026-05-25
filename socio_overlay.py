import folium
import pandas as pd
import json

from data_loader.loader  import load_psa, load_geojson, attach_psa_to_geojson
from map_builder.layers  import add_boundary, add_choropleth_layers

'''
Pozorrubio GIS - Socioeconomic Overlay Map
AI agents used:
Google Gemini - Research and Implementation
Claude - Logic and debugging
Copilot - Code completion
'''

# -- Data
df  = load_psa()
geo = load_geojson()
geo = attach_psa_to_geojson(geo, df)

SCALES = {
    'Total_Population':     ['#ffffb2', '#fecc5c', '#fd8d3c', '#f03b20', '#bd0026'],
    'Avg_Wealth':           ['#ffffe5', '#d9f0a3', '#78c679', '#31a354', '#004529'],
    'Pct_College_Grads':    ['#f7fbff', '#c6dbef', '#6baed6', '#2171b5', '#084594'],
    'Pct_Highschool_Grads': ['#f7fbff', '#c6dbef', '#6baed6', '#2171b5', '#084594'],
    'Avg_OFW':              ['#f7fcfd', '#bfd3e6', '#8c96c6', '#8856a7', '#810f7c'],
    'Avg_Agri':             ['#fff7ec', '#fdd49e', '#fc8d59', '#d7301f', '#7f0000'],
}

LABELS = {
    'Total_Population':     'Total Population',
    'Avg_Wealth':           'Avg Wealth Index',
    'Pct_College_Grads':    'College Grad Rate (%)',
    'Pct_Highschool_Grads': 'Highschool Grad Rate (%)',
    'Avg_OFW':              'OFW Rate',
    'Avg_Agri':             'Agricultural Dependency',
}

stats = {}
for col in SCALES:
    vals = df[col].dropna()
    stats[col] = {
        'min': round(float(vals.min()), 4),
        'max': round(float(vals.max()), 4),
    }

# -- Map
map = folium.Map(location=[16.11, 120.54], zoom_start=13, tiles='CartoDB positron')
add_boundary(map, geo)
layer_ids = add_choropleth_layers(map, geo, SCALES, LABELS, stats)

# -- Radio panel
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

# -- Inject radio panel JS (read from file)
with open('static/js/map_init.js', encoding='utf-8') as f:
    map.get_root().html.add_child(
        folium.Element(f'<script>{f.read()}</script>')
    )

radio_panel = f"""
<div id="overlay-panel" style="
    position:fixed; top:80px; right:10px; width:220px;
    background:white; border:1px solid #ccc; border-radius:6px;
    box-shadow:0 2px 6px rgba(0,0,0,0.15); z-index:9999;
    font-family:Arial,sans-serif; font-size:13px; padding:12px 14px;">
    <b style="font-size:13px; color:#333;">PSA Overlay</b>
    <hr style="margin:8px 0; border:none; border-top:1px solid #eee;">
    {radio_options}
    <hr style="margin:10px 0; border:none; border-top:1px solid #eee;">
    <div id="colorbar-wrap">
        <div id="colorbar-label" style="font-size:10px; color:#888; margin-bottom:4px;"></div>
        <div id="colorbar" style="height:10px; border-radius:3px; margin-bottom:4px;"></div>
        <div style="display:flex; justify-content:space-between; font-size:10px; color:#555;">
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

function updateColorBar(col) {{
    var colors = scales[col];
    document.getElementById('colorbar-label').textContent = labels[col];
    document.getElementById('colorbar').style.background  =
        'linear-gradient(to right, ' + colors.join(',') + ')';
    document.getElementById('cb-min').textContent = stats[col].min.toLocaleString();
    document.getElementById('cb-max').textContent = stats[col].max.toLocaleString();
}}

function switchLayer(col) {{
    if (!window._map) return;
    cols.forEach(function(c) {{
        var lv = window[layerIds[c]];
        if (lv && window._map.hasLayer(lv)) window._map.removeLayer(lv);
    }});
    var target = window[layerIds[col]];
    if (target) window._map.addLayer(target);
    updateColorBar(col);
}}

document.addEventListener('DOMContentLoaded', function() {{
    setTimeout(function() {{
        window._map = Object.values(window).find(
            function(v) {{ return v && v._container && v.setView; }}
        );
        if (window._map) {{
            cols.forEach(function(c, i) {{
                var lv = window[layerIds[c]];
                if (lv && i !== 0) window._map.removeLayer(lv);
            }});
            updateColorBar(cols[0]);
        }}
    }}, 600);
}});
</script>
"""

map.get_root().html.add_child(folium.Element(radio_panel))
map.save('output/pozorrubio_socioeconomic.html')
print("Map saved to 'output/pozorrubio_socioeconomic.html'")
import folium
import branca
import json

ROUTE_COLORS = [
    '#1D9E75', '#378ADD', '#E06C2B', '#9B59B6',
    '#E74C3C', '#F1C40F', '#1ABC9C', '#E67E22',
    '#2ECC71', '#3498DB', '#9B59B6', '#E91E63',
    '#00BCD4', '#FF5722', '#607D8B', '#795548',
    '#8BC34A', '#FF9800', '#673AB7', '#009688'
]

def add_boundary(map, geo):
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

def add_university_markers(map, universities):
    uni_fg = folium.FeatureGroup(name='Universities').add_to(map)
    for _, row in universities.iterrows():
        folium.Marker(
            location=[row['uni_latitude'], row['uni_longitude']],
            tooltip=folium.Tooltip(row['university_name'], sticky=True),
            popup=folium.Popup(f"<b>{row['university_name']}</b>", max_width=200),
            icon=folium.Icon(color='red', icon='graduation-cap', prefix='fa'),
        ).add_to(uni_fg)

def add_legend(map):
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
      &nbsp;Shortest route<br>
      <span style="color:#888; font-size:15px; letter-spacing:-1px;">╌</span>
      &nbsp;Other routes<br><br>
      <small style="color:#aaa;">driving profile</small><br>
      <small style="color:#aaa;">click map to clear routes</small>
    </div>
    {% endmacro %}
    '''
    legend = branca.element.MacroElement()
    legend._template = branca.element.Template(legend_html)
    map.get_root().add_child(legend)

def add_choropleth_layers(map, geo, SCALES, LABELS, stats):
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
        layer_ids[col] = layer.get_name()
    return layer_ids
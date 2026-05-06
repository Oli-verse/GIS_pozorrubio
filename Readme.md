# Pozorrubio GIS (Geospatial Data)

Geospatial analysis of Pozorrubio, Pangasinan, Philippines. Maps barangay locations, university access via driving routes, and PSA 2020 socioeconomic indicators as interactive choropleth overlays.


### Output

**pozorrubio_commute_matrix.csv** - Dataset for all possible commute from 34 barangays to 20 universities, total of 680 rows. 

**pozorrubio_interactive.html** - Click-to-route map — click any barangay to show all university routes, and commute time

**pozorrubio_socioeconomic.html** - Socioeconomic overlay — PSA 2020 choropleth with radio button switcher


### Project Structure
```
pozorrubio_gis/
├── data/
│   ├── barangay_coords.csv
│   ├── university_coords.csv
│   ├── pozorrubio_psa_data.csv
│   ├── barangay_with_psa_data.csv
│   └── bgysubmuns-municity-105530000.0.1.json
├── notebook/
│   ├──pozorrubio.ipynb
├── output/
│   ├── pozorrubio_commute_matrix.csv
│   ├── pozorrubio_interactive.html
│   ├── pozorrubio_socioeconomic.html
├── pozorrubio.py
├── socio_overlay.py
├── requirements.txt
├── gdal-3.12.2-cp312-cp312-win_arm64.whl
└── README.md
```
### Requirements
```
folium
branca
pandas
numpy
requests
geopandas
shapely
pyproj
osrm
polyline
```

**Install with:**
pip install -r requirements.txt

### AI Tools Used

Google Gemini - Research and Implementations
Claude - Code Review and Debugging
Github Copilot - Inline code completion

### Setup

1. Create virtual environment (.venv)

2. Install Dependencies
```
    - pip install -r requirements.txt
```
**Note:** If pip install fails on GDAL, download the prebuilt wheel for your Python version from https://github.com/cgohlke/geospatial-wheels/releases and install it manually first.

3. Run a script

### Interactive click-to-route map
python pozorrubio.py
### Socioeconomic overlay choropleth map
python socio_overlay.py


### Data Sources
```
barangay_coords.csv   - Manually geocoded barangay centroids

university_coords.csv - Manually geocoded university locations

bgysubmuns-municity-105530000.0.1.json - GADM / PhilGIS municipal boundary GeoJSON

barangay_with_psa_data.csv - PSA 2020 Census — population, wealth, education, OFW, agri

pozorrubio_psa_data.csv - PSA 2020 Census - Common Household Questionaire
```

### OSRM Routing
```
Scripts use the public OSRM demo server by default — no local installation needed.

OSRM_BASE = "http://router.project-osrm.org"

To use a local instance, replace the URL with your server address and start osrm-routed with a preprocessed Philippines PBF extract.
```

### PSA Socioeconomic Indicators

The socioeconomic map (socio_overlay.py) supports six switchable layers:
```
**Column**                         **Colors**
Total_Population(Demographic)      Yellow → Red
Avg_Wealth(Income)                 Yellow → Green
Pct_College_Grads(Education)       Light → Dark Blue
Pct_Highschool_Grads(Education)    Light → Dark Blue
Avg_OFW(Remittance)                Light → Purple
Avg_Agri(Livelihood)               Light → Dark Red
```





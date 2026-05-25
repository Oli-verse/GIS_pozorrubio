import pandas as pd
import json

def normalize_name(name):
    try:
        return name.encode('latin-1').decode('utf-8')
    except UnicodeDecodeError:
        return name
    
def load_barangays():
    return pd.read_csv('data/barangay_coords.csv')

def load_universities():
    return pd.read_csv('data/university_coords.csv')

def load_travels():
    return pd.read_csv('data/brgy_univ_matrix_db.csv')

def load_psa():
    return pd.read_csv('data/barangay_with_psa_data.csv')

def load_geojson():
    with open('data/bgysubmuns-municity-105530000.0.1.json', encoding='utf-8') as f:
        geo = json.load(f)
    for feature in geo['features']:
        feature['properties']['adm4_en'] = normalize_name(
            feature['properties']['adm4_en']
        )
    return geo

def attach_psa_to_geojson(geo, df):
    psa_lookup = df.set_index('origin_barangay').to_dict(orient='index')
    for feature in geo['features']:
        name = feature['properties']['adm4_en']
        data = psa_lookup.get(name, {})
        feature['properties']['Total_Population']     = int(data.get('Total_Population', 0))
        feature['properties']['Avg_Wealth']           = round(float(data.get('Avg_Wealth', 0)), 4)
        feature['properties']['Pct_College_Grads']    = round(float(data.get('Pct_College_Grads', 0)), 2)
        feature['properties']['Pct_Highschool_Grads'] = round(float(data.get('Pct_Highschool_Grads', 0)), 2)
        feature['properties']['Avg_OFW']              = round(float(data.get('Avg_OFW', 0)), 4)
        feature['properties']['Avg_Agri']             = round(float(data.get('Avg_Agri', 0)), 4)
    return geo
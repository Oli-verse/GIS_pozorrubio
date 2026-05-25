import requests
import time
import pandas as pd

OSRM_BASE = "http://router.project-osrm.org"

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

def build_travel_lookup(travels, universities):
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

    return {
        (r['barangay_name'], r['university_name']): r['travel_label']
        for _, r in merged.iterrows()
    }

def compute_all_routes(barangays, universities, travel_lookup):
    print("Pre-computing all barangay to university routes...")
    all_routes = {}

    for i, (_, brgy) in enumerate(barangays.iterrows()):
        brgy_name = brgy['origin_barangay']
        print(f"  [{i+1}/{len(barangays)}] {brgy_name}")
        all_routes[brgy_name] = []

        for _, uni in universities.iterrows():
            if pd.isna(uni['uni_latitude']) or pd.isna(uni['uni_longitude']):
                print(f"  Skipping {uni['university_name']} — missing coordinates")
                continue

            dur, dist, coords = get_route(
                brgy['origin_longitude'], brgy['origin_latitude'],
                uni['uni_longitude'],    uni['uni_latitude']
            )
            if dur is not None:
                uni_name = uni['university_name']
                all_routes[brgy_name].append({
                    'university':   uni_name,
                    'duration_min': round(dur / 60, 1),
                    'distance_km':  round(dist / 1000, 2),
                    'coords':       [[c[1], c[0]] for c in coords],
                    'travel_label': travel_lookup.get((brgy_name, uni_name), '-'),
                    'is_remote':    travel_lookup.get((brgy_name, uni_name), '-') == 'Remote',
                })
            time.sleep(0.05)

        all_routes[brgy_name].sort(key=lambda x: x['duration_min'])

    print("Routing complete!\n")
    return all_routes
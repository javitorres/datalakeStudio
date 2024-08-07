
mapbox_access_token = None

def init(secrets):
    print("Initializing maps service...")
    print("Reading Mapbox API key")
    global mapbox_access_token
    mapbox_access_token = secrets["mapbox_access_token"]
    if (mapbox_access_token is None):
        print("Mapbox API key not found")

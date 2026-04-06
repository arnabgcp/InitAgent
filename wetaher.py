import requests

def get_weather(city: str) -> dict:
    """
    Retrieves the current temperature for a specified city.
    Args:
        city: The name of the city (e.g., "London", "Pune").
    Returns:
        A dictionary containing the temperature or an error message.
    """
    try:
        # Step 1: Geocoding (Convert city to Lat/Lon)
        geo_url = "https://geocoding-api.open-meteo.com"
        geo_params = {"name": city, "count": 1, "language": "en", "format": "json"}
        geo_resp = requests.get(geo_url, params=geo_params).json()

        if "results" not in geo_resp:
            return {"status": "error", "message": f"City '{city}' not found."}

        location = geo_resp["results"][0]
        lat, lon = location["latitude"], location["longitude"]

        # Step 2: Weather Fetch
        weather_url = "https://api.open-meteo.com"
        weather_params = {
            "latitude": lat, 
            "longitude": lon, 
            "current_weather": True
        }
        weather_resp = requests.get(weather_url, params=weather_params).json()
        temp = weather_resp["current_weather"]["temperature"]

        return {
            "status": "success",
            "city": city,
            "temperature": f"{temp}°C"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
    
def get_wthr(city: str) -> str:
    """
    Retrieves the current temperature for a specified city.
    
    Args:
        city: The name of the city (e.g., 'London', 'New York').
    
    Returns:
        A string describing the current temperature in Celsius.
    """
    try:
        # Geocoding: Get coordinates
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en&format=json"
        geo_res = requests.get(geo_url).json()
        
        if "results" not in geo_res:
            return f"Could not find coordinates for {city}."
            
        lat = geo_res["results"][0]["latitude"]
        lon = geo_res["results"][0]["longitude"]

        # Weather: Get temperature
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        weather_res = requests.get(weather_url).json()
        
        temp = weather_res["current_weather"]["temperature"]
        return f"The current temperature in {city} is {temp}°C."
    except Exception as e:
        return f"Error retrieving weather: {str(e)}"
    
wth=get_wthr("Kolkata")
print(wth)
#
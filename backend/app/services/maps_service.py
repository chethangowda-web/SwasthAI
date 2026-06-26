import requests
from typing import List, Dict, Any, Optional
from app.core.config import settings

class GoogleMapsService:
    def __init__(self):
        self.api_key = settings.GOOGLE_MAPS_API_KEY
        self.base_url = "https://maps.googleapis.com/maps/api"

    def get_distance_matrix(
        self, 
        origins: List[str], 
        destinations: List[str], 
        mode: str = "driving"
    ) -> Optional[Dict[str, Any]]:
        """
        Calls Google Distance Matrix API to get transit distance and duration.
        origins/destinations format: ["lat,lng", "lat,lng"] or ["Village Name, Region"]
        """
        if not self.api_key:
            return None

        url = f"{self.base_url}/distancematrix/json"
        params = {
            "origins": "|".join(origins),
            "destinations": "|".join(destinations),
            "mode": mode,
            "key": self.api_key
        }
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Distance Matrix API request failed: {str(e)}")
            return None

    def optimize_route(self, origin: str, waypoints: List[str], destination: str) -> Optional[Dict[str, Any]]:
        """
        Calls Google Directions API with route optimization enabled.
        Reorders waypoints to minimize total transit distance.
        """
        if not self.api_key or not waypoints:
            return None

        url = f"{self.base_url}/directions/json"
        params = {
            "origin": origin,
            "destination": destination,
            "waypoints": f"optimize:true|{'|'.join(waypoints)}",
            "key": self.api_key
        }
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") == "OK":
                route = data["routes"][0]
                # The optimized order of waypoints is returned in route['waypoint_order']
                waypoint_order = route.get("waypoint_order", [])
                legs = route.get("legs", [])
                
                return {
                    "optimized_waypoint_order": waypoint_order,
                    "legs": [
                        {
                            "start_address": leg["start_address"],
                            "end_address": leg["end_address"],
                            "distance": leg["distance"]["text"],
                            "duration": leg["duration"]["text"],
                            "duration_seconds": leg["duration"]["value"]
                        } for leg in legs
                    ],
                    "total_distance": sum(leg["distance"]["value"] for leg in legs),
                    "total_duration_seconds": sum(leg["duration"]["value"] for leg in legs)
                }
            return None
        except Exception as e:
            print(f"Directions API Route Optimization failed: {str(e)}")
            return None

    def find_nearest_worker(
        self, 
        worker_origins: List[Dict[str, Any]], 
        target_village_coords: str
    ) -> Optional[Dict[str, Any]]:
        """
        Finds the nearest worker to a target village based on transit times.
        worker_origins: [{"worker_id": UUID, "worker_name": str, "coords": "lat,lng"}]
        """
        if not worker_origins:
            return None

        origins = [w["coords"] for w in worker_origins]
        destinations = [target_village_coords]
        
        matrix_data = self.get_distance_matrix(origins, destinations)
        
        # Fallback to straight-line Euclidean distance if API key is missing
        if not matrix_data or matrix_data.get("status") != "OK":
            dest_lat, dest_lng = map(float, target_village_coords.split(","))
            results = []
            for w in worker_origins:
                w_lat, w_lng = map(float, w["coords"].split(","))
                approx_dist = ((w_lat - dest_lat)**2 + (w_lng - dest_lng)**2)**0.5 * 111000
                results.append({
                    "worker_id": w["worker_id"],
                    "worker_name": w["worker_name"],
                    "distance_meters": int(approx_dist),
                    "duration_seconds": int(approx_dist / 10), # 10 m/s (~36km/h) speed
                    "is_mock": True
                })
            sorted_results = sorted(results, key=lambda x: x["distance_meters"])
            return {"nearest": sorted_results[0], "all_candidates": sorted_results}

        try:
            results = []
            rows = matrix_data["rows"]
            for idx, row in enumerate(rows):
                element = row["elements"][0]
                if element["status"] == "OK":
                    results.append({
                        "worker_id": worker_origins[idx]["worker_id"],
                        "worker_name": worker_origins[idx]["worker_name"],
                        "distance_meters": element["distance"]["value"],
                        "duration_seconds": element["duration"]["value"],
                        "is_mock": False
                    })
            if not results:
                return None
            sorted_results = sorted(results, key=lambda x: x["duration_seconds"])
            return {"nearest": sorted_results[0], "all_candidates": sorted_results}
        except Exception as e:
            print(f"Failed parsing Distance Matrix response: {str(e)}")
            return None

import logging
import requests
import os

import azure.functions as func

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def get_client_ip(req: func.HttpRequest) -> str:
    """
    Extracts the client IP address from the HttpRequest.
    """
    x_forwarded_for = req.headers.get('X-Forwarded-For')
    if x_forwarded_for:
        # X-Forwarded-For may contain multiple IPs; the first is the client's IP
        ip = x_forwarded_for.split(',')[0].strip()
        logger.info(f"Extracted IP from X-Forwarded-For: {ip}")
        return ip
    else:
        # Fallback to REMOTE_ADDR if X-Forwarded-For is not present
        remote_addr = req.headers.get('REMOTE_ADDR', '')
        logger.info(f"Extracted IP from REMOTE_ADDR: {remote_addr}")
        return remote_addr

def get_geolocation(ip: str) -> dict:
    """
    Retrieves geolocation information for the given IP address using ip-api.com.
    """
    if ip in ['::1', '127.0.0.1', 'localhost', '']:
        logger.warning("Cannot geolocate localhost or empty IP.")
        return {}
    
    try:
        response = requests.get(f"http://ip-api.com/json/{ip}")
        if response.status_code == 200:
            data = response.json()
            if data['status'] == 'success':
                location = {
                    "country": data.get("country", ""),
                    "region": data.get("regionName", ""),
                    "city": data.get("city", ""),
                    "lat": data.get("lat", ""),
                    "lon": data.get("lon", ""),
                    "query": data.get("query", ip)
                }
                logger.info(f"Geolocation data for IP {ip}: {location}")
                return location
            else:
                logger.warning(f"Geolocation API failed for IP {ip}: {data.get('message', 'No message')}")
                return {}
        else:
            logger.warning(f"Geolocation API request failed with status {response.status_code} for IP {ip}")
            return {}
    except Exception as e:
        logger.exception(f"Error calling Geolocation API for IP {ip}: {str(e)}")
        return {}

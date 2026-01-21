"""
IP Geolocation utility functions.

This module provides utilities for retrieving geolocation data for IP addresses
with built-in caching.
"""

import requests
import logging
from django.core.cache import cache

logger = logging.getLogger(__name__)

# Free IP Geolocation API
IPAPI_ENDPOINT = "https://ipapi.co/{ip}/json/"
GEOLOCATION_CACHE_TIMEOUT = 24 * 60 * 60  # 24 hours


def get_geolocation(ip_address):
    """
    Get geolocation data for an IP address with caching.

    Args:
        ip_address (str): The IP address to geolocate.

    Returns:
        dict: Dictionary with 'country' and 'city' keys, or empty if lookup fails.
    """
    # Check cache first
    cache_key = f"geo_{ip_address}"
    cached_result = cache.get(cache_key)

    if cached_result is not None:
        logger.debug(f"Geolocation cache hit for {ip_address}")
        return cached_result

    # Skip localhost and private IPs
    if _is_private_ip(ip_address):
        result = {'country': 'Local', 'city': 'Local'}
        cache.set(cache_key, result, GEOLOCATION_CACHE_TIMEOUT)
        return result

    # Fetch from API
    try:
        response = requests.get(
            IPAPI_ENDPOINT.format(ip=ip_address),
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            result = {
                'country': data.get('country_name', 'Unknown'),
                'city': data.get('city', 'Unknown')
            }
            # Cache the result for 24 hours
            cache.set(cache_key, result, GEOLOCATION_CACHE_TIMEOUT)
            logger.info(f"Geolocation retrieved for {ip_address}: {result}")
            return result
        else:
            logger.warning(
                f"Geolocation API error for {ip_address}: {response.status_code}")

    except requests.RequestException as e:
        logger.error(f"Geolocation request failed for {ip_address}: {str(e)}")
    except Exception as e:
        logger.error(f"Geolocation parsing error for {ip_address}: {str(e)}")

    # Return default on error
    default_result = {'country': 'Unknown', 'city': 'Unknown'}
    cache.set(cache_key, default_result, GEOLOCATION_CACHE_TIMEOUT)
    return default_result


def _is_private_ip(ip_address):
    """
    Check if an IP address is private/local.

    Args:
        ip_address (str): The IP address to check.

    Returns:
        bool: True if the IP is private/local, False otherwise.
    """
    private_ranges = [
        '127.0.0.1',
        '127.',
        '192.168.',
        '10.',
        '172.16.',
        '172.17.',
        '172.18.',
        '172.19.',
        '172.20.',
        '172.21.',
        '172.22.',
        '172.23.',
        '172.24.',
        '172.25.',
        '172.26.',
        '172.27.',
        '172.28.',
        '172.29.',
        '172.30.',
        '172.31.',
        '::1',
        'localhost',
    ]

    return any(ip_address.startswith(prefix) for prefix in private_ranges)

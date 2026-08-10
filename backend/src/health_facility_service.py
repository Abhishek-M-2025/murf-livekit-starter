import os
import json
import logging
import aiohttp
from typing import Any, Dict, List

logger = logging.getLogger("agent.health_facility_service")

# Resolve path for local fallback dataset
FACILITIES_JSON_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "health_facilities.json"
)

# Load local fallback dataset once at module load
_local_facilities: Dict[str, List[Dict[str, str]]] = {}
try:
    if os.path.exists(FACILITIES_JSON_PATH):
        with open(FACILITIES_JSON_PATH, "r", encoding="utf-8") as f:
            _local_facilities = json.load(f)
        logger.info(
            "Successfully loaded %d districts from local health facilities dataset.",
            len(_local_facilities),
        )
    else:
        logger.warning(
            "Local health facilities dataset not found at %s",
            FACILITIES_JSON_PATH,
        )
except Exception:
    logger.exception("Failed to load local health facilities dataset")


def normalize_district(district: str) -> str:
    """Normalize district/location names to match fallback keys and API queries."""
    if not district:
        return ""
    cleaned = district.strip().lower()
    # Normalize common spelling variations
    if cleaned in ("bangalore", "bengaluru urban", "bengaluru rural"):
        return "bengaluru"
    if cleaned in ("calcutta", "kolkata"):
        return "kolkata"
    if cleaned in ("madras", "chennai"):
        return "chennai"
    if cleaned in ("bombay", "mumbai"):
        return "mumbai"
    return cleaned


async def get_nearest_facilities(district_input: str) -> Dict[str, Any]:
    """
    Search for the nearest health facilities in the given district/location.
    Tries the live data.gov.in API first if DATA_GOV_IN_API_KEY is configured.
    Otherwise, or if the API query fails/returns no results, falls back to the local dataset.
    """
    normalized = normalize_district(district_input)
    if not normalized:
        return {"source": "none", "facilities": []}

    api_key = os.getenv("DATA_GOV_IN_API_KEY")
    resource_id = os.getenv(
        "DATA_GOV_IN_RESOURCE_ID", "9ef84268-d588-465a-a308-a864a43d0070"
    )

    # 1. Try Live API if API Key is configured
    if api_key:
        logger.info(
            "Attempting live API lookup for district: %s (Key: %s***)",
            district_input,
            api_key[:5] if len(api_key) > 5 else "valid",
        )
        url = f"https://api.data.gov.in/resource/{resource_id}"
        params = {
            "api-key": api_key,
            "format": "json",
            "filters[district]": district_input.strip(),
            "limit": "5",
        }
        try:
            # Enforce a 5-second timeout for voice conversation latency limits
            timeout = aiohttp.ClientTimeout(total=5.0)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        records = data.get("records", [])
                        if records:
                            mapped_facilities = []
                            for r in records:
                                mapped_facilities.append(
                                    {
                                        "name": (
                                            r.get("facility_name")
                                            or r.get("hospital_name")
                                            or r.get("name")
                                            or "Government Health Facility"
                                        ),
                                        "type": (
                                            r.get("facility_type")
                                            or r.get("type")
                                            or "Government Facility"
                                        ),
                                        "district": (
                                            r.get("district")
                                            or r.get("District")
                                            or district_input
                                        ),
                                        "state": (
                                            r.get("state")
                                            or r.get("State")
                                            or ""
                                        ),
                                        "address": (
                                            r.get("address")
                                            or r.get("Address")
                                            or r.get("location")
                                            or "Address not specified"
                                        ),
                                    }
                                )
                            logger.info(
                                "Live API lookup succeeded. Found %d facilities.",
                                len(mapped_facilities),
                            )
                            return {
                                "source": "live",
                                "facilities": mapped_facilities,
                            }
                        else:
                            logger.warning(
                                "Live API returned empty records for district: %s",
                                district_input,
                            )
                    else:
                        logger.error(
                            "Live API returned error status: %d for URL: %s",
                            response.status,
                            url,
                        )
        except Exception as e:
            logger.error(
                "Live API query failed or timed out. Falling back to local data. Error: %s",
                str(e),
            )

    # 2. Fall back to local/static dataset
    logger.info("Performing local fallback lookup for district: %s", normalized)
    local_matches = _local_facilities.get(normalized, [])

    if local_matches:
        logger.info(
            "Found %d facilities in local database for: %s",
            len(local_matches),
            normalized,
        )
        return {"source": "local", "facilities": local_matches}

    logger.warning("No facilities found for: %s (local or live)", district_input)
    return {"source": "none", "facilities": []}

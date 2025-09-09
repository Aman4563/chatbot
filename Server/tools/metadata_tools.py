"""Metadata tools for user context and environment information."""

import asyncio
import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union
import httpx
import pytz
from zoneinfo import ZoneInfo
from .base import BaseTool


class TimezoneTool(BaseTool):
    """Tool for timezone detection and conversion."""
    
    def __init__(self):
        super().__init__("timezone_tool", "Detect and convert timezone information")
        self.category = "metadata"
        self.timezone_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl = 3600  # 1 hour
    
    async def execute(
        self,
        timezone_input: Optional[str] = None,
        ip_address: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Execute timezone detection and conversion."""
        try:
            # Try browser timezone first (highest priority)
            if timezone_input:
                return await self._process_browser_timezone(timezone_input)
            
            # Try IP-based timezone detection
            if ip_address:
                return await self._get_timezone_from_ip(ip_address)
            
            # Try coordinates-based timezone detection
            if latitude and longitude:
                return await self._get_timezone_from_coordinates(latitude, longitude)
            
            # Fallback to UTC
            return await self._get_utc_timezone()
            
        except Exception as e:
            return await self.handle_error(e)
    
    async def _process_browser_timezone(self, timezone_str: str) -> Dict[str, Any]:
        """Process timezone from browser Intl API."""
        try:
            # Validate timezone
            tz = ZoneInfo(timezone_str)
            current_time = datetime.now(tz)
            
            return {
                "status": "success",
                "timezone": {
                    "value": timezone_str,
                    "source": "browser-intl",
                    "confidence": 1.0,
                    "ttl_sec": 86400,  # 24 hours
                    "current_time": current_time.isoformat(),
                    "utc_offset": current_time.strftime("%z"),
                    "is_dst": current_time.dst() != None
                },
                "metadata": {
                    "detection_method": "browser_intl",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            }
        except Exception as e:
            # Fallback to UTC if browser timezone is invalid
            return await self._get_utc_timezone()
    
    async def _get_timezone_from_ip(self, ip_address: str) -> Dict[str, Any]:
        """Get timezone from IP address using free APIs."""
        cache_key = f"ip_{ip_address}"
        
        # Check cache first
        if cache_key in self.timezone_cache:
            cached_data = self.timezone_cache[cache_key]
            if time.time() - cached_data["timestamp"] < self.cache_ttl:
                return cached_data["data"]
        
        try:
            # Try ip-api.com (free, no key required)
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"http://ip-api.com/json/{ip_address}")
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "success":
                        timezone_str = data.get("timezone")
                        if timezone_str:
                            tz = ZoneInfo(timezone_str)
                            current_time = datetime.now(tz)
                            
                            result = {
                                "status": "success",
                                "timezone": {
                                    "value": timezone_str,
                                    "source": "ip-api",
                                    "confidence": 0.8,
                                    "ttl_sec": 10800,  # 3 hours
                                    "current_time": current_time.isoformat(),
                                    "utc_offset": current_time.strftime("%z"),
                                    "is_dst": current_time.dst() != None
                                },
                                "location": {
                                    "country": data.get("country"),
                                    "region": data.get("regionName"),
                                    "city": data.get("city"),
                                    "lat": data.get("lat"),
                                    "lon": data.get("lon")
                                },
                                "metadata": {
                                    "detection_method": "ip_geolocation",
                                    "ip_address": ip_address,
                                    "timestamp": datetime.now(timezone.utc).isoformat()
                                }
                            }
                            
                            # Cache the result
                            self.timezone_cache[cache_key] = {
                                "data": result,
                                "timestamp": time.time()
                            }
                            
                            return result
            
            # Fallback to UTC
            return await self._get_utc_timezone()
            
        except Exception as e:
            return await self._get_utc_timezone()
    
    async def _get_timezone_from_coordinates(self, lat: float, lon: float) -> Dict[str, Any]:
        """Get timezone from coordinates using timezonefinder."""
        try:
            from timezonefinder import TimezoneFinder
            
            tf = TimezoneFinder()
            timezone_str = tf.timezone_at(lat=lat, lng=lon)
            
            if timezone_str:
                tz = ZoneInfo(timezone_str)
                current_time = datetime.now(tz)
                
                return {
                    "status": "success",
                    "timezone": {
                        "value": timezone_str,
                        "source": "coordinates-timezonefinder",
                        "confidence": 0.95,
                        "ttl_sec": 86400,  # 24 hours
                        "current_time": current_time.isoformat(),
                        "utc_offset": current_time.strftime("%z"),
                        "is_dst": current_time.dst() != None
                    },
                    "metadata": {
                        "detection_method": "coordinates_timezonefinder",
                        "coordinates": {"lat": lat, "lon": lon},
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                }
            else:
                # Fallback to UTC if timezone not found
                return await self._get_utc_timezone()
            
        except ImportError:
            # Fallback if timezonefinder not installed
            return {
                "status": "success",
                "timezone": {
                    "value": "UTC",
                    "source": "coordinates-fallback",
                    "confidence": 0.3,
                    "ttl_sec": 3600,
                    "current_time": datetime.now(timezone.utc).isoformat(),
                    "utc_offset": "+0000",
                    "is_dst": False
                },
                "metadata": {
                    "detection_method": "coordinates_fallback",
                    "coordinates": {"lat": lat, "lon": lon},
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "note": "timezonefinder library not available"
                }
            }
        except Exception as e:
            return await self._get_utc_timezone()
    
    async def _get_utc_timezone(self) -> Dict[str, Any]:
        """Get UTC timezone as fallback."""
        current_time = datetime.now(timezone.utc)
        return {
            "status": "success",
            "timezone": {
                "value": "UTC",
                "source": "fallback",
                "confidence": 0.3,
                "ttl_sec": 3600,
                "current_time": current_time.isoformat(),
                "utc_offset": "+0000",
                "is_dst": False
            },
            "metadata": {
                "detection_method": "fallback",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the tool's parameter schema."""
        return {
            "type": "object",
            "properties": {
                "timezone_input": {
                    "type": "string",
                    "description": "Timezone string from browser (e.g., 'America/New_York')"
                },
                "ip_address": {
                    "type": "string",
                    "description": "IP address for timezone detection"
                },
                "latitude": {
                    "type": "number",
                    "description": "Latitude for timezone detection"
                },
                "longitude": {
                    "type": "number",
                    "description": "Longitude for timezone detection"
                }
            },
            "required": []
        }


class LocationTool(BaseTool):
    """Tool for location detection and geocoding."""
    
    def __init__(self):
        super().__init__("location_tool", "Detect and process location information")
        self.category = "metadata"
        self.location_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl = 10800  # 3 hours
    
    async def execute(
        self,
        ip_address: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        address: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Execute location detection and processing."""
        try:
            # Try coordinates first (highest accuracy)
            if latitude and longitude:
                return await self._process_coordinates(latitude, longitude)
            
            # Try IP-based location detection
            if ip_address:
                return await self._get_location_from_ip(ip_address)
            
            # Try address geocoding
            if address:
                return await self._geocode_address(address)
            
            return {
                "status": "error",
                "error": "No location input provided"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "metadata": {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "detection_method": "location_error"
                }
            }
    
    async def _process_coordinates(self, lat: float, lon: float) -> Dict[str, Any]:
        """Process coordinates and reverse geocode using multiple providers for maximum accuracy."""
        cache_key = f"coords_{lat}_{lon}"
        
        # Check cache first
        if cache_key in self.location_cache:
            cached_data = self.location_cache[cache_key]
            if time.time() - cached_data["timestamp"] < self.cache_ttl:
                return cached_data["data"]
        
        try:
            # Try multiple geocoding providers for better accuracy
            results = []
            
            # Try Nominatim first (most detailed)
            nominatim_result = await self._nominatim_reverse_geocode(lat, lon)
            if nominatim_result.get("status") == "success":
                results.append(nominatim_result)
            
            # Try Photon API as backup
            photon_result = await self._photon_reverse_geocode(lat, lon)
            if photon_result.get("status") == "success":
                results.append(photon_result)
            
            # Try LocationIQ API (free tier available)
            try:
                locationiq_result = await self._locationiq_reverse_geocode(lat, lon)
                if locationiq_result and locationiq_result.get("status") == "success":
                    results.append(locationiq_result)
            except Exception as e:
                print(f"LocationIQ API error: {e}")
            
            # Try Pelias API (free tier available)
            try:
                pelias_result = await self._pelias_reverse_geocode(lat, lon)
                if pelias_result and pelias_result.get("status") == "success":
                    results.append(pelias_result)
            except Exception as e:
                print(f"Pelias API error: {e}")
            
            # Merge results for better accuracy
            if results:
                merged_result = self._merge_geocoding_results(results, lat, lon)
                
                # Cache the result
                self.location_cache[cache_key] = {
                    "data": merged_result,
                    "timestamp": time.time()
                }
                
                return merged_result
            
            # Fallback to basic coordinates if all providers fail
            return {
                            "status": "success",
                            "location": {
                    "granularity": "coordinates",
                                "value": {
                                    "lat": lat,
                                    "lon": lon,
                        "city": "Unknown",
                        "country": "Unknown"
                    },
                    "source": "coordinates-basic",
                    "confidence": 0.8,
                    "ttl_sec": 3600
                            },
                            "metadata": {
                                "detection_method": "coordinates",
                                "coordinates": {"lat": lat, "lon": lon},
                                "timestamp": datetime.now(timezone.utc).isoformat()
                            }
                        }
                        
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "metadata": {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "detection_method": "coordinates_error"
                }
            }
    
    async def _nominatim_reverse_geocode(self, lat: float, lon: float) -> Dict[str, Any]:
        """Reverse geocode using OpenStreetMap Nominatim API with detailed address extraction."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    "https://nominatim.openstreetmap.org/reverse",
                    params={
                        "lat": lat,
                        "lon": lon,
                        "format": "json",
                        "addressdetails": 1,
                        "extratags": 1,
                        "namedetails": 1,
                        "zoom": 18  # Maximum zoom for street-level detail
                    },
                    headers={'User-Agent': 'ChatBot/1.0'}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    address = data.get("address", {})
                    
                    # Extract detailed address components
                    detailed_address = self._extract_detailed_address(address, data)
                    
            return {
                "status": "success",
                        "provider": "nominatim",
                        "location": detailed_address,
                        "confidence": 0.95
                    }
        except Exception as e:
            return {"status": "error", "provider": "nominatim", "error": str(e)}
    
    def _extract_detailed_address(self, address: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract detailed address components from Nominatim response."""
        # Street-level details
        street_number = address.get("house_number", "")
        street_name = (address.get("road") or 
                      address.get("street") or 
                      address.get("footway") or 
                      address.get("path") or 
                      "")
        
        # Building details
        building = (address.get("building") or 
                   address.get("house") or 
                   address.get("apartment") or 
                   "")
        
        # Neighborhood details
        neighbourhood = (address.get("neighbourhood") or 
                        address.get("suburb") or 
                        address.get("quarter") or 
                        "")
        
        # City details
        city = (address.get("city") or 
                address.get("town") or 
                address.get("village") or 
                address.get("hamlet") or 
                address.get("municipality") or 
                "")
        
        # Administrative levels
        county = address.get("county", "")
        state = address.get("state", "")
        region = address.get("region", "")
        province = address.get("province", "")
        
        # Country details
        country = address.get("country", "Unknown")
        country_code = address.get("country_code", "").upper()
        
        # Postal code
        postcode = address.get("postcode", "")
        
        # Construct full address
        address_parts = []
        if street_number:
            address_parts.append(street_number)
        if street_name:
            address_parts.append(street_name)
        if building:
            address_parts.append(building)
        
        street_address = " ".join(address_parts) if address_parts else ""
        
        # Determine granularity level
        granularity = "coordinates"
        if street_address:
            granularity = "street"
        elif neighbourhood:
            granularity = "neighbourhood"
        elif city:
            granularity = "city"
        elif state or county:
            granularity = "administrative"
        
        return {
            # Basic location
            "city": city,
            "country": country,
            "country_code": country_code,
            "state": state or region or province,
            "county": county,
            "postcode": postcode,
            
            # Detailed address components
            "street_address": street_address,
            "street_number": street_number,
            "street_name": street_name,
            "building": building,
            "neighbourhood": neighbourhood,
            
            # Administrative hierarchy
            "administrative_levels": {
                "level_1": state or region or province,
                "level_2": county,
                "level_3": city,
                "level_4": neighbourhood
            },
            
            # Additional details
            "granularity": granularity,
            "display_name": data.get("display_name", ""),
            "place_id": data.get("place_id"),
            "osm_type": data.get("osm_type"),
            "osm_id": data.get("osm_id")
        }
    
    async def _photon_reverse_geocode(self, lat: float, lon: float) -> Dict[str, Any]:
        """Reverse geocode using Photon API."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    "https://photon.komoot.io/reverse",
                    params={
                        "lat": lat,
                        "lon": lon,
                        "limit": 1
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("features") and len(data["features"]) > 0:
                        feature = data["features"][0]
                        properties = feature.get("properties", {})
                        
                        return {
                            "status": "success",
                            "provider": "photon",
                "location": {
                                "city": properties.get("city") or properties.get("name"),
                                "country": properties.get("country"),
                                "state": properties.get("state"),
                                "postcode": properties.get("postcode"),
                                "display_name": properties.get("name", "")
                            },
                            "confidence": 0.9
                        }
                    else:
                        return {"status": "error", "provider": "photon", "error": "No results found"}
        except Exception as e:
            return {"status": "error", "provider": "photon", "error": str(e)}
    
    async def _locationiq_reverse_geocode(self, lat: float, lon: float) -> Dict[str, Any]:
        """Reverse geocode using LocationIQ API (free tier available)."""
        try:
            # Note: LocationIQ requires API key for production use
            # For demo purposes, we'll use their free tier
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    "https://us1.locationiq.com/v1/reverse",
                    params={
                        "key": "demo",  # Demo key - replace with actual key for production
                        "lat": lat,
                        "lon": lon,
                        "format": "json",
                        "addressdetails": 1,
                        "extratags": 1,
                        "namedetails": 1,
                        "zoom": 18
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    address = data.get("address", {})
                    
                    # Extract detailed address components
                    detailed_address = self._extract_detailed_address(address, data)
                    
                    return {
                        "status": "success",
                        "provider": "locationiq",
                        "location": detailed_address,
                        "confidence": 0.9
                    }
        except Exception as e:
            return {"status": "error", "provider": "locationiq", "error": str(e)}
    
    async def _pelias_reverse_geocode(self, lat: float, lon: float) -> Dict[str, Any]:
        """Reverse geocode using Pelias API (free tier available)."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    "https://api.geocode.earth/v1/reverse",
                    params={
                        "api_key": "demo",  # Demo key - replace with actual key for production
                        "point.lat": lat,
                        "point.lon": lon,
                        "size": 1
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    features = data.get("features", [])
                    
                    if features:
                        feature = features[0]
                        properties = feature.get("properties", {})
                        geometry = feature.get("geometry", {})
                        
                        # Extract address components from Pelias
                        address_components = properties.get("address_parts", {})
                        
                        return {
                            "status": "success",
                            "provider": "pelias",
                            "location": {
                                "city": properties.get("locality") or properties.get("localadmin"),
                                "country": properties.get("country"),
                                "country_code": properties.get("country_a"),
                                "state": properties.get("region"),
                                "county": properties.get("county"),
                                "postcode": properties.get("postalcode"),
                                "street_address": properties.get("label"),
                                "street_name": properties.get("street"),
                                "neighbourhood": properties.get("neighbourhood"),
                                "granularity": properties.get("layer"),
                                "confidence": properties.get("confidence", 0.8)
                            },
                            "confidence": 0.9
                        }
        except Exception as e:
            return {"status": "error", "provider": "pelias", "error": str(e)}
    
    def _merge_geocoding_results(self, results: List[Dict[str, Any]], lat: float, lon: float) -> Dict[str, Any]:
        """Merge results from multiple geocoding providers for maximum accuracy and detail."""
        # Prioritize results by confidence and provider
        valid_results = [r for r in results if r.get("status") == "success"]
        
        if not valid_results:
            return {
                "status": "error",
                "error": "All geocoding providers failed"
            }
        
        # Use the result with highest confidence as base
        best_result = max(valid_results, key=lambda x: x.get("confidence", 0))
        
        # Merge detailed information from all providers
        merged_location = best_result["location"].copy()
        providers_used = [best_result["provider"]]
        
        # Track the best granularity level achieved
        best_granularity = merged_location.get("granularity", "coordinates")
        
        for result in valid_results:
            if result["provider"] != best_result["provider"]:
                providers_used.append(result["provider"])
                location_data = result["location"]
                
                # Fill in missing information from other providers
                for key, value in location_data.items():
                    if key not in merged_location or (merged_location[key] in ["Unknown", "", None]):
                        merged_location[key] = value
                
                # Update granularity if we found more detailed information
                current_granularity = location_data.get("granularity", "coordinates")
                granularity_levels = {"coordinates": 0, "administrative": 1, "city": 2, "neighbourhood": 3, "street": 4}
                if granularity_levels.get(current_granularity, 0) > granularity_levels.get(best_granularity, 0):
                    best_granularity = current_granularity
                    # Update key fields with more detailed data
                    if location_data.get("street_address"):
                        merged_location["street_address"] = location_data["street_address"]
                    if location_data.get("street_name"):
                        merged_location["street_name"] = location_data["street_name"]
                    if location_data.get("street_number"):
                        merged_location["street_number"] = location_data["street_number"]
                    if location_data.get("building"):
                        merged_location["building"] = location_data["building"]
        
        # Validate and clean address components
        validated_location = self._validate_address_components(merged_location)
        
        # Determine address quality
        quality_assessment = self._determine_address_quality(validated_location)
        
        # Construct comprehensive address
        address_components = []
        if validated_location.get("street_number"):
            address_components.append(validated_location["street_number"])
        if validated_location.get("street_name"):
            address_components.append(validated_location["street_name"])
        if validated_location.get("building"):
            address_components.append(validated_location["building"])
        
        full_street_address = " ".join(address_components) if address_components else validated_location.get("street_address", "")
        
        # Format full address string
        formatted_address = self._format_address_string(validated_location)
        
        # Determine final granularity
        final_granularity = best_granularity
        if full_street_address and not final_granularity == "street":
            final_granularity = "street"
        
        return {
            "status": "success",
            "location": {
                "granularity": final_granularity,
                    "value": {
                        "lat": lat,
                    "lon": lon,
                    
                    # Basic location info
                    "city": validated_location.get("city", "Unknown"),
                    "country": validated_location.get("country", "Unknown"),
                    "country_code": validated_location.get("country_code", ""),
                    "admin1": validated_location.get("state"),
                    "admin2": validated_location.get("county"),
                    "postcode": validated_location.get("postcode"),
                    
                    # Detailed address components
                    "street_address": full_street_address,
                    "street_number": validated_location.get("street_number"),
                    "street_name": validated_location.get("street_name"),
                    "building": validated_location.get("building"),
                    "neighbourhood": validated_location.get("neighbourhood"),
                    
                    # Administrative hierarchy
                    "administrative_levels": validated_location.get("administrative_levels", {}),
                    
                    # Additional metadata
                    "display_name": validated_location.get("display_name", ""),
                    "place_id": validated_location.get("place_id"),
                    "osm_type": validated_location.get("osm_type"),
                    "osm_id": validated_location.get("osm_id"),
                    
                    # Quality and formatting
                    "formatted_address": formatted_address,
                    "address_quality": quality_assessment
                },
                "source": f"multi-provider-{'-'.join(providers_used)}",
                "confidence": min(0.99, best_result.get("confidence", 0.9) + (len(providers_used) * 0.02)),  # Boost for multi-provider
                "ttl_sec": 10800
                },
                "metadata": {
                "detection_method": "coordinates_multi_provider_enhanced",
                    "coordinates": {"lat": lat, "lon": lon},
                "providers_used": providers_used,
                "granularity_achieved": final_granularity,
                "address_components_found": len([k for k, v in validated_location.items() if v and k in ["street_address", "street_name", "street_number", "building"]]),
                "quality_level": quality_assessment.get("quality_level"),
                "quality_percentage": quality_assessment.get("quality_percentage"),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            }
            
    def _validate_address_components(self, address_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean address components."""
        validated = {}
        
        # Validate and clean each component
        for key, value in address_data.items():
            if value and str(value).strip():
                # Clean the value
                cleaned_value = str(value).strip()
                
                # Apply specific validation rules
                if key == "postcode":
                    # Remove non-alphanumeric characters except hyphens
                    cleaned_value = ''.join(c for c in cleaned_value if c.isalnum() or c == '-')
                elif key in ["street_number", "house_number"]:
                    # Keep only alphanumeric and common separators
                    cleaned_value = ''.join(c for c in cleaned_value if c.isalnum() or c in ['-', '/', ' '])
                elif key == "country_code":
                    # Ensure uppercase and 2-3 characters
                    cleaned_value = cleaned_value.upper()[:3]
                
                validated[key] = cleaned_value
        
        return validated
    
    def _determine_address_quality(self, address_data: Dict[str, Any]) -> Dict[str, Any]:
        """Determine the quality and completeness of address data."""
        quality_score = 0
        completeness = {}
        
        # Define required fields and their weights
        field_weights = {
            "street_number": 3,
            "street_name": 3,
            "city": 2,
            "state": 2,
            "country": 2,
            "postcode": 1,
            "building": 1,
            "neighbourhood": 1
        }
        
        total_weight = sum(field_weights.values())
        
        # Calculate completeness for each field
        for field, weight in field_weights.items():
            if address_data.get(field) and str(address_data[field]).strip():
                quality_score += weight
                completeness[field] = True
            else:
                completeness[field] = False
        
        # Calculate quality percentage
        quality_percentage = (quality_score / total_weight) * 100
        
        # Determine quality level
        if quality_percentage >= 80:
            quality_level = "excellent"
        elif quality_percentage >= 60:
            quality_level = "good"
        elif quality_percentage >= 40:
            quality_level = "fair"
        else:
            quality_level = "poor"
        
        return {
            "quality_score": quality_score,
            "quality_percentage": round(quality_percentage, 2),
            "quality_level": quality_level,
            "completeness": completeness,
            "missing_fields": [field for field, present in completeness.items() if not present]
        }
    
    def _format_address_string(self, address_data: Dict[str, Any]) -> str:
        """Format address data into a readable string."""
        address_parts = []
        
        # Street address
        street_parts = []
        if address_data.get("street_number"):
            street_parts.append(address_data["street_number"])
        if address_data.get("street_name"):
            street_parts.append(address_data["street_name"])
        if street_parts:
            address_parts.append(" ".join(street_parts))
        
        # Building
        if address_data.get("building"):
            address_parts.append(address_data["building"])
        
        # Neighborhood
        if address_data.get("neighbourhood"):
            address_parts.append(address_data["neighbourhood"])
        
        # City
        if address_data.get("city"):
            address_parts.append(address_data["city"])
        
        # State/Region
        if address_data.get("state"):
            address_parts.append(address_data["state"])
        
        # Country
        if address_data.get("country"):
            address_parts.append(address_data["country"])
        
        # Postal code
        if address_data.get("postcode"):
            address_parts.append(address_data["postcode"])
        
        return ", ".join(address_parts) if address_parts else "Address not available"
    
    async def _get_location_from_ip(self, ip_address: str) -> Dict[str, Any]:
        """Get location from IP address using multiple providers."""
        cache_key = f"ip_{ip_address}"
        
        # Check cache first
        if cache_key in self.location_cache:
            cached_data = self.location_cache[cache_key]
            if time.time() - cached_data["timestamp"] < self.cache_ttl:
                return cached_data["data"]
        
        try:
            # Try multiple IP geolocation providers for better accuracy
            results = []
            
            # Try ip-api.com first
            ip_api_result = await self._ip_api_geolocation(ip_address)
            if ip_api_result.get("status") == "success":
                results.append(ip_api_result)
            
            # Try BigDataCloud as backup
            bigdata_result = await self._bigdata_cloud_geolocation(ip_address)
            if bigdata_result.get("status") == "success":
                results.append(bigdata_result)
            
            # Merge results for better accuracy
            if results:
                merged_result = self._merge_ip_geolocation_results(results, ip_address)
                
                # Cache the result
                self.location_cache[cache_key] = {
                    "data": merged_result,
                    "timestamp": time.time()
                }
                
                return merged_result
            
            return {
                "status": "error",
                "error": "Unable to determine location from IP"
            }
            
        except Exception as e:
            return await self.handle_error(e)
    
    async def _ip_api_geolocation(self, ip_address: str) -> Dict[str, Any]:
        """Get location from IP using ip-api.com."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"http://ip-api.com/json/{ip_address}")
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "success":
                        return {
                            "status": "success",
                            "provider": "ip-api",
                            "location": {
                                    "lat": data.get("lat"),
                                    "lon": data.get("lon"),
                                    "city": data.get("city"),
                                    "country": data.get("country"),
                                    "country_code": data.get("countryCode"),
                                "state": data.get("regionName"),
                                "region": data.get("region"),
                                "postcode": data.get("zip"),
                                "timezone": data.get("timezone"),
                                "isp": data.get("isp"),
                                "org": data.get("org")
                            },
                            "confidence": 0.8
                        }
        except Exception as e:
            return {"status": "error", "provider": "ip-api", "error": str(e)}
    
    async def _bigdata_cloud_geolocation(self, ip_address: str) -> Dict[str, Any]:
        """Get location from IP using BigDataCloud API."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"https://api.bigdatacloud.net/data/ip-geolocation",
                    params={"ip": ip_address}
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get("country"):
                        location_data = data.get("location", {})
                        return {
                            "status": "success",
                            "provider": "bigdatacloud",
                            "location": {
                                "lat": location_data.get("latitude"),
                                "lon": location_data.get("longitude"),
                                "city": location_data.get("city"),
                                "country": data.get("country"),
                                "country_code": data.get("countryCode"),
                                "state": location_data.get("principalSubdivision"),
                                "region": location_data.get("principalSubdivisionCode"),
                                "postcode": location_data.get("postcode"),
                                "timezone": data.get("timezone", {}).get("name"),
                                "isp": data.get("network", {}).get("carrier", {}).get("name"),
                                "org": data.get("network", {}).get("organisation")
                            },
                            "confidence": 0.85
                        }
        except Exception as e:
            return {"status": "error", "provider": "bigdatacloud", "error": str(e)}
    
    def _merge_ip_geolocation_results(self, results: List[Dict[str, Any]], ip_address: str) -> Dict[str, Any]:
        """Merge results from multiple IP geolocation providers."""
        valid_results = [r for r in results if r.get("status") == "success"]
        
        if not valid_results:
            return {
                "status": "error",
                "error": "All IP geolocation providers failed"
            }
        
        # Use the result with highest confidence
        best_result = max(valid_results, key=lambda x: x.get("confidence", 0))
        
        # Merge additional information from other providers
        merged_location = best_result["location"].copy()
        providers_used = [best_result["provider"]]
        
        for result in valid_results:
            if result["provider"] != best_result["provider"]:
                providers_used.append(result["provider"])
                # Fill in missing information from other providers
                for key, value in result["location"].items():
                    if key not in merged_location or merged_location[key] is None:
                        merged_location[key] = value
        
        return {
            "status": "success",
            "location": {
                "granularity": "city",
                "value": {
                    "lat": merged_location.get("lat"),
                    "lon": merged_location.get("lon"),
                    "city": merged_location.get("city", "Unknown"),
                    "country": merged_location.get("country", "Unknown"),
                    "country_code": merged_location.get("country_code", ""),
                    "admin1": merged_location.get("state"),
                    "admin2": merged_location.get("region"),
                    "postcode": merged_location.get("postcode"),
                    "timezone": merged_location.get("timezone"),
                    "isp": merged_location.get("isp"),
                    "org": merged_location.get("org")
                },
                "source": f"ip-multi-provider-{'-'.join(providers_used)}",
                "confidence": min(0.95, best_result.get("confidence", 0.8) + 0.1),  # Boost for multi-provider
                "ttl_sec": 10800
            },
            "metadata": {
                "detection_method": "ip_geolocation_multi_provider",
                "ip_address": ip_address,
                "providers_used": providers_used,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
    
    async def _geocode_address(self, address: str) -> Dict[str, Any]:
        """Geocode an address to coordinates."""
        cache_key = f"addr_{address}"
        
        # Check cache first
        if cache_key in self.location_cache:
            cached_data = self.location_cache[cache_key]
            if time.time() - cached_data["timestamp"] < self.cache_ttl:
                return cached_data["data"]
        
        try:
            # Use Open-Meteo Geocoding API (free, no key required)
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    "https://geocoding-api.open-meteo.com/v1/search",
                    params={
                        "name": address,
                        "count": 1,
                        "language": "en"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("results"):
                        result_data = data["results"][0]
                        
                        result = {
                            "status": "success",
                            "location": {
                                "granularity": "city",
                                "value": {
                                    "lat": result_data.get("latitude"),
                                    "lon": result_data.get("longitude"),
                                    "city": result_data.get("name"),
                                    "country": result_data.get("country"),
                                    "country_code": result_data.get("country_code"),
                                    "admin1": result_data.get("admin1"),
                                    "admin2": result_data.get("admin2")
                                },
                                "source": "address-geocoding",
                                "confidence": 0.9,
                                "ttl_sec": 86400
                            },
                            "metadata": {
                                "detection_method": "address_geocoding",
                                "address": address,
                                "timestamp": datetime.now(timezone.utc).isoformat()
                            }
                        }
                        
                        # Cache the result
                        self.location_cache[cache_key] = {
                            "data": result,
                            "timestamp": time.time()
                        }
                        
                        return result
            
            return {
                "status": "error",
                "error": "Unable to geocode address"
            }
            
        except Exception as e:
            return await self.handle_error(e)
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the tool's parameter schema."""
        return {
            "type": "object",
            "properties": {
                "ip_address": {
                    "type": "string",
                    "description": "IP address for location detection"
                },
                "latitude": {
                    "type": "number",
                    "description": "Latitude coordinate"
                },
                "longitude": {
                    "type": "number",
                    "description": "Longitude coordinate"
                },
                "address": {
                    "type": "string",
                    "description": "Address string to geocode"
                }
            },
            "required": []
        }


class DateTimeTool(BaseTool):
    """Tool for date and time information."""
    
    def __init__(self):
        super().__init__("datetime_tool", "Get current date and time information")
        self.category = "metadata"
    
    async def execute(
        self,
        timezone_str: Optional[str] = None,
        format_type: str = "iso",
        **kwargs
    ) -> Dict[str, Any]:
        """Execute date and time retrieval."""
        try:
            if timezone_str:
                tz = ZoneInfo(timezone_str)
                current_time = datetime.now(tz)
            else:
                current_time = datetime.now(timezone.utc)
                timezone_str = "UTC"
            
            if format_type == "iso":
                time_str = current_time.isoformat()
            elif format_type == "readable":
                time_str = current_time.strftime("%Y-%m-%d %H:%M:%S %Z")
            elif format_type == "timestamp":
                time_str = str(int(current_time.timestamp()))
            else:
                time_str = current_time.isoformat()
            
            return {
                "status": "success",
                "datetime": {
                    "value": time_str,
                    "timezone": timezone_str,
                    "format": format_type,
                    "utc_offset": current_time.strftime("%z"),
                    "is_dst": current_time.dst() != None,
                    "day_of_week": current_time.strftime("%A"),
                    "day_of_year": current_time.timetuple().tm_yday,
                    "week_number": current_time.isocalendar()[1]
                },
                "metadata": {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "source": "system_clock"
                }
            }
            
        except Exception as e:
            return await self.handle_error(e)
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the tool's parameter schema."""
        return {
            "type": "object",
            "properties": {
                "timezone_str": {
                    "type": "string",
                    "description": "Timezone string (e.g., 'America/New_York')"
                },
                "format_type": {
                    "type": "string",
                    "enum": ["iso", "readable", "timestamp"],
                    "description": "Format for the datetime output",
                    "default": "iso"
                }
            },
            "required": []
        }


class UserAgentTool(BaseTool):
    """Tool for user agent and device detection."""
    
    def __init__(self):
        super().__init__("user_agent_tool", "Detect user agent and device information")
        self.category = "metadata"
    
    async def execute(
        self,
        user_agent: Optional[str] = None,
        client_hints: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Execute user agent and device detection."""
        try:
            device_info = {
                "form_factor": "unknown",
                "browser": "unknown",
                "os": "unknown",
                "mobile": False,
                "source": "unknown",
                "confidence": 0.0
            }
            
            # Process User-Agent Client Hints (preferred method)
            if client_hints:
                device_info.update(await self._process_client_hints(client_hints))
            
            # Fallback to User-Agent string parsing
            elif user_agent:
                device_info.update(await self._parse_user_agent(user_agent))
            
            return {
                "status": "success",
                "device": device_info,
                "metadata": {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "detection_method": device_info["source"]
                }
            }
            
        except Exception as e:
            return await self.handle_error(e)
    
    async def _process_client_hints(self, hints: Dict[str, str]) -> Dict[str, Any]:
        """Process User-Agent Client Hints."""
        form_factor = "desktop"
        mobile = False
        
        # Check for mobile indicators
        if hints.get("Sec-CH-UA-Mobile") == "?1":
            mobile = True
            form_factor = "mobile"
        
        # Check for platform
        platform = hints.get("Sec-CH-UA-Platform", "").strip('"')
        if platform.lower() in ["android", "ios"]:
            mobile = True
            form_factor = "mobile"
        
        return {
            "form_factor": form_factor,
            "browser": hints.get("Sec-CH-UA", "unknown"),
            "os": platform,
            "mobile": mobile,
            "source": "ua-client-hints",
            "confidence": 0.95
        }
    
    async def _parse_user_agent(self, user_agent: str) -> Dict[str, Any]:
        """Parse User-Agent string using user-agents library for enhanced detection."""
        try:
            from user_agents import parse
            
            ua = parse(user_agent)
            
            return {
                "form_factor": "mobile" if ua.is_mobile else ("tablet" if ua.is_tablet else "desktop"),
                "browser": {
                    "name": ua.browser.family,
                    "version": ua.browser.version_string,
                    "major_version": ua.browser.version[0] if ua.browser.version else None
                },
                "os": {
                    "name": ua.os.family,
                    "version": ua.os.version_string,
                    "major_version": ua.os.version[0] if ua.os.version else None
                },
                "device": {
                    "brand": ua.device.brand,
                    "model": ua.device.model,
                    "family": ua.device.family
                },
                "mobile": ua.is_mobile,
                "tablet": ua.is_tablet,
                "pc": ua.is_pc,
                "bot": ua.is_bot,
                "source": "user-agents-library",
                "confidence": 0.9
            }
        except ImportError:
            # Fallback to basic parsing if user-agents library not available
            return await self._parse_user_agent_basic(user_agent)
        except Exception as e:
            # Fallback to basic parsing on any error
            return await self._parse_user_agent_basic(user_agent)
    
    async def _parse_user_agent_basic(self, user_agent: str) -> Dict[str, Any]:
        """Basic User-Agent string parsing (fallback implementation)."""
        ua_lower = user_agent.lower()
        
        # Detect mobile
        mobile = any(indicator in ua_lower for indicator in [
            "mobile", "android", "iphone", "ipad", "tablet"
        ])
        
        # Detect form factor
        if mobile:
            form_factor = "mobile"
        elif "tablet" in ua_lower:
            form_factor = "tablet"
        else:
            form_factor = "desktop"
        
        # Detect browser
        browser = "unknown"
        if "chrome" in ua_lower:
            browser = "chrome"
        elif "firefox" in ua_lower:
            browser = "firefox"
        elif "safari" in ua_lower:
            browser = "safari"
        elif "edge" in ua_lower:
            browser = "edge"
        
        # Detect OS
        os_name = "unknown"
        if "windows" in ua_lower:
            os_name = "windows"
        elif "mac" in ua_lower:
            os_name = "macos"
        elif "linux" in ua_lower:
            os_name = "linux"
        elif "android" in ua_lower:
            os_name = "android"
        elif "ios" in ua_lower:
            os_name = "ios"
        
        return {
            "form_factor": form_factor,
            "browser": browser,
            "os": os_name,
            "mobile": mobile,
            "source": "user-agent-string-basic",
            "confidence": 0.7
        }
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the tool's parameter schema."""
        return {
            "type": "object",
            "properties": {
                "user_agent": {
                    "type": "string",
                    "description": "User-Agent string from browser"
                },
                "client_hints": {
                    "type": "object",
                    "description": "User-Agent Client Hints headers",
                    "properties": {
                        "Sec-CH-UA": {"type": "string"},
                        "Sec-CH-UA-Mobile": {"type": "string"},
                        "Sec-CH-UA-Platform": {"type": "string"}
                    }
                }
            },
            "required": []
        }

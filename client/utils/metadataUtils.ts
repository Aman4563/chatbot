/**
 * Utility functions for collecting browser metadata
 */

export interface BrowserMetadata {
  timezone?: string;
  language?: string;
  platform?: string;
  userAgent?: string;
  screenResolution?: string;
  location?: {
    latitude: number;
    longitude: number;
    accuracy?: number;        // Accuracy radius in meters
    altitude?: number | null; // Altitude in meters
    altitudeAccuracy?: number | null; // Altitude accuracy in meters
    heading?: number | null;  // Direction of travel in degrees
    speed?: number | null;    // Speed in meters per second
    timestamp?: number;       // When location was obtained
    source?: string;          // Source of location data
  };
  consent?: {
    location: boolean;
    timezone: boolean;
  };
  display?: {
    screen: {
      width: number;
      height: number;
      availWidth: number;
      availHeight: number;
      colorDepth: number;
      pixelDepth: number;
    };
    window: {
      innerWidth: number;
      innerHeight: number;
      outerWidth: number;
      outerHeight: number;
    };
    devicePixelRatio: number;
    orientation: string;
  };
  network?: {
    effectiveType?: string;
    downlink?: number;
    rtt?: number;
    saveData?: boolean;
  };
  device?: {
    formFactor: string;
    mobile: boolean;
    tablet: boolean;
    touch: boolean;
  };
}

/**
 * Get browser timezone using Intl API
 */
export const getBrowserTimezone = (): string => {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone;
  } catch (error) {
    console.warn('Failed to get browser timezone:', error);
    return 'UTC';
  }
};

/**
 * Get browser language
 */
export const getBrowserLanguage = (): string => {
  return navigator.language || 'en-US';
};

/**
 * Get browser platform
 */
export const getBrowserPlatform = (): string => {
  return navigator.platform || 'unknown';
};

/**
 * Get screen resolution
 */
export const getScreenResolution = (): string => {
  return `${screen.width}x${screen.height}`;
};

// Session cache for location data
let locationCache: {
  data: {
    latitude: number;
    longitude: number;
    accuracy?: number;
    altitude?: number | null;
    altitudeAccuracy?: number | null;
    heading?: number | null;
    speed?: number | null;
    timestamp?: number;
    source?: string;
  } | null;
  timestamp: number;
} = {
  data: null,
  timestamp: 0
};

const LOCATION_CACHE_DURATION = 5 * 60 * 1000; // 5 minutes in milliseconds

/**
 * Request location permission and get coordinates with enhanced accuracy
 */
export const getLocationWithPermission = async (forceRefresh: boolean = false): Promise<{
  latitude: number;
  longitude: number;
  accuracy?: number;
  altitude?: number | null;
  altitudeAccuracy?: number | null;
  heading?: number | null;
  speed?: number | null;
  timestamp?: number;
  source?: string;
} | null> => {
  if (!navigator.geolocation) {
    console.warn('Geolocation is not supported by this browser');
    return null;
  }

  // Check cache first (unless force refresh)
  if (!forceRefresh && locationCache.data && (Date.now() - locationCache.timestamp) < LOCATION_CACHE_DURATION) {
    console.log('Using cached location data');
    return locationCache.data;
  }

  try {
    // Try high accuracy first
    const position = await new Promise<GeolocationPosition>((resolve, reject) => {
      navigator.geolocation.getCurrentPosition(resolve, reject, {
        enableHighAccuracy: true,    // Use GPS if available
        timeout: 15000,              // Increased timeout for better accuracy
        maximumAge: 60000           // Accept cached data up to 1 minute old
      });
    });

    const locationData = {
      latitude: position.coords.latitude,
      longitude: position.coords.longitude,
      accuracy: position.coords.accuracy,
      altitude: position.coords.altitude,
      altitudeAccuracy: position.coords.altitudeAccuracy,
      heading: position.coords.heading,
      speed: position.coords.speed,
      timestamp: position.timestamp,
      source: 'geolocation-high-accuracy'
    };

    // Cache the result
    locationCache = {
      data: locationData,
      timestamp: Date.now()
    };

    console.log('Location obtained with high accuracy:', {
      lat: locationData.latitude,
      lng: locationData.longitude,
      accuracy: locationData.accuracy,
      source: locationData.source
    });

    return locationData;

  } catch (error) {
    console.warn('High accuracy location failed, trying fallback:', error);
    
    // Fallback to lower accuracy if high accuracy fails
    try {
      const position = await new Promise<GeolocationPosition>((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(resolve, reject, {
          enableHighAccuracy: false,  // Use network-based location
          timeout: 10000,             // Shorter timeout for fallback
          maximumAge: 300000          // Accept older cached data
        });
      });

      const locationData = {
        latitude: position.coords.latitude,
        longitude: position.coords.longitude,
        accuracy: position.coords.accuracy,
        altitude: position.coords.altitude,
        altitudeAccuracy: position.coords.altitudeAccuracy,
        heading: position.coords.heading,
        speed: position.coords.speed,
        timestamp: position.timestamp,
        source: 'geolocation-network'
      };

      // Cache the result
      locationCache = {
        data: locationData,
        timestamp: Date.now()
      };

      console.log('Location obtained with network accuracy:', {
        lat: locationData.latitude,
        lng: locationData.longitude,
        accuracy: locationData.accuracy,
        source: locationData.source
      });

      return locationData;

    } catch (fallbackError) {
      console.error('All location methods failed:', fallbackError);
      return null;
    }
  }
};

/**
 * Clear location cache (useful for testing or when user moves significantly)
 */
export const clearLocationCache = (): void => {
  locationCache = {
    data: null,
    timestamp: 0
  };
  console.log('Location cache cleared');
};

/**
 * Get cached location data without requesting new location
 */
export const getCachedLocation = (): {
  latitude: number;
  longitude: number;
  accuracy?: number;
  altitude?: number | null;
  altitudeAccuracy?: number | null;
  heading?: number | null;
  speed?: number | null;
  timestamp?: number;
  source?: string;
} | null => {
  if (locationCache.data && (Date.now() - locationCache.timestamp) < LOCATION_CACHE_DURATION) {
    return locationCache.data;
  }
  return null;
};

/**
 * Get enhanced display information
 */
export const getEnhancedDisplayInfo = () => {
  return {
    screen: {
      width: screen.width,
      height: screen.height,
      availWidth: screen.availWidth,
      availHeight: screen.availHeight,
      colorDepth: screen.colorDepth,
      pixelDepth: screen.pixelDepth
    },
    window: {
      innerWidth: window.innerWidth,
      innerHeight: window.innerHeight,
      outerWidth: window.outerWidth,
      outerHeight: window.outerHeight
    },
    devicePixelRatio: window.devicePixelRatio,
    orientation: screen.orientation?.type || 'unknown'
  };
};

/**
 * Get network information
 */
export const getNetworkInfo = async () => {
  if ('connection' in navigator) {
    const connection = (navigator as any).connection;
    return {
      effectiveType: connection.effectiveType,
      downlink: connection.downlink,
      rtt: connection.rtt,
      saveData: connection.saveData
    };
  }
  return null;
};

/**
 * Get device information
 */
export const getDeviceInfo = () => {
  const userAgent = navigator.userAgent.toLowerCase();
  
  // Detect mobile
  const mobile = /android|webos|iphone|ipad|ipod|blackberry|iemobile|opera mini/i.test(userAgent);
  
  // Detect tablet
  const tablet = /ipad|android(?!.*mobile)|tablet/i.test(userAgent);
  
  // Detect touch capability
  const touch = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
  
  // Determine form factor
  let formFactor = 'desktop';
  if (mobile) formFactor = 'mobile';
  else if (tablet) formFactor = 'tablet';
  
  return {
    formFactor,
    mobile,
    tablet,
    touch
  };
};

/**
 * Collect all available browser metadata
 */
export const collectBrowserMetadata = async (): Promise<BrowserMetadata> => {
  const metadata: BrowserMetadata = {
    timezone: getBrowserTimezone(),
    language: getBrowserLanguage(),
    platform: getBrowserPlatform(),
    userAgent: navigator.userAgent,
    screenResolution: getScreenResolution(),
    display: getEnhancedDisplayInfo(),
    device: getDeviceInfo(),
    consent: {
      timezone: true, // Timezone is always available
      location: false // Location requires explicit permission
    }
  };

  // Try to get network information
  try {
    const networkInfo = await getNetworkInfo();
    if (networkInfo) {
      metadata.network = networkInfo;
    }
  } catch (error) {
    console.warn('Failed to get network information:', error);
  }

  // Try to get location if user has previously granted permission
  try {
    const location = await getLocationWithPermission();
    if (location) {
      metadata.location = location;
      metadata.consent!.location = true;
    }
  } catch (error) {
    // Location permission denied or failed
    console.warn('Location access denied or failed:', error);
  }

  return metadata;
};

/**
 * Request location permission with user consent and enhanced accuracy
 */
export const requestLocationPermission = async (): Promise<{
  success: boolean;
  location?: {
    latitude: number;
    longitude: number;
    accuracy?: number;
    altitude?: number | null;
    altitudeAccuracy?: number | null;
    heading?: number | null;
    speed?: number | null;
    timestamp?: number;
    source?: string;
  };
  error?: string;
}> => {
  if (!navigator.geolocation) {
    return {
      success: false,
      error: 'Geolocation is not supported by this browser'
    };
  }

  try {
    const location = await getLocationWithPermission(true); // Force refresh
    if (location) {
      return {
        success: true,
        location: location
      };
    } else {
      return {
        success: false,
        error: 'Unable to obtain location data'
      };
    }
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error occurred'
    };
  }
};

/**
 * Check if location permission is already granted
 */
export const checkLocationPermission = async (): Promise<boolean> => {
  if (!navigator.permissions) {
    return false;
  }

  try {
    const permission = await navigator.permissions.query({ name: 'geolocation' as PermissionName });
    return permission.state === 'granted';
  } catch (error) {
    return false;
  }
};

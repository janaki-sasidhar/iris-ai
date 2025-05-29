"""Doppler secrets manager integration"""

import os
import sys
import logging
from dopplersdk import DopplerSDK

logger = logging.getLogger(__name__)

class DopplerError(Exception):
    """Exception raised for Doppler-related errors"""
    pass

def load_doppler_secrets():
    """Load Doppler secrets into environment variables
    
    Requires:
        DOPPLER_TOKEN: API token for Doppler
        ENVIRONMENT: Must be either 'DEV' or 'PROD'
        
    Returns:
        dict: Dictionary of loaded secrets
        
    Raises:
        DopplerError: If required environment variables are missing or invalid
    """
    # Check for required environment variables
    token = os.environ.get("DOPPLER_TOKEN")
    if not token:
        raise DopplerError("DOPPLER_TOKEN environment variable is required")
        
    environment = os.environ.get("ENVIRONMENT")
    if not environment:
        raise DopplerError("ENVIRONMENT environment variable is required (must be 'DEV' or 'PROD')")
    
    # Validate environment
    environment = environment.upper()
    if environment not in ["DEV", "PROD"]:
        raise DopplerError(f"Invalid ENVIRONMENT value: {environment}. Must be 'DEV' or 'PROD'")
    
    # Map environment to Doppler config
    config = "dev" if environment == "DEV" else "prd"
    project = "iris-ai"
    
    try:
        # Initialize Doppler SDK
        sdk = DopplerSDK()
        sdk.set_access_token(token)
        
        # Fetch secrets
        results = sdk.secrets.list(project=project, config=config)
        
        if not hasattr(results, 'secrets'):
            raise DopplerError(f"Failed to fetch secrets from Doppler for {project}/{config}")
        
        # Extract and load secrets
        secrets = {}
        for key, secret_data in results.secrets.items():
            # Skip Doppler's internal variables
            if key.startswith("DOPPLER_"):
                continue
                
            value = secret_data.get('computed', '')
            if value:
                os.environ[key] = str(value)
                secrets[key] = value
        
        logger.info(f"Loaded {len(secrets)} secrets from Doppler ({project}/{config})")
        return secrets
        
    except Exception as e:
        error_msg = f"Error loading Doppler secrets: {str(e)}"
        logger.error(error_msg)
        raise DopplerError(error_msg) from e
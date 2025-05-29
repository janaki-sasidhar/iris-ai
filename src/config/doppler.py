"""Doppler secrets manager integration"""

import os
import sys
import logging
from dopplersdk import DopplerSDK

logger = logging.getLogger(__name__)

class DopplerError(Exception):
    """Exception raised for Doppler-related errors"""
    pass

def load_doppler_secrets(token=None, environment=None, project="iris-ai"):
    """Load Doppler secrets into environment variables
    
    Args:
        token (str, optional): Doppler service token. If None, uses DOPPLER_TOKEN env var.
        environment (str, optional): Environment (DEV or PROD). If None, uses ENVIRONMENT env var.
        project (str, optional): Doppler project name. Defaults to "iris-ai".
        
    Returns:
        dict: Dictionary of loaded secrets
        
    Raises:
        DopplerError: If required parameters are missing or invalid
    """
    # Get token from parameter or environment
    token = token or os.environ.get("DOPPLER_TOKEN")
    if not token:
        raise DopplerError("Doppler token not provided and DOPPLER_TOKEN env var not set")
        
    # Get environment from parameter or environment variable
    environment = environment or os.environ.get("ENVIRONMENT")
    if not environment:
        raise DopplerError("Environment not provided and ENVIRONMENT env var not set")
    
    # Validate environment
    environment = environment.upper()
    if environment not in ["DEV", "PROD"]:
        raise DopplerError(f"Invalid environment value: {environment}. Must be 'DEV' or 'PROD'")
    
    # Map environment to Doppler config
    config = "dev" if environment == "DEV" else "prd"
    
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
                # Only set if not already set in environment
                # This preserves any values set directly in the environment
                if not os.environ.get(key):
                    os.environ[key] = str(value)
                secrets[key] = value
        
        logger.info(f"Loaded {len(secrets)} secrets from Doppler ({project}/{config})")
        return secrets
        
    except Exception as e:
        error_msg = f"Error loading Doppler secrets: {str(e)}"
        logger.error(error_msg)
        raise DopplerError(error_msg) from e
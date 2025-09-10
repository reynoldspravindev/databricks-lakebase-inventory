"""
Configuration management for the Flask inventory app.
Supports both environment variables and YAML configuration file.
"""

import os
import yaml
from typing import Dict, Any, Optional

class Config:
    """Configuration class that loads settings from environment variables and YAML file."""
    
    def __init__(self, yaml_file: str = "app.yaml"):
        self.yaml_file = yaml_file
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file and environment variables."""
        config = {}
        
        # Load from YAML file if it exists
        if os.path.exists(self.yaml_file):
            try:
                with open(self.yaml_file, 'r') as file:
                    config = yaml.safe_load(file) or {}
                print(f"✅ Loaded configuration from {self.yaml_file}")
            except Exception as e:
                print(f"⚠️  Warning: Could not load {self.yaml_file}: {e}")
        
        # Override with environment variables (environment takes precedence)
        config = self._override_with_env_vars(config)
        
        return config
    
    def _override_with_env_vars(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Override YAML config with environment variables."""
        env_mappings = {
            'DATABRICKS_HOST': ['databricks', 'host'],
            'DASHBOARD_ID': ['databricks', 'dashboard_id'],
            'GENIE_SPACE_ID': ['databricks', 'genie_space_id'],
            'PGHOST': ['database', 'host'],
            'PGPORT': ['database', 'port'],
            'PGDATABASE': ['database', 'database'],
            'PGUSER': ['database', 'user'],
            'PGSSLMODE': ['database', 'ssl_mode'],
            'SECRET_KEY': ['app', 'secret_key'],
            'PORT': ['app', 'port'],
            'DEBUG': ['app', 'debug']
        }
        
        for env_var, config_path in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                # Navigate to the nested config path
                current = config
                for key in config_path[:-1]:
                    if key not in current:
                        current[key] = {}
                    current = current[key]
                
                # Set the final value
                final_key = config_path[-1]
                current[final_key] = self._convert_env_value(env_value)
        
        return config
    
    def _convert_env_value(self, value: str) -> Any:
        """Convert environment variable string to appropriate type."""
        # Convert boolean strings
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # Convert numeric strings
        if value.isdigit():
            return int(value)
        
        # Try to convert to float
        try:
            return float(value)
        except ValueError:
            pass
        
        # Return as string
        return value
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value using dot notation (e.g., 'databricks.host')."""
        keys = key_path.split('.')
        current = self.config
        
        try:
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return default
    
    def get_dashboard_embed_url(self) -> Optional[str]:
        """Get the dashboard embed URL."""
        host = self.get('databricks.host')
        dashboard_id = self.get('databricks.dashboard_id')
        
        if not host or not dashboard_id:
            return None
        
        base_url = host.rstrip('/')
        return f"{base_url}/embed/dashboardsv3/{dashboard_id}"
    
    def get_dashboard_public_url(self) -> Optional[str]:
        """Get the dashboard public URL."""
        host = self.get('databricks.host')
        dashboard_id = self.get('databricks.dashboard_id')
        
        if not host or not dashboard_id:
            return None
        
        base_url = host.rstrip('/')
        return f"{base_url}/dashboardsv3/{dashboard_id}"
    
    def get_genie_space_id(self) -> Optional[str]:
        """Get the Genie space ID."""
        return self.get('databricks.genie_space_id')
    
    def is_dashboard_configured(self) -> bool:
        """Check if dashboard is configured."""
        return self.get_dashboard_embed_url() is not None
    
    def is_genie_configured(self) -> bool:
        """Check if Genie is configured."""
        return self.get_genie_space_id() is not None
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration."""
        return {
            'host': self.get('database.host'),
            'port': self.get('database.port', 5432),
            'database': self.get('database.database'),
            'user': self.get('database.user'),
            'ssl_mode': self.get('database.ssl_mode', 'require')
        }
    
    def print_config_summary(self):
        """Print a summary of the current configuration."""
        print("📋 Configuration Summary:")
        print(f"  Dashboard configured: {self.is_dashboard_configured()}")
        print(f"  Genie configured: {self.is_genie_configured()}")
        print(f"  Databricks host: {self.get('databricks.host', 'Not set')}")
        print(f"  Dashboard ID: {self.get('databricks.dashboard_id', 'Not set')}")
        print(f"  Genie Space ID: {self.get('databricks.genie_space_id', 'Not set')}")
        print(f"  Database host: {self.get('database.host', 'Not set')}")

# Global config instance
config = Config()

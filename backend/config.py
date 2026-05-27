"""
Configuration and environment variable validation.
Ensures all required configuration is present before the app starts.
"""
import os
from typing import Optional
from dotenv import load_dotenv


class Config:
    """Application configuration with validation"""

    @staticmethod
    def load_and_validate() -> dict:
        """Load and validate all required environment variables"""
        load_dotenv()

        required_vars = {
            'HF_API_TOKEN': 'Hugging Face API token',
            'FLASK_ENV': 'Flask environment (development/production)',
        }

        optional_vars = {
            'FLASK_DEBUG': False,
            'HF_API_BASE_URL': 'https://router.huggingface.co/v1',
            'LLM_MODEL': 'meta-llama/Llama-3.1-8B-Instruct',
            'FRONTEND_URL': 'http://localhost:5173',
            'LOG_LEVEL': 'INFO',
            'HTTP_PROXY': None,
            'HTTPS_PROXY': None,
        }

        config = {}

        # Validate required variables
        missing_vars = []
        for var_name, description in required_vars.items():
            value = os.getenv(var_name)
            if not value:
                missing_vars.append(f"{var_name}: {description}")
            else:
                config[var_name] = value

        if missing_vars:
            raise ValueError(
                f"Missing required environment variables:\n" +
                "\n".join(f"  - {var}" for var in missing_vars) +
                "\nPlease set these variables in your .env file or environment."
            )

        # Load optional variables with defaults
        for var_name, default_value in optional_vars.items():
            config[var_name] = os.getenv(var_name, default_value)

        # Validate specific values
        flask_env = config['FLASK_ENV']
        if flask_env not in ['development', 'production', 'testing']:
            raise ValueError(
                f"Invalid FLASK_ENV: {flask_env}. "
                "Must be one of: development, production, testing"
            )

        return config

    @staticmethod
    def get_flask_config(config: dict) -> dict:
        """Convert environment config to Flask config"""
        return {
            'DEBUG': config['FLASK_ENV'] == 'development',
            'TESTING': config['FLASK_ENV'] == 'testing',
            'JSON_SORT_KEYS': False,
        }


# Load configuration on module import
try:
    ENVIRONMENT_CONFIG = Config.load_and_validate()
except ValueError as e:
    print(f"❌ Configuration Error: {e}")
    raise SystemExit(1)

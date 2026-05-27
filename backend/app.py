"""
Main Flask Application Factory

Entry point for the Flask application.
Responsibilities:
- Create Flask app instance
- Load and validate environment variables
- Configure logging, CORS, and error handlers
- Register API blueprints
- Define health-check endpoint
"""
import os
import logging
import logging.config
from typing import Tuple
from flask import Flask, jsonify
from flask_cors import CORS
from config import ENVIRONMENT_CONFIG, Config
from models.schemas import ErrorResponse
from models.database import db
from middleware.audit_middleware import setup_audit_middleware
from utils.rate_limiter import setup_rate_limiting

logger = logging.getLogger(__name__)


def setup_logging(config: dict) -> None:
    """Configure structured logging"""
    log_level = config.get('LOG_LEVEL', 'INFO')

    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            },
            'detailed': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': log_level,
                'formatter': 'standard',
                'stream': 'ext://sys.stdout'
            }
        },
        'root': {
            'level': log_level,
            'handlers': ['console']
        }
    }

    logging.config.dictConfig(logging_config)
    logger.info(f"Logging configured at level {log_level}")


def create_app() -> Flask:
    """
    Create and configure Flask application.

    Returns:
        Flask: Configured Flask application instance
    """
    # Setup logging first
    setup_logging(ENVIRONMENT_CONFIG)
    logger.info("Initializing Flask application")

    app = Flask(__name__)

    # Apply Flask configuration
    flask_config = Config.get_flask_config(ENVIRONMENT_CONFIG)
    app.config.update(flask_config)
    logger.info(f"Flask config: DEBUG={flask_config['DEBUG']}, TESTING={flask_config['TESTING']}")

    # Configure database (default to SQLite for development)
    db_url = os.getenv('DATABASE_URL', 'sqlite:///ticket_support.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
    }

    # Initialize database
    db.init_app(app)
    logger.info(f"Database configured: {db_url.split('@')[1] if '@' in db_url else 'sqlite'}")

    # Configure CORS
    allowed_origins = ENVIRONMENT_CONFIG.get('FRONTEND_URL', 'http://localhost:5173')
    CORS(
        app,
        resources={r"/api/*": {
            "origins": allowed_origins.split(','),
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": False,
            "max_age": 3600
        }}
    )
    logger.info(f"CORS configured for origins: {allowed_origins}")

    # Setup audit logging middleware
    setup_audit_middleware(app)
    logger.info("Audit logging middleware configured")

    # Setup rate limiting
    setup_rate_limiting(app)
    logger.info("Rate limiting configured (100 req/min per IP)")

    # Create database tables on startup
    with app.app_context():
        try:
            db.create_all()
            logger.info("Database tables initialized")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}", exc_info=True)
            raise

    # Register blueprints
    try:
        from routes.ticket_routes import ticket_bp
        from routes.analytics_routes import analytics_bp
        app.register_blueprint(ticket_bp)
        app.register_blueprint(analytics_bp)
        logger.info("API blueprints registered (ticket, analytics)")
    except Exception as e:
        logger.error(f"Failed to register blueprints: {e}", exc_info=True)
        raise

    # Health check endpoint
    @app.route('/')
    def health_check() -> Tuple[dict, int]:
        """Health check endpoint"""
        return jsonify({
            "status": "ok",
            "message": "AI Ticket Router backend is running"
        }), 200

    # Error handlers
    @app.errorhandler(404)
    def not_found(error) -> Tuple[dict, int]:
        """Handle 404 errors"""
        logger.warning(f"Route not found: {error}")
        response = ErrorResponse(
            error="Endpoint not found",
            error_code="NOT_FOUND"
        )
        return jsonify(response.model_dump()), 404

    @app.errorhandler(500)
    def internal_error(error) -> Tuple[dict, int]:
        """Handle 500 errors"""
        logger.error(f"Internal server error: {error}", exc_info=True)
        response = ErrorResponse(
            error="Internal server error",
            error_code="INTERNAL_SERVER_ERROR"
        )
        return jsonify(response.model_dump()), 500

    logger.info("Flask application created successfully")
    return app


if __name__ == '__main__':
    try:
        app = create_app()
        logger.info("Starting Flask development server on http://127.0.0.1:5001")
        app.run(debug=True, port=5001)
    except Exception as e:
        logger.error(f"Failed to start application: {e}", exc_info=True)
        raise
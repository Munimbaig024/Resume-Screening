import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from config import Config
from middleware.rate_limiter import limiter

def create_app() -> Flask:
    app = Flask(__name__, static_folder="../frontend", static_url_path="")

    # Config
    app.config["JWT_SECRET_KEY"]              = Config.JWT_SECRET_KEY
    app.config["JWT_ACCESS_TOKEN_EXPIRES"]    = Config.JWT_ACCESS_TOKEN_EXPIRES
    app.config["JWT_REFRESH_TOKEN_EXPIRES"]   = Config.JWT_REFRESH_TOKEN_EXPIRES
    app.config["JWT_TOKEN_LOCATION"]          = Config.JWT_TOKEN_LOCATION
    app.config["JWT_COOKIE_SECURE"]           = Config.JWT_COOKIE_SECURE
    app.config["JWT_COOKIE_CSRF_PROTECT"]     = Config.JWT_COOKIE_CSRF_PROTECT
    app.config["JWT_COOKIE_SAMESITE"]         = Config.JWT_COOKIE_SAMESITE
    app.config["MAX_CONTENT_LENGTH"]          = Config.MAX_UPLOAD_MB * 1024 * 1024

    # Extensions
    CORS(app, supports_credentials=True, resources={r"/api/*": {"origins": "*"}})
    JWTManager(app)
    limiter.init_app(app)

    # Register blueprints
    from routes.auth   import auth_bp
    from routes.chat   import chat_bp
    from api.resume    import resume_bp   # kept in api/ for backward compat

    app.register_blueprint(auth_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(resume_bp)

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"error": "Bad request"}), 400

    @app.errorhandler(401)
    def unauthorized(e):
        return jsonify({"error": "Unauthorized"}), 401

    @app.errorhandler(403)
    def forbidden(e):
        return jsonify({"error": "Forbidden"}), 403

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(413)
    def too_large(e):
        return jsonify({"error": f"File too large. Max {Config.MAX_UPLOAD_MB}MB"}), 413

    @app.errorhandler(429)
    def rate_limit(e):
        return jsonify({"error": "Too many requests"}), 429

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Internal server error"}), 500

    @app.route("/api/health")
    def health():
        return jsonify({"status": "ok", "version": "1.0.0"})

    @app.route("/")
    def landing():
        return send_from_directory(app.static_folder, "index.html")

    @app.route("/<path:filename>")
    def serve_file(filename):
        try:
            return send_from_directory(app.static_folder, filename)
        except Exception:
            return send_from_directory(app.static_folder, "index.html")

    return app


if __name__ == "__main__":
    from db.mongo import setup_indexes
    app = create_app()

    print(f"🚀  ResumeChecker starting → http://localhost:{Config.PORT}")
    print(f"📁  Serving frontend: {os.path.abspath('../frontend')}")
    print("⚠️   Run 'python setup_db.py' first if this is a fresh install")

    try:
        setup_indexes()
    except Exception as e:
        print(f"⚠️   MongoDB not reachable at startup: {e}")
        print("    App will still run but DB features will fail until MongoDB is available.")

    app.run(debug=Config.DEBUG, port=Config.PORT)

import logging
from connexion import FlaskApp
from connexion.middleware import MiddlewarePosition
from dotenv import load_dotenv
from os import environ as env
from flask import Response, request
from flask_jwt_extended import JWTManager
from flask_limiter.errors import RateLimitExceeded
from healthcheck import HealthCheck, EnvironmentDump
from httpproblem import problem_http_response
from prometheus_client import generate_latest
from starlette.middleware.cors import CORSMiddleware
from utils import healthchecks
from utils.logs import setup_logging
from utils.ratelimit import limiter

load_dotenv()
setup_logging("api-rest")

__version__ = "1.1.0"

# health Checks
health = HealthCheck()
dump = EnvironmentDump()
CONTENT_TYPE_LATEST = str('text/plain; version=0.0.4; charset=utf-8')

health.add_check(healthchecks.mongo_available)


# add your own data to the environment dump
def application_data():
    return {"maintainer": "David A. Mancilla",
            "git_repo": "https://github.com/dmancilla85/py-rest-server",
            "version": __version__}


dump.add_section("application", application_data)

con_app = FlaskApp(__name__, specification_dir="./")

con_app.add_middleware(
    CORSMiddleware,
    position=MiddlewarePosition.BEFORE_EXCEPTION,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

con_app.add_api("../swagger.yml")
# app = Flask(__name__)

app = con_app.app
app.app_context().push()

limiter.init_app(app)


@app.errorhandler(RateLimitExceeded)
def handle_rate_limit_exceeded(e):
    response = problem_http_response(
        429, "Too Many Requests", f"Rate limit exceeded ({e.description}).", "/api/v1"
    )
    headers = dict(response['headers'])
    headers["Retry-After"] = str(e.limit.limit.get_expiry())
    return Response(response['body'], status=response['statusCode'], headers=headers)


# Add a flask route to expose information
app.add_url_rule("/api/health", "healthcheck", view_func=lambda: health.run())
app.add_url_rule("/api/environment", "environment", view_func=lambda: dump.run())
app.add_url_rule("/api/metrics", "metrics", view_func=lambda: Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST))

app.config["JWT_SECRET_KEY"] = env.get('JWT_SECRET_KEY') or env.get('MONGODB_CONN') or "dev-secret-change-in-production"
jwt = JWTManager(app)


# for logging purposes
@app.after_request
def after_request(response):
    logging.info('%s %s %s %s %s', request.remote_addr, request.method, request.scheme, request.full_path,
                 response.status)
    return response


if __name__ == '__main__':
    port = int(env.get('PORT', 5000))
    con_app.run(host="0.0.0.0", port=port)

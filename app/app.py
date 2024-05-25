import logging
import connexion
from connexion.middleware import MiddlewarePosition
from dotenv import load_dotenv
from os import environ as env
from flask import Response, request
from flask_jwt_extended import JWTManager
from healthcheck import HealthCheck, EnvironmentDump
from prometheus_client import generate_latest
from starlette.middleware.cors import CORSMiddleware
from utils import healthchecks

load_dotenv()

# health Checks
health = HealthCheck()
dump = EnvironmentDump()
CONTENT_TYPE_LATEST = str('text/plain; version=0.0.4; charset=utf-8')

health.add_check(healthchecks.mongo_available)


# add your own data to the environment dump
def application_data():
    return {"maintainer": "David A. Mancilla",
            "git_repo": "https://github.com/dmancilla85/py-rest-server"}


dump.add_section("application", application_data)

con_app = connexion.App(__name__, specification_dir="./")

con_app.add_middleware(
    CORSMiddleware,
    position=MiddlewarePosition.BEFORE_EXCEPTION,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

con_app.add_api("../swagger.yml")
# app = Flask(__name__)

app = con_app.app
app.app_context().push()

# Add a flask route to expose information
app.add_url_rule("/api/health", "healthcheck", view_func=lambda: health.run())
app.add_url_rule("/api/environment", "environment", view_func=lambda: dump.run())
app.add_url_rule("/api/metrics", "metrics", view_func=lambda: Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST))

app.config["JWT_SECRET_KEY"] = env['MONGODB_CONN']
jwt = JWTManager(app)


# for logging purposes
@app.after_request
def after_request(response):
    logging.info('%s %s %s %s %s', request.remote_addr, request.method, request.scheme, request.full_path,
                 response.status)
    return response


if __name__ == '__main__':
    con_app.run(host="0.0.0.0", port=5000)

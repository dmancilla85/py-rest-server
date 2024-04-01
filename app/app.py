import connexion
from dotenv import load_dotenv
from os import environ as env

from flask import Response
from flask_jwt_extended import JWTManager
from healthcheck import HealthCheck, EnvironmentDump
from pymongo import MongoClient
from prometheus_client import generate_latest

load_dotenv()

# health Checks
health = HealthCheck()
envdump = EnvironmentDump()
CONTENT_TYPE_LATEST = str('text/plain; version=0.0.4; charset=utf-8')


# add your own check function to the healthcheck
def mongo_available():
    client = MongoClient(env['MONGODB_CONN'])
    info = client.server_info()
    return True, {"status": "OK", "info": str(info)}


health.add_check(mongo_available)


# add your own data to the environment dump
def application_data():
    return {"maintainer": "David A. Mancilla",
            "git_repo": "https://github.com/dmancilla85/py-rest-server"}


envdump.add_section("application", application_data)

con_app = connexion.App(__name__, specification_dir="./")
con_app.add_api("../swagger.yml")
# app = Flask(__name__)

app = con_app.app
app.app_context().push()

# Add a flask route to expose information
app.add_url_rule("/api/health", "healthcheck", view_func=lambda: health.run())
app.add_url_rule("/api/environment", "environment", view_func=lambda: envdump.run())
app.add_url_rule("/api/metrics", "metrics", view_func=lambda: Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST))

app.config["JWT_SECRET_KEY"] = env['MONGODB_CONN']
jwt = JWTManager(app)

if __name__ == '__main__':
    con_app.run(host="0.0.0.0", port=5000)

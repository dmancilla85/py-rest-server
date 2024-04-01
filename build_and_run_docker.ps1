
# cleaning
docker image prune --force

# Build image
docker build . -t "py-rest-api"

# Run and bind to port 5000
docker run --rm -p 0.0.0.0:5000:5000 py-rest-api

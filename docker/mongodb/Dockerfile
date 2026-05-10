FROM mongo:7.0

# Copy initialization script
COPY init-mongo.js /docker-entrypoint-initdb.d/

# Copy custom configuration
COPY mongod.conf /etc/mongod.conf

# Expose MongoDB port
EXPOSE 27017

CMD ["mongod", "--config", "/etc/mongod.conf"]

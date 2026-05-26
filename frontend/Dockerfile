# Frontend Dockerfile for development with hot-reload

FROM node:20-alpine

WORKDIR /app

# Set Docker environment flag
ENV DOCKER_ENV=true

# Install dependencies first (for better caching)
COPY package*.json ./
RUN npm install

# Copy source code
COPY . .

# Expose Vite dev server port
EXPOSE 3000

# Start Vite dev server with hot-reload
CMD ["npm", "run", "dev"]

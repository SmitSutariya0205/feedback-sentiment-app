# ==============================================================================
# Stage 1: Build stage — Build React static assets with Vite
# ==============================================================================
FROM node:20-alpine AS build

WORKDIR /app

# Copy package manifests first for optimal Docker layer caching
COPY package*.json ./

# Install npm dependencies cleanly
RUN npm ci

# Copy source code and build production static bundle
COPY . .
RUN npm run build

# ==============================================================================
# Stage 2: Production Stage — Serve static assets via Nginx
# ==============================================================================
FROM nginx:alpine

# Copy built HTML/JS/CSS assets from build stage to Nginx web root
COPY --from=build /app/dist /usr/share/nginx/html

# Expose HTTP port
EXPOSE 80

# Run Nginx in the foreground
CMD ["nginx", "-g", "daemon off;"]

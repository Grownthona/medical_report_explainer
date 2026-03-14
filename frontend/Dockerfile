FROM node:18-alpine AS build

WORKDIR /app

# Read build arguments and set them as environment variables
ARG VITE_API_BASE
ENV VITE_API_BASE=${VITE_API_BASE}

COPY package.json package-lock.json* ./
RUN npm ci

COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built assets
COPY --from=build /app/dist /usr/share/nginx/html

# Add try_files rule to default nginx conf to support client-side routing
RUN sed -i '10i \\ttry_files $uri $uri/ /index.html;' /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

# Build stage
FROM node:18-alpine AS builder

WORKDIR /app

COPY package*.json ./

RUN npm install

COPY . .

RUN npm run build

# Production stage
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./

# Install all dependencies for flexibility
RUN npm install

COPY --from=builder /app/dist ./dist

EXPOSE 3000

# Use environment variable to switch between dev/prod
CMD ["sh", "-c", "if [ \"$NODE_ENV\" = \"production\" ]; then npm install -g serve && serve -s dist -l 3000; else npm run dev; fi"]

# Frontend Dockerfile
FROM node:18-alpine

WORKDIR /app

# Debugging: List files in the current directory
RUN ls -la

# Copy package.json and package-lock.json before other files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy all files
COPY . .

# Build the Next.js application
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
RUN npm run build

EXPOSE 3000

# Start the application
CMD ["npm", "start"]
FROM node:18-alpine

WORKDIR /app

# copy package.json 
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application
COPY . .

# Expose the port
EXPOSE 3000

# Set the command to run the application
CMD ["npm", "run", "dev"]
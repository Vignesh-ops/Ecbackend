# Let's create all the backend files for the e-commerce application
import os

# Create the main project structure
backend_structure = {
    "package.json": '''
{
  "name": "ecommerce-backend",
  "version": "1.0.0",
  "description": "E-commerce backend API with Node.js, Express, and MongoDB",
  "main": "server.js",
  "scripts": {
    "start": "node server.js",
    "dev": "nodemon server.js",
    "build": "npm install"
  },
  "keywords": ["ecommerce", "nodejs", "express", "mongodb", "jwt"],
  "author": "Your Name",
  "license": "MIT",
  "dependencies": {
    "express": "^4.18.2",
    "mongoose": "^7.5.0",
    "bcryptjs": "^2.4.3",
    "jsonwebtoken": "^9.0.2",
    "cors": "^2.8.5",
    "dotenv": "^16.3.1",
    "multer": "^1.4.5",
    "cloudinary": "^1.40.0",
    "express-rate-limit": "^6.10.0",
    "helmet": "^7.0.0",
    "express-validator": "^7.0.1"
  },
  "devDependencies": {
    "nodemon": "^3.0.1"
  },
  "engines": {
    "node": ">=16.0.0"
  }
}
''',

    ".env": '''
# Database
MONGODB_URI=mongodb://localhost:27017/ecommerce
# Replace with your MongoDB Atlas connection string
# MONGODB_URI=mongodb+srv://<username>:<password>@cluster0.mongodb.net/ecommerce?retryWrites=true&w=majority

# JWT Secret
JWT_SECRET=your-super-secret-jwt-key-here-change-this-in-production

# Server Port
PORT=5000

# Frontend URL for CORS (Replace with your frontend URL)
FRONTEND_URL=http://localhost:3000

# Cloudinary (Optional - for image uploads)
CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=

# Node Environment
NODE_ENV=development
''',

    "server.js": '''
const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
require('dotenv').config();

// Import routes
const authRoutes = require('./routes/authRoutes');
const productRoutes = require('./routes/productRoutes');
const orderRoutes = require('./routes/orderRoutes');
const userRoutes = require('./routes/userRoutes');
const categoryRoutes = require('./routes/categoryRoutes');

// Import middleware
const { errorHandler, notFound } = require('./middleware/errorMiddleware');

const app = express();

// Security middleware
app.use(helmet());

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // limit each IP to 100 requests per windowMs
  message: 'Too many requests from this IP, please try again later.'
});
app.use(limiter);

// CORS configuration
const corsOptions = {
  origin: [
    process.env.FRONTEND_URL || 'http://localhost:3000',
    'https://your-frontend-domain.vercel.app' // Add your Vercel frontend URL here
  ],
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization']
};

app.use(cors(corsOptions));
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Connect to MongoDB
mongoose.connect(process.env.MONGODB_URI, {
  useNewUrlParser: true,
  useUnifiedTopology: true,
})
.then(() => console.log('MongoDB connected successfully'))
.catch((err) => console.error('MongoDB connection error:', err));

// Health check route
app.get('/', (req, res) => {
  res.json({
    message: 'E-commerce API is running!',
    version: '1.0.0',
    status: 'healthy'
  });
});

// API Routes
app.use('/api/auth', authRoutes);
app.use('/api/products', productRoutes);
app.use('/api/orders', orderRoutes);
app.use('/api/users', userRoutes);
app.use('/api/categories', categoryRoutes);

// Error handling middleware
app.use(notFound);
app.use(errorHandler);

const PORT = process.env.PORT || 5000;

app.listen(PORT, () => {
  console.log(`Server running in ${process.env.NODE_ENV} mode on port ${PORT}`);
});

module.exports = app;
''',

    "vercel.json": '''
{
  "version": 2,
  "builds": [
    {
      "src": "./server.js",
      "use": "@vercel/node"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "/"
    }
  ],
  "env": {
    "MONGODB_URI": "@mongodb_uri",
    "JWT_SECRET": "@jwt_secret",
    "NODE_ENV": "production"
  }
}
''',

    "config/database.js": '''
const mongoose = require('mongoose');

const connectDB = async () => {
  try {
    const conn = await mongoose.connect(process.env.MONGODB_URI, {
      useNewUrlParser: true,
      useUnifiedTopology: true,
    });

    console.log(`MongoDB Connected: ${conn.connection.host}`);
  } catch (error) {
    console.error(`Error: ${error.message}`);
    process.exit(1);
  }
};

module.exports = connectDB;
'''
}

# Create the files
for file_path, content in backend_structure.items():
    # Create directory if it doesn't exist
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)
    
    # Write the file
    with open(file_path, 'w') as f:
        f.write(content.strip())

print("Created basic project structure files:")
for file_path in backend_structure.keys():
    print(f"✓ {file_path}")
# Create controllers
controllers = {
    "controllers/authController.js": '''
const User = require('../models/User');
const { generateToken } = require('../utils/generateToken');
const { sendSuccess, sendError, sendBadRequest, sendUnauthorized } = require('../utils/apiResponse');

// @desc    Register new user
// @route   POST /api/auth/register
// @access  Public
const registerUser = async (req, res) => {
  try {
    const { name, email, password } = req.body;

    // Check if user exists
    const userExists = await User.findOne({ email });
    if (userExists) {
      return sendBadRequest(res, 'User already exists with this email');
    }

    // Create user
    const user = await User.create({
      name,
      email,
      password,
    });

    if (user) {
      const token = generateToken(user._id);
      
      // Set cookie
      res.cookie('token', token, {
        httpOnly: true,
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'strict',
        maxAge: 30 * 24 * 60 * 60 * 1000 // 30 days
      });

      return sendSuccess(res, 'User registered successfully', {
        _id: user._id,
        name: user.name,
        email: user.email,
        role: user.role,
        token
      }, 201);
    } else {
      return sendError(res, 'Invalid user data', 400);
    }
  } catch (error) {
    console.error('Register error:', error);
    return sendError(res, 'Server error during registration');
  }
};

// @desc    Authenticate user & get token
// @route   POST /api/auth/login
// @access  Public
const loginUser = async (req, res) => {
  try {
    const { email, password } = req.body;

    // Check for user email and include password
    const user = await User.findOne({ email }).select('+password');

    if (user && (await user.matchPassword(password))) {
      // Update last login
      await User.findByIdAndUpdate(user._id, { lastLogin: new Date() });

      const token = generateToken(user._id);
      
      // Set cookie
      res.cookie('token', token, {
        httpOnly: true,
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'strict',
        maxAge: 30 * 24 * 60 * 60 * 1000 // 30 days
      });

      return sendSuccess(res, 'Login successful', {
        _id: user._id,
        name: user.name,
        email: user.email,
        role: user.role,
        avatar: user.avatar,
        token
      });
    } else {
      return sendUnauthorized(res, 'Invalid email or password');
    }
  } catch (error) {
    console.error('Login error:', error);
    return sendError(res, 'Server error during login');
  }
};

// @desc    Logout user / clear cookie
// @route   POST /api/auth/logout
// @access  Private
const logoutUser = (req, res) => {
  res.cookie('token', '', {
    httpOnly: true,
    expires: new Date(0),
  });
  
  return sendSuccess(res, 'Logged out successfully');
};

// @desc    Get user profile
// @route   GET /api/auth/profile
// @access  Private
const getUserProfile = async (req, res) => {
  try {
    const user = await User.findById(req.user._id);
    
    if (user) {
      return sendSuccess(res, 'Profile retrieved successfully', user);
    } else {
      return sendError(res, 'User not found', 404);
    }
  } catch (error) {
    console.error('Get profile error:', error);
    return sendError(res, 'Server error retrieving profile');
  }
};

// @desc    Update user profile
// @route   PUT /api/auth/profile
// @access  Private
const updateUserProfile = async (req, res) => {
  try {
    const user = await User.findById(req.user._id);

    if (user) {
      user.name = req.body.name || user.name;
      user.email = req.body.email || user.email;
      user.phone = req.body.phone || user.phone;
      user.avatar = req.body.avatar || user.avatar;
      
      if (req.body.address) {
        user.address = { ...user.address, ...req.body.address };
      }

      if (req.body.password) {
        user.password = req.body.password;
      }

      const updatedUser = await user.save();

      return sendSuccess(res, 'Profile updated successfully', {
        _id: updatedUser._id,
        name: updatedUser.name,
        email: updatedUser.email,
        role: updatedUser.role,
        phone: updatedUser.phone,
        avatar: updatedUser.avatar,
        address: updatedUser.address
      });
    } else {
      return sendError(res, 'User not found', 404);
    }
  } catch (error) {
    console.error('Update profile error:', error);
    return sendError(res, 'Server error updating profile');
  }
};

module.exports = {
  registerUser,
  loginUser,
  logoutUser,
  getUserProfile,
  updateUserProfile,
};
''',

    "controllers/productController.js": '''
const Product = require('../models/Product');
const Category = require('../models/Category');
const { sendSuccess, sendError, sendNotFound, sendCreated } = require('../utils/apiResponse');

// @desc    Get all products with filtering, sorting and pagination
// @route   GET /api/products
// @access  Public
const getProducts = async (req, res) => {
  try {
    const page = parseInt(req.query.page) || 1;
    const limit = parseInt(req.query.limit) || 12;
    const skip = (page - 1) * limit;

    // Build query object
    let query = {};

    // Filtering
    if (req.query.category) {
      query.category = req.query.category;
    }

    if (req.query.brand) {
      query.brand = new RegExp(req.query.brand, 'i');
    }

    if (req.query.featured) {
      query.featured = req.query.featured === 'true';
    }

    if (req.query.status) {
      query.status = req.query.status;
    } else {
      query.status = 'active'; // Default to active products
    }

    // Price range
    if (req.query.minPrice || req.query.maxPrice) {
      query.price = {};
      if (req.query.minPrice) query.price.$gte = parseFloat(req.query.minPrice);
      if (req.query.maxPrice) query.price.$lte = parseFloat(req.query.maxPrice);
    }

    // Search
    if (req.query.search) {
      query.$text = { $search: req.query.search };
    }

    // Sorting
    let sortOptions = {};
    if (req.query.sort) {
      const sortField = req.query.sort.startsWith('-') 
        ? req.query.sort.substring(1) 
        : req.query.sort;
      const sortOrder = req.query.sort.startsWith('-') ? -1 : 1;
      sortOptions[sortField] = sortOrder;
    } else {
      sortOptions.createdAt = -1; // Default sort by newest
    }

    // Execute query
    const products = await Product.find(query)
      .populate('category', 'name slug')
      .populate('createdBy', 'name')
      .sort(sortOptions)
      .skip(skip)
      .limit(limit);

    const total = await Product.countDocuments(query);
    const totalPages = Math.ceil(total / limit);

    return sendSuccess(res, 'Products retrieved successfully', products, 200, {
      pagination: {
        current: page,
        pages: totalPages,
        total,
        hasNext: page < totalPages,
        hasPrev: page > 1
      }
    });
  } catch (error) {
    console.error('Get products error:', error);
    return sendError(res, 'Server error retrieving products');
  }
};

// @desc    Get single product
// @route   GET /api/products/:id
// @access  Public
const getProductById = async (req, res) => {
  try {
    const product = await Product.findById(req.params.id)
      .populate('category', 'name slug')
      .populate('createdBy', 'name')
      .populate('reviews.user', 'name avatar');

    if (product) {
      return sendSuccess(res, 'Product retrieved successfully', product);
    } else {
      return sendNotFound(res, 'Product not found');
    }
  } catch (error) {
    console.error('Get product error:', error);
    return sendError(res, 'Server error retrieving product');
  }
};

// @desc    Create a product
// @route   POST /api/products
// @access  Private/Admin
const createProduct = async (req, res) => {
  try {
    const {
      name,
      description,
      price,
      discountPrice,
      images,
      category,
      brand,
      stock,
      specifications,
      tags,
      featured
    } = req.body;

    // Verify category exists
    const categoryExists = await Category.findById(category);
    if (!categoryExists) {
      return sendError(res, 'Category not found', 404);
    }

    const product = new Product({
      name,
      description,
      price,
      discountPrice,
      images,
      category,
      brand,
      stock,
      specifications,
      tags,
      featured,
      createdBy: req.user._id,
    });

    const createdProduct = await product.save();
    await createdProduct.populate('category', 'name slug');

    return sendCreated(res, 'Product created successfully', createdProduct);
  } catch (error) {
    console.error('Create product error:', error);
    return sendError(res, 'Server error creating product');
  }
};

// @desc    Update a product
// @route   PUT /api/products/:id
// @access  Private/Admin
const updateProduct = async (req, res) => {
  try {
    const product = await Product.findById(req.params.id);

    if (product) {
      const {
        name,
        description,
        price,
        discountPrice,
        images,
        category,
        brand,
        stock,
        specifications,
        tags,
        featured,
        status
      } = req.body;

      product.name = name || product.name;
      product.description = description || product.description;
      product.price = price || product.price;
      product.discountPrice = discountPrice || product.discountPrice;
      product.images = images || product.images;
      product.category = category || product.category;
      product.brand = brand || product.brand;
      product.stock = stock !== undefined ? stock : product.stock;
      product.specifications = specifications || product.specifications;
      product.tags = tags || product.tags;
      product.featured = featured !== undefined ? featured : product.featured;
      product.status = status || product.status;

      const updatedProduct = await product.save();
      await updatedProduct.populate('category', 'name slug');

      return sendSuccess(res, 'Product updated successfully', updatedProduct);
    } else {
      return sendNotFound(res, 'Product not found');
    }
  } catch (error) {
    console.error('Update product error:', error);
    return sendError(res, 'Server error updating product');
  }
};

// @desc    Delete a product
// @route   DELETE /api/products/:id
// @access  Private/Admin
const deleteProduct = async (req, res) => {
  try {
    const product = await Product.findById(req.params.id);

    if (product) {
      await Product.findByIdAndDelete(req.params.id);
      return sendSuccess(res, 'Product deleted successfully');
    } else {
      return sendNotFound(res, 'Product not found');
    }
  } catch (error) {
    console.error('Delete product error:', error);
    return sendError(res, 'Server error deleting product');
  }
};

// @desc    Create new review
// @route   POST /api/products/:id/reviews
// @access  Private
const createProductReview = async (req, res) => {
  try {
    const { rating, comment } = req.body;
    const product = await Product.findById(req.params.id);

    if (product) {
      const alreadyReviewed = product.reviews.find(
        (r) => r.user.toString() === req.user._id.toString()
      );

      if (alreadyReviewed) {
        return sendError(res, 'Product already reviewed', 400);
      }

      const review = {
        name: req.user.name,
        rating: Number(rating),
        comment,
        user: req.user._id,
      };

      product.reviews.push(review);
      product.numOfReviews = product.reviews.length;
      product.ratings =
        product.reviews.reduce((acc, item) => item.rating + acc, 0) /
        product.reviews.length;

      await product.save();
      return sendCreated(res, 'Review added successfully');
    } else {
      return sendNotFound(res, 'Product not found');
    }
  } catch (error) {
    console.error('Create review error:', error);
    return sendError(res, 'Server error creating review');
  }
};

module.exports = {
  getProducts,
  getProductById,
  createProduct,
  updateProduct,
  deleteProduct,
  createProductReview,
};
'''
}

# Create controller files
for file_path, content in controllers.items():
    # Create directory if it doesn't exist
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)
    
    # Write the file
    with open(file_path, 'w') as f:
        f.write(content.strip())

print("Created controller files:")
for file_path in controllers.keys():
    print(f"✓ {file_path}")
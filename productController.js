const Product = require('../models/Product');
const Category = require('../models/Category');
const { sendSuccess, sendError, sendNotFound, sendCreated } = require('./utils/apiResponse');

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
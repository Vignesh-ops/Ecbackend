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
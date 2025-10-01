// Standard API response format
const sendResponse = (res, statusCode, success, message, data = null, meta = null) => {
  const response = {
    success,
    message,
    ...(data && { data }),
    ...(meta && { meta })
  };

  return res.status(statusCode).json(response);
};

// Success responses
const sendSuccess = (res, message, data = null, statusCode = 200) => {
  return sendResponse(res, statusCode, true, message, data);
};

const sendCreated = (res, message, data = null) => {
  return sendResponse(res, 201, true, message, data);
};

// Error responses
const sendError = (res, message, statusCode = 500, data = null) => {
  return sendResponse(res, statusCode, false, message, data);
};

const sendBadRequest = (res, message = 'Bad Request', data = null) => {
  return sendResponse(res, 400, false, message, data);
};

const sendUnauthorized = (res, message = 'Unauthorized') => {
  return sendResponse(res, 401, false, message);
};

const sendForbidden = (res, message = 'Forbidden') => {
  return sendResponse(res, 403, false, message);
};

const sendNotFound = (res, message = 'Resource not found') => {
  return sendResponse(res, 404, false, message);
};

module.exports = {
  sendResponse,
  sendSuccess,
  sendCreated,
  sendError,
  sendBadRequest,
  sendUnauthorized,
  sendForbidden,
  sendNotFound
};
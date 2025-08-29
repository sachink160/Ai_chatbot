# Multi-Tool Chatbot API Documentation

## Overview
The Multi-Tool Chatbot is a comprehensive AI-powered application that provides document analysis, HR document processing, video-to-audio conversion, AI chat capabilities, and subscription management. This API is built with FastAPI and includes authentication, rate limiting based on subscription plans, and various AI-powered tools.

## Base URL
```
http://localhost:8000
```

## Authentication
All protected endpoints require authentication using Bearer tokens. Include the access token in the Authorization header:
```
Authorization: Bearer <access_token>
```

---

## 1. Authentication & User Management

### 1.1 User Registration
**POST** `/register`

Register a new user account.

**Request Body:**
```json
{
  "username": "string",
  "fullname": "string", 
  "email": "string",
  "phone": "string",
  "user_type": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "message": "User registered successfully"
}
```

### 1.2 User Login
**POST** `/login`

Authenticate user and receive access/refresh tokens.

**Request Body (Form Data):**
```
username: string
password: string
```

**Response:**
```json
{
  "access_token": "string",
  "refresh_token": "string",
  "user": {
    "id": "string",
    "username": "string",
    "fullname": "string",
    "email": "string",
    "phone": "string",
    "user_type": "string",
    "is_subscribed": boolean,
    "subscription_end_date": "datetime"
  }
}
```

### 1.3 Refresh Token
**POST** `/refresh`

Get new access and refresh tokens using existing refresh token.

**Request Body:**
```json
{
  "refresh_token": "string"
}
```

**Response:**
```json
{
  "access_token": "string",
  "refresh_token": "string"
}
```

### 1.4 User Logout
**POST** `/logout`

Logout user and blacklist refresh token.

**Request Body:**
```json
{
  "refresh_token": "string"
}
```

**Response:**
```json
{
  "message": "User logged out. Refresh token blacklisted."
}
```

### 1.5 Get User Profile
**GET** `/profile`

Get comprehensive user profile with subscription and usage information.

**Response:**
```json
{
  "id": "string",
  "username": "string",
  "fullname": "string",
  "email": "string",
  "phone": "string",
  "user_type": "string",
  "is_subscribed": boolean,
  "subscription_end_date": "datetime",
  "current_usage": {
    "month_year": "string",
    "chats_used": integer,
    "documents_uploaded": integer,
    "hr_documents_uploaded": integer,
    "video_uploads": integer,
    "max_chats": integer,
    "max_documents": integer,
    "max_hr_documents": integer,
    "max_video_uploads": integer
  }
}
```

---

## 2. AI ChatBot

### 2.1 Chat with AI
**POST** `/chat`

Send a message to the AI chatbot and receive a response.

**Request Body:**
```
query: string
```

**Response:**
```json
{
  "response": "string",
  "usage": {
    "chats_used": integer,
    "max_chats": integer,
    "remaining": integer
  }
}
```

### 2.2 Get Chat History
**GET** `/chat/history`

Retrieve user's chat history.

**Response:**
```json
[
  {
    "message": "string",
    "response": "string",
    "tool_used": ["string"],
    "timestamp": "datetime"
  }
]
```

---

## 3. Document Analysis (RAG)

### 3.1 Upload Document
**POST** `/upload`

Upload a document for analysis (PDF, DOC, TXT, etc.).

**Request Body:**
```
file: UploadFile
```

**Response:**
```json
{
  "message": "File uploaded",
  "document_id": integer,
  "usage": {
    "documents_uploaded": integer,
    "max_documents": integer,
    "remaining": integer
  }
}
```

### 3.2 List Documents
**GET** `/documents`

Get list of user's uploaded documents.

**Response:**
```json
[
  {
    "id": integer,
    "filename": "string"
  }
]
```

### 3.3 Ask Question About Document
**POST** `/ask`

Ask questions about uploaded documents using AI-powered analysis.

**Request Body:**
```json
{
  "document_id": "string",
  "question": "string",
  "prompt_type": "string", // "summarize", "critical_issues", "action_items", "custom"
  "custom_query": "string" // Required if prompt_type is "custom"
}
```

**Response:**
```json
{
  "answer": "string"
}
```

**Available Prompt Types:**
- `summarize`: Document summary
- `critical_issues`: Extract critical legal/compliance issues
- `action_items`: Extract action items
- `custom`: Custom query analysis

---

## 4. HR Document Management

### 4.1 Upload HR Document
**POST** `/hr/upload`

Upload HR-related documents for analysis.

**Request Body:**
```
file: UploadFile
```

**Response:**
```json
{
  "message": "Hr File uploaded",
  "document_id": integer,
  "usage": {
    "hr_documents_uploaded": integer,
    "max_hr_documents": integer,
    "remaining": integer
  }
}
```

### 4.2 List HR Documents
**GET** `/hr/documents`

Get list of user's HR documents.

**Response:**
```json
[
  {
    "id": "string",
    "filename": "string",
    "is_active": boolean
  }
]
```

### 4.3 Activate HR Document
**POST** `/hr/documents/{doc_id}/activate`

Activate a specific HR document (deactivates all others).

**Response:**
```json
{
  "message": "Activated document: {filename}"
}
```

### 4.4 Deactivate HR Document
**POST** `/hr/documents/{doc_id}/deactivate`

Deactivate a specific HR document.

**Response:**
```json
{
  "message": "Deactivated document: {filename}"
}
```

### 4.5 Ask HR Document Question
**POST** `/hr/ask`

Ask questions about the active HR document.

**Request Body:**
```json
{
  "question": "string"
}
```

**Response:**
```json
{
  "question": "string",
  "answer": "string",
  "document": "string"
}
```

---

## 5. Video to Audio Conversion

### 5.1 Upload Video
**POST** `/video-to-audio/upload`

Upload a video file for processing (converts to 720p and extracts audio).

**Request Body:**
```
file: UploadFile (MP4, MOV, AVI, MKV)
```

**Response:**
```json
{
  "video_url": "string",
  "audio_url": "string",
  "usage": {
    "video_uploads": integer,
    "max_video_uploads": integer,
    "remaining": integer
  }
}
```

### 5.2 List Uploaded Files
**GET** `/video-to-audio/uploads`

Get list of user's uploaded video files.

**Response:**
```json
{
  "uploads": ["string"]
}
```

### 5.3 List Processed Files
**GET** `/video-to-audio/processed`

Get list of user's processed video/audio files.

**Response:**
```json
{
  "processed": ["string"]
}
```

### 5.4 Download Processed File
**GET** `/video-to-audio/download/{user_id}/{filename}`

Download a processed video or audio file.

**Response:** File download

---

## 6. Subscription Management

### 6.1 Get Subscription Plans
**GET** `/plans`

Get all available subscription plans.

**Response:**
```json
[
  {
    "id": "string",
    "name": "string",
    "price": float,
    "duration_days": integer,
    "max_chats_per_month": integer,
    "max_documents": integer,
    "max_hr_documents": integer,
    "max_video_uploads": integer,
    "features": "string",
    "is_active": boolean
  }
]
```

### 6.2 Get User Subscription
**GET** `/user/subscription`

Get current user's active subscription.

**Response:**
```json
{
  "id": "string",
  "plan_name": "string",
  "start_date": "datetime",
  "end_date": "datetime",
  "status": "string",
  "payment_status": "string",
  "features": "string"
}
```

### 6.3 Get Subscription History
**GET** `/user/subscription/history`

Get user's complete subscription history.

**Response:** Array of subscription objects (same structure as above)

### 6.4 Get User Usage
**GET** `/user/usage`

Get current user's usage statistics.

**Response:**
```json
{
  "month_year": "string",
  "chats_used": integer,
  "documents_uploaded": integer,
  "hr_documents_uploaded": integer,
  "video_uploads": integer,
  "max_chats": integer,
  "max_documents": integer,
  "max_hr_documents": integer,
  "max_video_uploads": integer
}
```

### 6.5 Subscribe to Plan
**POST** `/subscribe`

Subscribe user to a subscription plan.

**Request Body:**
```json
{
  "plan_id": "string"
}
```

**Response:**
```json
{
  "message": "Successfully subscribed to {plan_name} plan",
  "plan_name": "string",
  "end_date": "datetime",
  "features": "string"
}
```

### 6.6 Cancel Subscription
**POST** `/cancel`

Cancel current user's subscription.

**Response:**
```json
{
  "message": "Subscription cancelled successfully"
}
```

### 6.7 Initialize Subscription Plans
**POST** `/initialize-plans`

Initialize default subscription plans (admin only).

**Response:**
```json
{
  "message": "Subscription plans initialized successfully"
}
```

---

## 7. Error Responses

### Standard Error Format
```json
{
  "detail": "Error message description"
}
```

### Common HTTP Status Codes
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden (subscription limits exceeded)
- `404` - Not Found
- `500` - Internal Server Error

### Subscription Limit Errors
When users exceed their subscription limits, endpoints return:
```json
{
  "detail": "Limit reached message with current usage and limits"
}
```

---

## 8. Rate Limiting & Subscription Tiers

The API implements usage-based rate limiting based on user subscription plans:

- **Free Tier**: Limited access to basic features
- **Premium Plans**: Increased limits for chats, document uploads, HR documents, and video processing
- **Usage Tracking**: All API calls are tracked and count against monthly limits
- **Real-time Validation**: Subscription limits are checked before processing requests

---

## 9. File Upload Limits

- **Document Uploads**: PDF, DOC, DOCX, TXT, and other text-based formats
- **Video Uploads**: MP4, MOV, AVI, MKV (converted to 720p + audio extraction)
- **File Size**: Determined by server configuration
- **Storage**: User-specific folders with UUID-based naming

---

## 10. AI Models & Processing

- **Chat Model**: OpenAI GPT-4 or Ollama (configurable)
- **Document Analysis**: LlamaIndex with vector embeddings
- **HR Analysis**: Specialized prompts for HR document analysis
- **Video Processing**: FFmpeg-based conversion and audio extraction

---

## 11. Development & Testing

### Running the API
```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
uvicorn app.main:app --reload

# Access interactive docs
http://localhost:8000/docs
```

### Environment Variables
- Database connection strings
- OpenAI API keys
- JWT secret keys
- File storage paths

---

## 12. Database Schema

The application uses PostgreSQL with the following main tables:
- `users` - User accounts and profiles
- `subscription_plans` - Available subscription tiers
- `user_subscriptions` - User subscription records
- `documents` - Uploaded documents
- `hr_documents` - HR-specific documents
- `chat_history` - AI chat conversations
- `usage_tracking` - Monthly usage statistics

---

## 13. Security Features

- JWT-based authentication with access/refresh tokens
- Password hashing using bcrypt
- Token blacklisting for logout
- User-specific file access control
- Subscription-based rate limiting
- CORS middleware configuration

---

## 14. Monitoring & Logging

- Structured logging with configurable levels
- Usage tracking for subscription management
- Error logging and monitoring
- Scheduled tasks (news agent, subscription management)

---

This API provides a comprehensive suite of AI-powered tools with proper authentication, subscription management, and usage tracking. All endpoints are designed to work together to provide a seamless user experience while maintaining proper access controls and resource management.

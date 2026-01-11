# Hodler Backend

Backend infrastructure for Hodler - a cryptocurrency trading simulator mobile app.

## Architecture

Serverless backend built on AWS using:

-   **Lambda Functions**: Node.js for API endpoints
-   **API Gateway**: REST API routing
-   **DynamoDB**: NoSQL database for users and leaderboards
-   **Infrastructure**: Manual deployment (Terraform coming in Week 7-8)

## API Endpoints

### Authentication

-   `POST /auth/register` - Create new user account
-   `POST /auth/login` - User login with JWT token

### User Management

-   `GET /users/{id}/profile` - Fetch user profile
-   `PUT /users/{id}/profile` - Update user profile

### Leaderboards (Coming Week 4-5)

-   `POST /leaderboards/submit` - Submit portfolio score
-   `GET /leaderboards/global` - Get global rankings
-   `GET /leaderboards/{userId}/rank` - Get user's rank

## Development Setup

### Prerequisites

-   Node.js 20+
-   Python 3.12+
-   AWS CLI configured
-   AWS account with IAM user (not root)

### AWS CLI Configuration

```bash
aws configure
# Enter your IAM user access keys
# Region: us-east-1
# Output: json
```

### Install Dependencies (per Lambda)

```bash
cd lambda-functions/registerUser
npm install
```

## Security

### AWS Account Protection

-   ✅ MFA enabled on root + IAM user
-   ✅ Billing alerts at different dollar levels
-   ✅ IAM user with AdministratorAccess (for learning)
-   ✅ Service throttling configured
-   ✅ Emergency teardown scripts

### Credentials

**NEVER commit to Git:**

-   AWS access keys
-   JWT secrets
-   `.env` files
-   `.zip` deployment packages

### Emergency Teardown

If AWS costs spike unexpectedly:

**Bash:**

```bash
./scripts/teardown.sh
# Type "DELETE" to confirm
```

**PowerShell:**

```powershell
.\scripts\teardown.ps1
# Type "DELETE" to confirm
```

Deletes all Lambda functions, API Gateways, and DynamoDB tables.

## DynamoDB Schema

### Users Table

```
Users
├── userId (String, PK)       - Unique user ID
├── email (String)            - User email
├── passwordHash (String)     - Bcrypt hashed password
├── username (String)         - Display name
├── createdAt (String)        - ISO timestamp
└── updatedAt (String)        - ISO timestamp
```

### Leaderboards Table (Coming Week 4-5)

```
Leaderboards
├── userId (String, PK)
├── portfolioValue (Number)
├── rank (Number)
├── percentGain (Number)
└── updatedAt (String)
```

## Testing

### Postman

1. Import collection: `postman/Hodler_API.postman_collection.json`
2. Register a new user
3. Copy the token from response
4. Use token in Authorization header for protected endpoints

### Manual Testing

```bash
# Test Lambda locally (requires AWS SAM - optional)
sam local invoke registerUser -e test-event.json

# Test via API Gateway
curl -X POST https://YOUR_API_URL/prod/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"pass123"}'
```

## Cost Monitoring

**Expected monthly costs (within aws free tier):**

-   Lambda: $0 (1M requests free)
-   API Gateway: $0 (1M calls free)
-   DynamoDB: $0 (25GB + 200M requests free)
-   **Total: $0/month** (for learning/development)

**Monitor costs:**

```bash
# Check current month-to-date spend
aws ce get-cost-and-usage \
  --time-period Start=2025-11-01,End=2025-11-30 \
  --granularity MONTHLY \
  --metrics "UnblendedCost"
```

Or visit: AWS Console → Billing Dashboard

## Deployment Notes

### Lambda Deployment

#### Node.js Lambdas

1. Package function with dependencies:

```bash
    cd lambda-functions/functionName
    npm install
    zip -r functionName.zip .
```

2. Upload via AWS Console:

    - Lambda → Function → Code → Upload from .zip

3. Configure:
    - Runtime: Node.js 20.x
    - Timeout: 30 seconds
    - Memory: 256 MB
    - Environment variables (if needed)

#### Python Lambdas

**Prerequisites:**

-   Docker Desktop installed and running

1. Package function with dependencies (using Docker for Linux compatibility):

```powershell
    # In PowerShell, navigate to lambda function directory
    cd lambda-functions/functionName

    # Run build script
    .\build.ps1

    # Or manually:
    docker run --rm -v ${PWD}:/var/task python:3.14-slim pip install -r /var/task/requirements.txt -t /var/task/package/
    Copy-Item lambda_function.py, models.py package/ -Force
    cd package
    Compress-Archive -Path * -DestinationPath ../functionName.zip -Force
    cd ..
```

2. Upload via AWS Console:

    - Lambda → Function → Code → Upload from .zip
    - Note: Package may be 10-20MB due to dependencies like Pydantic

3. Configure:
    - Runtime: Python 3.14
    - Handler: lambda_function.lambda_handler
    - Timeout: 30 seconds
    - Memory: 256 MB
    - Environment variables:
        - `JWT_SECRET`: (same value across all auth Lambdas)

**Why Docker?**
Python packages with compiled dependencies (like Pydantic) must be built for Linux (Lambda's runtime environment). Docker ensures cross-platform compatibility.

**Build Script:**
Each Python Lambda includes a `build.ps1` script for easy rebuilding:

```powershell
.\build.ps1  # Creates functionName.zip ready for upload
```

### API Gateway Deployment

1. Create resources and methods in Console
2. Deploy to stage: `prod`
3. Note Invoke URL for frontend

## Learning Context

This backend is part of an 8-week learning project to build full-stack web development skills:

-   **Week 1**: React landing page
-   **Week 2**: AWS Lambda + DynamoDB
-   **Week 3**: Redux state management
-   **Week 4**: Leaderboard backend (current)
-   **Week 5**: Terraform + CI/CD
-   **Week 6**: Production deployment + polish

Coming from Android development (Kotlin, Jetpack Compose), this project translates mobile patterns to web/cloud architecture.

## Development Checklist

### Week 2 (Nov 10-16, 2025) ✅

-   [x] AWS account setup (MFA, IAM, billing alerts, CLI)
-   [x] DynamoDB Users table + helloWorld Lambda
-   [x] User registration (registerUser Lambda, bcrypt, validation)
-   [x] User login (loginUser Lambda, JWT generation)
-   [x] User profile operations (getUserProfile, updateUserProfile Lambdas)
-   [x] API Gateway endpoints (GET/POST /auth, GET/PUT /users/{id}/profile)
-   [x] Postman collection + API documentation

### Week 4 (Dec 16-22, 2025) ✅

-   [x] SNS topic + sendWelcomeEmail Lambda (Python)
-   [x] Email verification (generateVerificationToken, verifyEmail Lambdas)
-   [x] Upload profile picture lambdas (Python)
-   [x] SQS queue + processImage Lambda (Python)
-   [x] EventBridge cron + cleanUpOldUploads Lambda (Python)
-   [x] S3 bucket + generateUploadUrl Lambda (Python) for profile pictures

### Week 5 (Dec 23-29, 2025)

-   [ ] Terraform modules (Lambda, DynamoDB, API Gateway, SNS, SQS, EventBridge, S3)
-   [ ] Terraform workspaces (dev/prod)
-   [ ] GitHub Actions deployment automation
-   [ ] AWS Secrets Manager for sensitive values
-   [ ] Convert getUserProfile to Python (remove email from response)
-   [ ] OAuth architecture documentation

### Tech Debt

-   [ ] DynamoDB GSI on email attribute + refactor getUserProfile to use GSI
-   [ ] Add JWT auth to generateUploadUrl

## API Endpoints

Base URL: `https://5bnu3oi26m.execute-api.us-east-1.amazonaws.com/prod`

### Authentication

#### Register User

```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "username": "MyUsername"
}
```

**Response (201):**

```json
{
    "message": "User registered successfully",
    "token": "eyJhbGci...",
    "userId": "user-abc123",
    "username": "MyUsername"
}
```

#### Login

```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response (200):**

```json
{
    "message": "Login successful",
    "token": "eyJhbGci...",
    "userId": "user-abc123",
    "username": "MyUsername"
}
```

### User Profile

#### Get Profile

```http
GET /users/{userId}/profile
```

**Response (200):**

```json
{
    "userId": "user-abc123",
    "email": "user@example.com",
    "username": "MyUsername",
    "createdAt": "2024-12-10T12:00:00Z",
    "updatedAt": "2024-12-10T12:00:00Z"
}
```

#### Update Profile

```http
PUT /users/{userId}/profile
Authorization: Bearer
Content-Type: application/json

{
  "username": "NewUsername"
}
```

**Response (200):**

```json
{
    "message": "Profile updated successfully",
    "user": {
        "userId": "user-abc123",
        "email": "user@example.com",
        "username": "NewUsername",
        "createdAt": "2024-12-10T12:00:00Z",
        "updatedAt": "2024-12-10T13:00:00Z"
    }
}
```

### Error Responses

#### 400 Bad Request

```json
{
    "error": "Invalid email format"
}
```

#### 401 Unauthorized

```json
{
    "error": "Token expired"
}
```

#### 403 Forbidden

```json
{
    "error": "Not authorized to update this profile"
}
```

#### 409 Conflict

```json
{
    "error": "Email already registered"
}
```

#### 500 Internal Server Error

```json
{
    "error": "Internal server error"
}
```

## Password Requirements

-   Minimum 8 characters
-   At least one uppercase letter
-   At least one lowercase letter
-   At least one number
-   At least one special character (!@#$%^&\*...)

## Related Repositories

-   [hodler-landing](https://github.com/luisdelae/hodler-landing) - React frontend (marketing site)
-   [hodler-android](https://github.com/luisdelae/hodler-android) - V1 Complete | V2 In Progress

## Author

**Luis De La Espriella**

[GitHub](https://github.com/luisdelae) • [LinkedIn](https://linkedin.com/in/luisdelaespriella)

---

**Status**: 🚧 In Active Development 🚧

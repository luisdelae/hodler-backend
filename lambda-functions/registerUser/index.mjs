import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import {
    DynamoDBDocumentClient,
    PutCommand,
    ScanCommand,
} from '@aws-sdk/lib-dynamodb';
import bcrypt from 'bcryptjs';
import { v4 as uuidv4 } from 'uuid';
import jwt from 'jsonwebtoken';

const client = new DynamoDBClient({});
const dynamodb = DynamoDBDocumentClient.from(client);
const TABLE_NAME = 'Users';
const JWT_SECRET = process.env.JWT_SECRET || 'dev-secret-change-in-production';

/**
 * Validates password strength
 * @param {string} password - Password to validate
 * @returns {object|null} - Error object if invalid, null if valid
 */
function validatePassword(password) {
    if (!password) {
        return { error: 'Password is required' };
    }

    if (password.length < 8) {
        return { error: 'Password must be at least 8 characters long' };
    }

    if (!/[A-Z]/.test(password)) {
        return { error: 'Password must contain at least one uppercase letter' };
    }

    if (!/[a-z]/.test(password)) {
        return { error: 'Password must contain at least one lowercase letter' };
    }

    if (!/\d/.test(password)) {
        return { error: 'Password must contain at least one number' };
    }

    if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
        return {
            error: 'Password must contain at least one special character (!@#$%^&*...)',
        };
    }

    return null;
}

export const handler = async (event) => {
    console.log('Event: ', JSON.stringify(event, null, 2));

    let body;

    try {
        body = JSON.parse(event.body);
    } catch (err) {
        return {
            statusCode: 400,
            headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            body: JSON.stringify({ error: 'Invalid JSON in request body' }),
        };
    }

    const { email, password, username } = body;

    if (!email) {
        return {
            statusCode: 400,
            headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            body: JSON.stringify({ error: 'Email is required' }),
        };
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        return {
            statusCode: 400,
            headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            body: JSON.stringify({ error: 'Invalid email format' }),
        };
    }

    const passwordError = validatePassword(password);
    if (passwordError) {
        return {
            statusCode: 400,
            headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            body: JSON.stringify(passwordError),
        };
    }

    try {
        // Check if email already exists
        // TODO (Week 5): Replace table scan with GSI query for production
        // Current: O(n) scan - inefficient but fine for <100 users during development
        // Future: Create GSI on 'email' attribute for O(1) lookup
        const scanCommand = new ScanCommand({
            TableName: TABLE_NAME,
            FilterExpression: 'email = :email',
            ExpressionAttributeValues: {
                ':email': email,
            },
        });

        const existingUsers = await dynamodb.send(scanCommand);

        if (existingUsers.Items && existingUsers.Items.length > 0) {
            return {
                statusCode: 409,
                headers: {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                },
                body: JSON.stringify({ error: 'Email already registered' }),
            };
        }

        const passwordHash = await bcrypt.hash(password, 10);

        const userId = `user-${uuidv4()}`;

        const newUser = {
            userId,
            email,
            passwordHash,
            username: username || email.split('@')[0],
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
        };

        const putCommand = new PutCommand({
            TableName: TABLE_NAME,
            Item: newUser,
            ConditionExpression: 'attribute_not_exists(userId)',
        });

        await dynamodb.send(putCommand);

        const token = jwt.sign(
            {
                userId: userId,
                email: email,
            },
            JWT_SECRET,
            { expiresIn: '7d' }
        );

        return {
            statusCode: 201,
            headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            body: JSON.stringify({
                message: 'User registered successfully',
                token,
                userId,
                email,
                username: newUser.username,
            }),
        };
    } catch (err) {
        console.error('Error:', err);

        return {
            statusCode: 500,
            headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            body: JSON.stringify({
                error: 'Internal server error',
                details: err.message,
            }),
        };
    }
};

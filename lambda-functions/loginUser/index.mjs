import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { DynamoDBDocumentClient, ScanCommand } from '@aws-sdk/lib-dynamodb';
import bcrypt from 'bcryptjs';
import jwt from 'jsonwebtoken';

const client = new DynamoDBClient({});
const dynamodb = DynamoDBDocumentClient.from(client);
const TABLE_NAME = 'Users';
const JWT_SECRET = process.env.JWT_SECRET || 'dev-secret-change-in-production';

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
            body: JSON.stringify({ error: 'Invalid JSON' }),
        };
    }

    const { email, password } = body;

    if (!email || !password) {
        return {
            statusCode: 400,
            headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            body: JSON.stringify({ error: 'Email and password required' }),
        };
    }

    try {
        // Find user by email
        // TODO (Week 5): Replace with GSI query
        const scanCommand = new ScanCommand({
            TableName: TABLE_NAME,
            FilterExpression: 'email = :email',
            ExpressionAttributeValues: {
                ':email': email,
            },
        });

        const result = await dynamodb.send(scanCommand);

        if (!result.Items || result.Items.length === 0) {
            return {
                statusCode: 401,
                headers: {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                },
                body: JSON.stringify({ error: 'Invalid credentials' }),
            };
        }

        const user = result.Items[0];
        const passwordMatch = await bcrypt.compare(password, user.passwordHash);

        if (!passwordMatch) {
            return {
                statusCode: 401,
                headers: {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                },
                body: JSON.stringify({ error: 'Invalid credentials' }),
            };
        }

        const isVerified = user.verified !== false;

        if (!isVerified) {
            return {
                statusCode: 403,
                headers: {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                },
                body: JSON.stringify({
                    error: 'Email not verified. Please check your email for the verification link.',
                    userId: user.userId,
                }),
            };
        }

        const token = jwt.sign(
            {
                userId: user.userId,
                email: user.email,
            },
            JWT_SECRET,
            { expiresIn: '7d' }
        );

        return {
            statusCode: 200,
            headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            body: JSON.stringify({
                message: 'Login successful',
                token,
                userId: user.userId,
                username: user.username,
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
            body: JSON.stringify({ error: 'Internal server error' }),
        };
    }
};

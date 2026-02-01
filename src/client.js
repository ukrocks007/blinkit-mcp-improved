import axios from 'axios';
import fs from 'fs/promises';
import path from 'path';
import os from 'os';
import dotenv from 'dotenv';

dotenv.config();

export class BlinkitAPIClient {
    constructor() {
        this.baseUrl = 'https://blinkit.com';
        this.sessionFile = path.join(os.homedir(), '.blinkit_api_session.json');
        this.browserSessionFile = path.join(os.homedir(), '.blinkit_mcp/cookies/auth.json');
        this.authTokens = {
            'auth_key': null,
            'session_uuid': null,
            'access_token': null
        };
        this.cookies = {};
    }

    async loadAuthTokensFromSession() {
        try {
            // Try specific API session first
            try {
                const apiData = await fs.readFile(this.sessionFile, 'utf8');
                const apiSession = JSON.parse(apiData);
                if (apiSession.auth_tokens) this.authTokens = { ...this.authTokens, ...apiSession.auth_tokens };
                if (apiSession.cookies) this.cookies = { ...this.cookies, ...apiSession.cookies };
                return true;
            } catch (e) {
                // Ignore and try browser session fallback
            }

            const data = await fs.readFile(this.browserSessionFile, 'utf8');
            const session = JSON.parse(data);
            
            // Extract relevant cookies
            const cookieDict = {};
            if (Array.isArray(session)) {
                session.forEach(c => {
                    cookieDict[c.name] = c.value;
                });
            } else if (session.cookies && Array.isArray(session.cookies)) {
                session.cookies.forEach(c => {
                    cookieDict[c.name] = c.value;
                });
            }
            
            this.cookies = { ...this.cookies, ...cookieDict };
            
            // Map common tokens from cookies
            if (cookieDict['auth_key']) this.authTokens.auth_key = cookieDict['auth_key'];
            if (cookieDict['session_uuid']) this.authTokens.session_uuid = cookieDict['session_uuid'];
            
            return true;
        } catch (error) {
            console.warn('Could not load session:', error.message);
            return false;
        }
    }

    async request(method, endpoint, options = {}) {
        const url = endpoint.startsWith('http') ? endpoint : `${this.baseUrl}${endpoint}`;
        
        const headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (X11; Linux aarch64; rv:109.0) Gecko/20100101 Firefox/115.0',
            'Origin': 'https://blinkit.com',
            'Referer': 'https://blinkit.com/',
            ...options.headers
        };

        // Add discovered authentication tokens
        Object.entries(this.authTokens).forEach(([k, v]) => {
            if (v) headers[k] = v;
        });

        // Add session cookies
        const cookieString = Object.entries(this.cookies)
            .map(([name, value]) => `${name}=${value}`)
            .join('; ');
        
        if (cookieString) {
            headers['Cookie'] = cookieString;
        }

        try {
            const response = await axios({
                method,
                url,
                data: options.data,
                params: options.params,
                headers,
                timeout: 30000
            });
            return response.data;
        } catch (error) {
            if (error.response) {
                return { 
                    error: true, 
                    status: error.response.status, 
                    message: typeof error.response.data === 'string' ? error.response.data.substring(0, 200) : JSON.stringify(error.response.data)
                };
            }
            throw error;
        }
    }

    async get(endpoint, options = {}) {
        return this.request('GET', endpoint, options);
    }

    async post(endpoint, data, options = {}) {
        return this.request('POST', endpoint, { ...options, data });
    }
}
import axios from 'axios';
import MockAdapter from 'axios-mock-adapter';
import { apiClient } from './lib/api-client';

// Create a mock adapter on the custom axios instance
const mock = new MockAdapter(apiClient, { delayResponse: 500 });

// Mock /auth/login
mock.onPost('/auth/login').reply(200, { access_token: 'fake_mock_token_123' });

// Mock /auth/register
mock.onPost('/auth/register').reply(200, {
  id: 1, email: 'demo@eva.com', display_name: 'Demo User', role: 'student', timezone: 'UTC'
});

// Mock /auth/me
mock.onGet('/auth/me').reply(200, {
  id: 1,
  email: 'alex@example.com',
  display_name: 'Alex Thompson',
  role: 'student',
  timezone: 'UTC'
});

// Mock /courses
mock.onGet('/courses').reply(200, [
  { id: 1, title: 'Introduction to Python', description: 'Learn python', thumbnail_url: null, created_at: '2023-01-01', updated_at: '2023-01-01' },
  { id: 2, title: 'Advanced UI/UX Design', description: 'Design better interfaces', thumbnail_url: null, created_at: '2023-01-01', updated_at: '2023-01-01' }
]);

// Mock /dashboard
mock.onGet(/\/dashboard.*/).reply(200, {});

// Mock generic array responses for any other route
mock.onAny().reply((config) => {
  console.log('Mocked API Call:', config.method?.toUpperCase(), config.url);
  // Just return empty array by default to prevent .map crashes
  return [200, []];
});

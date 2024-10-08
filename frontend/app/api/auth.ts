// app/api/auth.ts
import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://freelpay-nextjs-pm2fo.ondigitalocean.app/api';

export const login = async (username: string, password: string) => {
  const formData = new URLSearchParams();
  formData.append('username', username);
  formData.append('password', password);
  const response = await axios.post(`${API_URL}/auth/login`, formData, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  });
  return response.data;
};

export const signup = async (username: string, email: string, password: string, siretNumber: string, phone: string, address: string) => {
  const response = await axios.post(`${API_URL}/auth/signup`, {
    username,
    email,
    password,
    siret_number: siretNumber,
    phone,
    address,
  });
  return response.data;
};
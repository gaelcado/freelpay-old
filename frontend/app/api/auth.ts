// app/api/auth.ts
import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://freelpay.com/api";

// Créez une instance axios avec une configuration par défaut
const axiosInstance = axios.create({
  baseURL: API_URL,
});

// Ajoutez un intercepteur pour ajouter le token aux requêtes
axiosInstance.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Ajouter un intercepteur pour gérer les erreurs
axiosInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const login = async (username: string, password: string) => {
  try {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    const response = await axiosInstance.post('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    return response.data;
  } catch (error) {
    console.error('Login error:', error);
    throw error;
  }
};

export const signup = async (username: string, email: string, password: string, siretNumber: string, phone: string, address: string) => {
  const response = await axiosInstance.post('/auth/signup', {
    username,
    email,
    password,
    siret_number: siretNumber,
    phone,
    address,
  });
  return response.data;
};

// Ajoutez cette fonction pour récupérer le profil
export const getProfile = async () => {
  const response = await axiosInstance.get('/users/me');
  return response.data;
};
import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'react-hot-toast';

const Login: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await axios.post(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/auth/login`, {
        email,
        password,
      });
      localStorage.setItem('volunite_token', response.data.token);
      localStorage.setItem('volunite_user', JSON.stringify(response.data.user));
      toast.success('Welcome back to Volunite!');
      navigate('/dashboard');
    } catch (error: any) {
      toast.error(error.response?.data?.message || 'Login failed');
    }
  };

  return (
    <div className="min-h-screen bg-[#0f172a] text-white flex flex-col items-center justify-center p-6">
      <motion.div 
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-md bg-white/5 backdrop-blur-xl p-8 rounded-3xl border border-white/10 shadow-2xl"
      >
        <h2 className="text-3xl font-bold mb-6 text-center">Login to <span className="text-[#00bfa5]">Volunite</span></h2>
        
        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Email</label>
            <input 
              type="email" 
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-3 rounded-xl bg-black/20 border border-white/10 focus:border-[#00bfa5] focus:outline-none focus:ring-1 focus:ring-[#00bfa5] transition-colors"
              placeholder="you@example.com"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Password</label>
            <input 
              type="password" 
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-3 rounded-xl bg-black/20 border border-white/10 focus:border-[#00bfa5] focus:outline-none focus:ring-1 focus:ring-[#00bfa5] transition-colors"
              placeholder="••••••••"
            />
          </div>

          <button 
            type="submit"
            className="w-full py-3 mt-6 bg-[#00bfa5] text-white font-bold rounded-xl hover:bg-teal-500 transition-colors shadow-lg shadow-teal-500/30"
          >
            Sign In
          </button>
        </form>

        <p className="mt-6 text-center text-gray-400 text-sm">
          Don't have an account? <span onClick={() => navigate('/register')} className="text-[#00bfa5] cursor-pointer hover:underline">Register here</span>
        </p>
      </motion.div>
    </div>
  );
};

export default Login;

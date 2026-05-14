import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { MapComponent } from '../components/MapComponent';

const Dashboard: React.FC = () => {
  const [user, setUser] = useState<any>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const storedUser = localStorage.getItem('volunite_user');
    const token = localStorage.getItem('volunite_token');
    
    if (!storedUser || !token) {
      navigate('/login');
      return;
    }
    
    setUser(JSON.parse(storedUser));
  }, [navigate]);

  const handleLogout = () => {
    localStorage.removeItem('volunite_token');
    localStorage.removeItem('volunite_user');
    navigate('/login');
  };

  if (!user) return <div className="min-h-screen bg-[#0f172a] text-white flex items-center justify-center">Loading...</div>;

  return (
    <div className="min-h-screen bg-[#0f172a] text-white p-6">
      <nav className="flex justify-between items-center bg-white/5 backdrop-blur-md p-4 rounded-2xl border border-white/10 mb-8">
        <h1 className="text-2xl font-bold text-[#00bfa5]">Volunite Dashboard</h1>
        <div className="flex items-center gap-4">
          <span className="text-gray-300">Hello, {user.name} ({user.role})</span>
          <button onClick={handleLogout} className="px-4 py-2 bg-red-500/20 text-red-400 rounded-lg hover:bg-red-500/30 transition-colors">
            Logout
          </button>
        </div>
      </nav>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <motion.div whileHover={{ y: -5 }} className="bg-white/5 p-6 rounded-2xl border border-white/10">
          <h3 className="text-xl font-bold mb-2">My Requests</h3>
          <p className="text-gray-400 text-3xl font-light">0 Active</p>
        </motion.div>
        
        {user.role === 'VOLUNTEER' && (
          <motion.div whileHover={{ y: -5 }} className="bg-[#00bfa5]/10 p-6 rounded-2xl border border-[#00bfa5]/30">
            <h3 className="text-xl font-bold mb-2 text-[#00bfa5]">Tasks Available</h3>
            <p className="text-gray-400 text-3xl font-light">12 Nearby</p>
          </motion.div>
        )}

        <motion.div whileHover={{ y: -5 }} className="bg-white/5 p-6 rounded-2xl border border-white/10">
          <h3 className="text-xl font-bold mb-2">Impact Score</h3>
          <p className="text-gray-400 text-3xl font-light">Level 1</p>
        </motion.div>
      </div>
      
      <div className="mt-8 bg-white/5 p-2 rounded-2xl border border-white/10 h-[500px] flex items-center justify-center shadow-2xl overflow-hidden">
        <MapComponent />
      </div>
    </div>
  );
};

export default Dashboard;

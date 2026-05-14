import React from 'react';
import { motion } from 'framer-motion';

function App() {
  return (
    <div className="min-h-screen bg-[#0f172a] text-white flex flex-col items-center justify-center p-6">
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
        className="max-w-3xl text-center space-y-8"
      >
        <h1 className="text-6xl font-extrabold tracking-tight">
          Welcome to <span className="text-[#00bfa5]">Volunite</span>
        </h1>
        <p className="text-xl text-gray-300">
          The ultimate AI-powered community help and volunteer coordination platform.
          Currently deploying the next-generation architecture.
        </p>
        
        <div className="flex gap-4 justify-center pt-8">
          <motion.button 
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="px-8 py-3 bg-[#00bfa5] text-white font-bold rounded-full shadow-lg shadow-teal-500/30"
          >
            I Need Help
          </motion.button>
          <motion.button 
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="px-8 py-3 bg-white/10 text-white font-bold rounded-full backdrop-blur-md border border-white/20 hover:bg-white/20"
          >
            Volunteer Now
          </motion.button>
        </div>
      </motion.div>
    </div>
  );
}

export default App;

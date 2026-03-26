import { useState, useEffect } from 'react';
import { Info, Database, PlayCircle, User, X, MessageSquare, ExternalLink } from 'lucide-react';

export default function WelcomeModal() {
  const [isOpen, setIsOpen] = useState(true);

  const handleClose = () => {
    setIsOpen(false);
  };

  if (!isOpen) return null;

  const sessionId = import.meta.env.VITE_CODEBASE_SESSION_ID || "30e82929-e82f-4ed0-9463-2da67d8a5ea8";

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-gray-900/60 backdrop-blur-md animate-fade-in">
      <div className="relative w-full max-w-md bg-gray-800/90 border border-gray-700 rounded-2xl shadow-2xl overflow-hidden animate-slide-in-up">
        {/* Top Gradient Bar */}
        <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-500 to-purple-600"></div>

        <div className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <Info className="h-5 w-5 text-blue-400" />
              Quick Guide
            </h2>
            <button onClick={handleClose} className="text-gray-500 hover:text-white transition-colors">
              <X className="h-5 w-5" />
            </button>
          </div>

          <div className="space-y-4 pt-2">
            <div className="space-y-4 text-sm text-gray-300">
              <div className="flex gap-3">
                <span className="text-blue-400 font-bold">1.</span>
                <p><span className="text-white font-semibold">Note:</span> This project doesn't require auth. Please <span className="text-blue-300">avoid ingesting very large repositories, because we are working on free tier.</span>.</p>
              </div>

              <div className="flex gap-3">
                <span className="text-blue-400 font-bold">2.</span>
                <p><span className="text-white font-semibold">Neo4j:</span> Aura instance pauses after 3 days. If you get an error, try again later; I'll be notified via email.</p>
              </div>

              <div className="flex gap-3">
                <span className="text-blue-400 font-bold">3.</span>
                <div className="flex-1">
                  <p className="mb-2"><span className="text-white font-semibold">Demo Chat:</span> Try chatting with this coderag repository using this session ID or click START:</p>
                  <div className="bg-gray-900 border border-gray-700 p-2 rounded flex justify-between items-center group">
                    <code className="text-purple-400 font-mono text-xsSelection">{sessionId}</code>
                    <MessageSquare className="h-4 w-4 text-gray-600 group-hover:text-purple-500 transition-colors" />
                  </div>
                </div>
              </div>

              <div className="flex gap-3">
                <span className="text-blue-400 font-bold">4.</span>
                <a
                  href="https://drive.google.com/file/d/1Im3uKlEFYP6dIadV66dBiUt3xHshyjEH/view?usp=drive_link"
                  target="_blank" rel="noreferrer"
                  className="text-blue-400 hover:text-blue-300 hover:underline flex items-center gap-1 font-semibold"
                >
                  Watch Demo Video <ExternalLink className="h-3 w-3" />
                </a>
              </div>

              <div className="flex gap-3">
                <span className="text-blue-400 font-bold">5.</span>
                <a
                  href="https://shsax.vercel.app"
                  target="_blank" rel="noreferrer"
                  className="text-blue-400 hover:text-blue-300 hover:underline flex items-center gap-1 font-semibold"
                >
                  My Portfolio <ExternalLink className="h-3 w-3" />
                </a>
              </div>
            </div>
          </div>

          <button
            onClick={handleClose}
            className="mt-8 w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white font-bold py-3 px-6 rounded-xl transition-all shadow-lg shadow-blue-500/20 active:scale-95"
          >
            Okay
          </button>
        </div>
      </div>
    </div>
  );
} 

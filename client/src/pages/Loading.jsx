import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Copy } from "lucide-react";

export default function LoadingPage({sessionId, reqId}) {
  const [currentGif, setCurrentGif] = useState(0);
  const [isVisible, setIsVisible] = useState(false);
  const [processLine, setProcessLine] = useState(".....");
  const [copied, setCopied] = useState(false);
  const navigator = useNavigate()
  const receivedWsLabelRef = useRef(false);

  const gifUrls = [
    "https://media3.giphy.com/media/v1.Y2lkPTc5MGI3NjExZGc4cThtOGZ4eTI1Ymd5aDF1MmZzejN4MXEyMzNvYmE4amQ1enB1eCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/EMi5WGu5ld8HTRJ0iK/giphy.gif",
    "https://media3.giphy.com/media/v1.Y2lkPTc5MGI3NjExNXM4ZmdjdWl4NmVteHd1YTExbTQ1d2hoZTJyajhuMG1qZ3ppMTc4aiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/5d0YGiH8L3mc2gBmAS/giphy.gif",
    "https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExbDJrOXA5bWNxcndzNHBjb3RlYTFvdDg3Nzh2cnByMXoxdmcwaTR3MSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/OvRI36nbtGEkXvGeKw/giphy.gif",
    "https://media3.giphy.com/media/v1.Y2lkPTc5MGI3NjExNXM4ZmdjdWl4NmVteHd1YTExbTQ1d2hoZTJyajhuMG1qZ3ppMTc4aiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/5d0YGiH8L3mc2gBmAS/giphy.gif", // Replace with your second GIF URL
    "https://media3.giphy.com/media/v1.Y2lkPTc5MGI3NjExaTh5Nm1sbXQ0Zmh4ZWg4OHZ4aGdmYm44dmVrMzRlOHdic3J4NWxqayZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/Cq7bLcxDvko3TytAvS/giphy.gif",  // Replace with your third GIF URL
    "https://media3.giphy.com/media/v1.Y2lkPTc5MGI3NjExbjlnMm54ZmJlZW9qcWc1Y2V5OGluZm1ieDJ2NnphN2ZsazJ6dmlxcSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/J8hpHYrzNPs1b3crQG/giphy.gif"
    ];

const progressSteps = [
  "Validating repository URL...",
  "Cloning repository...",
  "Walking through the file system...",
  "Reading source files...",
  "Parsing files into ASTs...",
  "Extracting functions, classes, and modules...",
  "Generating embeddings for code chunks...",
  "Storing embeddings in Vector Database...",
  "Updating Graph Database with AST relationships...",
  "Linking code elements for semantic search...",
  "Indexing code for quick context retrieval...",
  "Optimizing storage and retrieval structures...",
  "Finalizing RAG setup...",
  "Ready to chat with the codebase!",
  "chatting about to start....",
  "Wait",
  "wait",
  "if it takes too long, contact for support",
];

  const [logs, setLogs] = useState([]);
  const logsEndRef = useRef(null);
  
  // Auto-scroll to bottom of terminal when new logs arrive
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  useEffect(() => {
    if (!reqId) {
      console.log("[Loading] No reqId provided, skipping WebSocket connection.");
      return;
    }
    const serverUrl = import.meta.env.VITE_SERVER_URL || `http://${window.location.host}`;
    const cleanServerUrl = serverUrl.replace(/\/$/, '');
    const wsUrl = `${cleanServerUrl.replace(/^http/, 'ws')}/api/ws/logs/${reqId}`;
    
    console.log("[Loading] Attempting WebSocket connection to:", wsUrl);
    const ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
      console.log("[Loading] WebSocket connection established successfully.");
    };

    ws.onmessage = (event) => {
      console.log("[Loading] WebSocket message received:", event.data);
      receivedWsLabelRef.current = true;
      setLogs((prev) => [...prev, event.data]);
      setProcessLine(event.data);
    };

    ws.onerror = (error) => {
      console.error("[Loading] WebSocket error encountered:", error);
    };

    ws.onclose = (event) => {
      console.log(`[Loading] WebSocket connection closed. Code: ${event.code}, Reason: ${event.reason}`);
    };

    return () => {
      console.log("[Loading] Cleaning up WebSocket connection.");
      ws.close();
    };
  }, [reqId]);

  useEffect(() => { 
    let step = 0;
    const interval = setInterval(() => {
      if (!receivedWsLabelRef.current) {
        setProcessLine(progressSteps[step%progressSteps.length]);
        step++;
        if(step >= progressSteps.length) clearInterval(interval);
      } else {
        clearInterval(interval);
      }
    }, 3000)
    return () => clearInterval(interval);
  }, []);

  const handleCopy = () => {
    navigator.clipboard.writeText(sessionId);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const onStartChat = () => {
    navigator(`/chat/${sessionId}`)
  }




  useEffect(() => {
    setIsVisible(true);
      const gifInterval = setInterval(() => {
      setCurrentGif(prev => (prev + 1) % gifUrls.length);
    }, 2500);

    return () => {
      clearInterval(gifInterval);
    };
  }, []);

  return (
    <div className="min-h-screen bg-slate-900 relative overflow-hidden">
      {/* Grid background matching your website */}
      <div className="absolute inset-0 opacity-40">
        <div className="absolute inset-0"
             style={{
               backgroundImage: 'linear-gradient(to right, #3b82f6 1px, transparent 1px), linear-gradient(to bottom, #3b82f6 1px, transparent 1px)',
               backgroundSize: '40px 40px'
             }}>
        </div>
      </div>

      {/* Subtle gradient overlay */}
      <div className="absolute inset-0 bg-gradient-to-br from-blue-900/10 via-transparent to-purple-900/10"></div>

      {
        sessionId != "" ? (
          <div className="min-h-screen flex items-center justify-center bg-slate-900 px-4">
            <div className="bg-slate-800/80 backdrop-blur-sm border border-blue-500/30 rounded-2xl p-8 w-full max-w-md shadow-xl">
              
              {/* Description */}
              <p className="text-slate-200 text-center text-lg mb-6">
                You can copy this Session ID and continue chatting later on this repository 
                before Neo4j is reset.
              </p>

              {/* Input box with copy */}
              <div className="flex items-center bg-slate-700 border border-blue-500/50 rounded-xl overflow-hidden mb-6">
                <input
                  type="text"
                  readOnly
                  value={sessionId}
                  className="flex-1 px-4 py-2 bg-transparent text-slate-200 focus:outline-none"
                />
                <button
                  onClick={handleCopy}
                  className="px-3 py-2 bg-blue-500/30 hover:bg-blue-500/50 transition-colors flex items-center"
                >
                  <Copy className="w-5 h-5 text-white" />
                </button>
              </div>

              {/* Copy feedback */}
              {copied && (
                <p className="text-green-400 text-sm text-center mb-4">
                  Session ID copied to clipboard!
                </p>
              )}

              {/* Start Chatting button */}
              <button
                onClick={onStartChat}
                className="w-full py-3 bg-blue-500 hover:bg-blue-600 hover:cursor-pointer transition-colors text-white font-semibold rounded-xl shadow-md"
              >
                Start Chatting
              </button>
            </div>
          </div>
        ) : (
          <div className="relative z-10 min-h-screen flex items-center justify-center px-4">
           <div className={`text-center transform transition-all duration-1000 ${
              isVisible ? 'scale-100 opacity-100' : 'scale-95 opacity-0'
            }`}>
              
              {/* GIF Container with dark theme */}
              <div className="relative">
                <div className="relative w-80 h-80 mx-auto">
                  {/* Dark container with blue border */}
                  <div className="absolute inset-0 bg-gradient-to-br from-slate-800 via-slate-700 to-slate-800 rounded-2xl shadow-2xl border border-blue-500/30"></div>
                  
                  {/* GIF Container with blend mode to remove white backgrounds */}
                  <div className="relative w-full h-full rounded-2xl overflow-hidden p-4">
                    {gifUrls.map((gifUrl, index) => (
                      <div
                        key={index}
                        className={`absolute inset-4 transition-all duration-700 ease-in-out ${
                          currentGif === index 
                            ? 'opacity-100 scale-100' 
                            : 'opacity-0 scale-110'
                        }`}
                      >
                        <div className="relative w-full h-full rounded-xl overflow-hidden bg-slate-700">
                          <img
                            src={gifUrl}
                            alt={`Loading ${index + 1}`}
                            className="w-full h-full object-contain"
                            style={{
                              mixBlendMode: 'screen',
                              filter: 'brightness(1.2) contrast(1.1) hue-rotate(200deg)'
                            }}
                          />
                          {/* Overlay to blend with dark theme */}
                          <div className="absolute inset-0 bg-gradient-to-br from-blue-900/20 via-transparent to-purple-900/20 pointer-events-none"></div>
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Simple glowing border */}
                  <div className="absolute inset-0 rounded-2xl ring-1 ring-blue-500/50"></div>
                </div>

                {/* Message matching your website's style */}
                <div className={`mt-8 transform transition-all duration-1000 delay-500 ${
                  isVisible ? 'translate-y-0 opacity-100' : 'translate-y-4 opacity-0'
                }`}>
                  <div className="bg-slate-800/80 backdrop-blur-sm border border-blue-500/30 rounded-2xl p-6 shadow-xl relative overflow-hidden">
                    {/* Subtle gradient background */}
                    <div className="absolute inset-0 bg-gradient-to-r from-blue-600/5 via-purple-600/5 to-blue-600/5 rounded-2xl"></div>
                    <div className="relative z-10">
                      <p className="text-slate-200 text-lg font-medium leading-relaxed">
                        Analyzing and processing your repository with advanced RAG technology. <br />
                        <span className="text-blue-400 font-normal">This may take a moment depending on the codebase complexity.</span>
                      </p>
                    </div>
                  </div>
                </div>
              </div>

            {/* Terminal Window */}
            {receivedWsLabelRef.current && (
              <div className="mt-8 w-full max-w-2xl mx-auto bg-[#0d1117]/90 backdrop-blur-md rounded-xl border border-blue-500/30 shadow-2xl overflow-hidden font-mono text-xs relative">
                {/* Terminal Header */}
                <div className="bg-[#161b22] px-4 py-2 flex items-center justify-between border-b border-blue-500/30">
                  <div className="flex space-x-2">
                    <div className="w-3 h-3 rounded-full bg-red-500 shadow-sm shadow-red-500/50"></div>
                    <div className="w-3 h-3 rounded-full bg-yellow-500 shadow-sm shadow-yellow-500/50"></div>
                    <div className="w-3 h-3 rounded-full bg-green-500 shadow-sm shadow-green-500/50"></div>
                  </div>
                  <div className="text-gray-400 font-semibold tracking-wider">server-logs ~ bash</div>
                  <div className="w-12"></div>
                </div>
                
                {/* Terminal Body */}
                <div className="p-4 h-64 overflow-y-auto w-full flex flex-col items-start text-left space-y-1 scrollbar-thin scrollbar-thumb-gray-700">
                  {logs.map((log, i) => {
                     const match = log.match(/^([A-Z]+):\s+\[(.*?)\]\s+(.*)$/);
                     if (match) {
                       return (
                         <div key={i} className="text-gray-300 w-full break-all whitespace-pre-wrap">
                           <span className={match[1] === 'ERROR' ? 'text-red-400' : match[1] === 'WARNING' ? 'text-yellow-400' : 'text-blue-400 font-bold'}>{match[1]}</span>
                           <span className="text-gray-500 ml-2">[{match[2]}]</span>
                           <span className="text-green-400 ml-2">{match[3]}</span>
                         </div>
                       )
                     }
                     return <div key={i} className="text-gray-300 w-full break-all whitespace-pre-wrap">{log}</div>;
                  })}
                  <div ref={logsEndRef} />
                </div>
              </div>
            )}
            
            {!receivedWsLabelRef.current && (
              <p className="text-blue-400 font-semibold mt-5 animate-pulse">
                {processLine}
              </p>
            )}


              {/* Loading dots with purple-blue gradient */}
              <div className="flex justify-center space-x-3 mt-12">
                {[0, 1, 2, 3, 4].map((dot) => (
                  <div
                    key={dot}
                    className="w-2 h-2 bg-gradient-to-r from-blue-500 via-purple-500 to-blue-600 rounded-full animate-bounce shadow-md shadow-blue-500/40"
                    style={{ 
                      animationDelay: `${dot * 0.15}s`,
                      animationDuration: '1.5s'
                    }}
                  ></div>
                ))}
              </div>
            </div>
      </div>
        )
      }
      
      

      <style jsx='true'>{`
        @keyframes float {
          0%, 100% { 
            transform: translateY(0px) rotate(0deg); 
            opacity: 0.2;
          }
          50% { 
            transform: translateY(-10px) rotate(180deg); 
            opacity: 0.4;
          }
        }
      `}</style>
    </div>
  );
}
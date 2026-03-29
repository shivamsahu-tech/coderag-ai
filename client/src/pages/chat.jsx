import { Send, Bot, User, Code, MessageSquare, RotateCcw, Github, ChevronDown } from 'lucide-react';
import { useState, useRef, useEffect } from 'react';
import MarkdownLoader from '../components/markdownLoader';
import { useNavigate, useParams } from 'react-router-dom';

export default function ChatPage() {
  const [inputMessage, setInputMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isVisible, setIsVisible] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const scrollContainerRef = useRef(null);
  const navigator = useNavigate();
  const { sessionId } = useParams();

  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'bot',
      content: "Hi! I'm your CodeRAG Agent assistant. I've analyzed your repository and I'm ready to help you understand your codebase. What would you like to know?",
      timestamp: new Date()
    }
  ]);
  const [showScrollButton, setShowScrollButton] = useState(false);

  useEffect(() => {
    const uuidRegex = /^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/;
    if (!uuidRegex.test(sessionId)) {
      alert("Please enter a valid session id");
      navigator("/");
    }
    setIsVisible(true);
    inputRef.current?.focus();
  }, [sessionId, navigator]);

  const handleScroll = () => {
    if (!scrollContainerRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = scrollContainerRef.current;
    const isAtBottom = scrollHeight - scrollTop - clientHeight < 150;
    setShowScrollButton(!isAtBottom);
  };

  useEffect(() => {
    if (!showScrollButton) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, showScrollButton]);

  const chat = async (query) => {
    const url = `${import.meta.env.VITE_SERVER_URL}/api/retreive`;
    try {
      const result = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ session_id: sessionId, query: query })
      });
      const res = await result.json();
      if (result.ok && res.status === "success") {
        return res.llm_response;
      }
      return "I encountered an error. Please check if the server is running.";
    } catch (error) {
      console.error("Network error:", error);
      return "Network error. Please try again.";
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim() || isTyping) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputMessage,
      timestamp: new Date()
    };
    const userQuery = inputMessage;
    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsTyping(true);

    const llmResponse = await chat(userQuery);

    const botMessage = {
      id: Date.now() + 1,
      type: 'bot',
      content: llmResponse,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, botMessage]);
    setIsTyping(false);
  };

  const clearChat = () => {
    if (confirm("Clear chat?")) {
      setMessages([{
        id: 1,
        type: 'bot',
        content: "Chat cleared! How can I help you now?",
        timestamp: new Date()
      }]);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 relative overflow-hidden flex flex-col font-sans">
      {/* Background Layer */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#374151_1px,transparent_1px),linear-gradient(to_bottom,#374151_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_80%_50%_at_50%_0%,#000_70%,transparent_110%)] animate-pulse pointer-events-none"></div>
      <div className="absolute inset-0 bg-gradient-to-br from-blue-900/10 via-purple-900/10 to-gray-900/20 animate-gradient-x pointer-events-none"></div>

      {/* Floating Particles */}
      <div className="absolute inset-0 pointer-events-none z-0">
        {[...Array(15)].map((_, i) => (
          <div
            key={i}
            className="absolute w-1 h-1 bg-blue-400/20 rounded-full animate-float"
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              animationDelay: `${Math.random() * 5}s`,
              animationDuration: `${3 + Math.random() * 4}s`
            }}
          />
        ))}
      </div>

      {/* Header */}
      <header className="bg-gray-900/95 backdrop-blur-xl border-b border-gray-800 fixed top-0 left-0 right-0 z-[100] shadow-2xl">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className={`flex items-center space-x-3 transform transition-all duration-1000 ${isVisible ? 'translate-x-0 opacity-100' : '-translate-x-10 opacity-0'}`}>
              <div className="bg-gradient-to-r from-blue-500 to-purple-600 p-2 rounded-lg animate-glow">
                <MessageSquare className="h-6 w-6 text-white" />
              </div>
              <div onClick={() => navigator("/")} className="cursor-pointer">
                <h1 className="text-xl font-bold text-white tracking-tight">CodeRAG Agent</h1>
              </div>
            </div>

            <div className={`flex items-center space-x-4 transform transition-all duration-1000 delay-200 ${isVisible ? 'translate-x-0 opacity-100' : 'translate-x-10 opacity-0'}`}>
              <button
                onClick={clearChat}
                className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-all duration-300"
                title="Clear Chat"
              >
                <RotateCcw className="h-5 w-5" />
              </button>
              <a href='https://github.com/shivamsahu-tech/coderag-ai' target='_blank' rel="noreferrer" className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-all duration-300">
                <Github className="h-5 w-5" />
              </a>
            </div>
          </div>
        </div>
      </header>

      {/* Main Chat Area */}
      <main className="flex-grow flex flex-col relative z-20 overflow-hidden pt-[73px] h-screen">
        <div 
          ref={scrollContainerRef}
          onScroll={handleScroll}
          className="flex-grow overflow-y-auto px-4 pt-10 pb-40 scroll-smooth scrollbar-hide"
        >
          <div className="max-w-5xl mx-auto space-y-12">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex items-start space-x-4 animate-slide-in-up ${message.type === 'user' ? 'flex-row-reverse space-x-reverse' : ''}`}
              >
                {/* Avatar */}
                <div className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center shadow-lg ${
                  message.type === 'bot'
                    ? 'bg-gradient-to-r from-blue-500 to-purple-600 animate-glow'
                    : 'bg-gradient-to-r from-green-500 to-teal-600'
                }`}>
                  {message.type === 'bot' ? <Bot className="h-5 w-5 text-white" /> : <User className="h-5 w-5 text-white" />}
                </div>

                {/* Message Content */}
                <div className={`flex flex-col ${message.type === 'user' ? 'items-end' : 'items-start'} max-w-[80%]`}>
                  <div className={`inline-block p-4 rounded-2xl shadow-xl border transform transition-all duration-300 hover:scale-[1.01] max-w-3xl ${
                    message.type === 'user'
                      ? 'bg-gray-700/50 border-gray-600 text-gray-100 rounded-tr-sm'
                      : 'bg-gray-700/50 border-gray-600 text-gray-100 rounded-tl-sm'
                  }`}>
                    <MarkdownLoader content={message.content} />
                  </div>
                  <p className="text-[10px] text-gray-500 mt-2 font-mono uppercase tracking-widest">
                    {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </p>
                </div>
              </div>
            ))}

            {/* Typing Indicator */}
            {isTyping && (
              <div className="flex items-start space-x-4 animate-pulse">
                <div className="flex-shrink-0 w-10 h-10 rounded-full bg-gradient-to-r from-blue-500 to-purple-600 flex items-center justify-center">
                  <Bot className="h-5 w-5 text-white" />
                </div>
                <div className="inline-block p-4 bg-gray-700/50 border border-gray-600 rounded-2xl rounded-tl-sm shadow-xl">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} className="h-4" />
          </div>
        </div>

        {/* Floating Input Area */}
        <div className="fixed bottom-0 left-0 right-0 z-50 p-6 bg-gradient-to-t from-gray-900 via-gray-900/90 to-transparent">
          <div className="max-w-3xl mx-auto flex items-end space-x-4">
            <form onSubmit={handleSendMessage} className="flex-1 flex space-x-4 bg-gray-800/80 backdrop-blur-xl p-2 rounded-3xl border border-gray-700 shadow-2xl transition-all">
              <div className="flex-1 relative group flex items-center pl-4">
                <Code className="text-gray-400 h-5 w-5 group-hover:text-blue-400 transition-colors" />
                <input
                  ref={inputRef}
                  type="text"
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  placeholder="Ask anything about your codebase..."
                  className="w-full pl-3 pr-4 py-3 bg-transparent border-none text-white focus:ring-0 focus:outline-none placeholder-gray-500"
                  disabled={isTyping}
                />
              </div>
              <button
                type="submit"
                disabled={!inputMessage.trim() || isTyping}
                className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white p-3 rounded-2xl transition-all disabled:opacity-30 flex items-center justify-center shadow-lg"
              >
                <Send className="h-5 w-5" />
              </button>
            </form>
            
            {showScrollButton && (
              <button
                onClick={() => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })}
                className="mb-1 bg-gray-800/80 backdrop-blur-xl p-4 rounded-full border border-gray-700 text-gray-400 hover:text-white hover:border-gray-500 transition-all shadow-2xl animate-in zoom-in fade-in duration-300"
                title="Scroll to Bottom"
              >
                <ChevronDown className="h-5 w-5" />
              </button>
            )}
          </div>
          <p className="text-center text-[10px] text-gray-600 mt-4 font-medium uppercase tracking-[0.3em]">
            Powered by Groq • CodeRAG AI
          </p>
        </div>
      </main>

      <style jsx='true'>{`
        @keyframes gradient-x { 0%, 100% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } }
        @keyframes float { 0%, 100% { transform: translateY(0px); } 50% { transform: translateY(-20px); } }
        @keyframes glow { 0%, 100% { box-shadow: 0 0 5px rgba(59, 130, 246, 0.3); } 50% { box-shadow: 0 0 20px rgba(59, 130, 246, 0.6), 0 0 30px rgba(59, 130, 246, 0.4); } }
        @keyframes slide-in-up { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
        .animate-gradient-x { animation: gradient-x 15s ease infinite; }
        .animate-float { animation: float 6s ease-in-out infinite; }
        .animate-glow { animation: glow 3s ease-in-out infinite; }
        .animate-slide-in-up { animation: slide-in-up 0.5s ease-out forwards; }
        .scrollbar-hide::-webkit-scrollbar { display: none; }
        .scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
      `}</style>
    </div>
  );
}
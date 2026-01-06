import { Send, Bot, User, Code, MessageSquare, RotateCcw, Settings, Github } from 'lucide-react';
import { useState, useRef, useEffect } from 'react';
import MarkdownLoader from '../components/markdownLoader';
import { useNavigate, useParams } from 'react-router-dom';

export default function ChatPage() {
  const [inputMessage, setInputMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isVisible, setIsVisible] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const navigator = useNavigate()
  const { sessionId } = useParams()

  const [messages, setMessages] = useState([
      {
        id: 1,
        type: 'bot',
        content: "Hi! I'm your CodeRAG Agent assistant. I've analyzed your repository and I'm ready to help you understand your codebase. What would you like to know?",
        timestamp: new Date()
      }
    ]);


  useEffect(() => {
    const uuidRegex = /^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/;
    if(!uuidRegex.test(sessionId)){
       alert("Please enter a valid session id")
       navigator("/")
    }
    setIsVisible(true);
    inputRef.current?.focus();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);


  const chat = async (query) => {
    const url = `${import.meta.env.VITE_SERVER_URL}/api/retreive`

    try {
        const result = await fetch(url, {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          credentials: "include",
          body: JSON.stringify({ session_id: sessionId, query: query })
        })
        const res = await result.json();
        console.log("retreive api response", res);
        if (result.ok && res.status === "success") {
            console.log("chat responded", res.llm_response);
            return res.llm_response;
          } else {
            console.error("Error processing repo:", res);
            alert("Please try again or contact with the maintainer!!!");
          }
      } catch (error) {
        console.error("Network error:", error);
        alert("Server not reachable!");
      }
  }

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim() || isTyping) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputMessage,
      timestamp: new Date()
    };
    const userQuery = inputMessage
    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsTyping(true);

    const llmResponse = await chat(userQuery)

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
    setMessages([
      {
        id: 1,
        type: 'bot',
        content: "Chat cleared! I'm still here to help you understand your codebase. What would you like to explore?",
        timestamp: new Date()
      }
    ]);
  };

  return (
    <div className="min-h-screen bg-gray-900 relative overflow-hidden">
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#374151_1px,transparent_1px),linear-gradient(to_bottom,#374151_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_80%_50%_at_50%_0%,#000_70%,transparent_110%)] animate-pulse"></div>
            <div className="absolute inset-0 bg-gradient-to-br from-blue-900/10 via-purple-900/10 to-gray-900/20 animate-gradient-x"></div>

      <div className="absolute inset-0 pointer-events-none">
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
      <header className="bg-gray-800/90 backdrop-blur-md border-b border-gray-700 sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className={`flex items-center space-x-3 transform transition-all duration-1000 ${
              isVisible ? 'translate-x-0 opacity-100' : '-translate-x-10 opacity-0'
            }`}>
              <div className="bg-gradient-to-r from-blue-500 to-purple-600 p-2 rounded-lg animate-glow">
                <MessageSquare className="h-6 w-6 text-white" />
              </div>
              <div onClick={() => goingOut()} >
                <h1 className="text-xl font-bold text-white">CodeRAG Agent Chat</h1>
              </div>
            </div>
            
            <div className={`flex items-center space-x-4 transform transition-all duration-1000 delay-200 ${
              isVisible ? 'translate-x-0 opacity-100' : 'translate-x-10 opacity-0'
            }`}>
              <button 
                onClick={clearChat}
                className="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded-lg transition-all duration-300 hover:scale-110"
                title="Clear Chat"
              >
                <RotateCcw className="h-5 w-5" />
              </button>
              {/* <button className="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded-lg transition-all duration-300 hover:scale-110" title="Settings">
                <Settings className="h-5 w-5" />
              </button> */}
              <a href='https://github.com/shivamsahu-tech/coderag-ai' target='_blank' className="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded-lg transition-all duration-300 hover:scale-110" title="Repository">
                <Github className="h-5 w-5" />
              </a>
            </div>
          </div>
        </div>
      </header>

      {/* Chat Container */}
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-6 relative z-10">
        <div className={`bg-gray-800/30 backdrop-blur-sm rounded-2xl border border-gray-700 shadow-2xl transform transition-all duration-1000 delay-300 ${
          isVisible ? 'scale-100 opacity-100' : 'scale-95 opacity-0'
        }`} style={{ height: 'calc(100vh - 200px)' }}>
          
          {/* Messages Area */}
          <div className="flex flex-col h-full">
            <div className="flex-1 overflow-y-auto p-6 space-y-6 scrollbar-thin scrollbar-thumb-gray-600 scrollbar-track-gray-800">
              {messages.map((message, index) => (
                <div
                  key={message.id}
                  className={`flex items-start space-x-4 animate-slide-in-up ${
                    message.type === 'user' ? 'flex-row-reverse space-x-reverse' : ''
                  }`}
                  style={{ animationDelay: `${index * 100}ms` }}
                >
                  {/* Avatar */}
                  <div className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${
                    message.type === 'bot' 
                      ? 'bg-gradient-to-r from-blue-500 to-purple-600 animate-glow' 
                      : 'bg-gradient-to-r from-green-500 to-teal-600'
                  }`}>
                    {message.type === 'bot' ? (
                      <Bot className="h-5 w-5 text-white" />
                    ) : (
                      <User className="h-5 w-5 text-white" />
                    )}
                  </div>

                  {/* Message Content */}
                  <div className={`flex-1 max-w-3xl ${
                    message.type === 'user' ? 'text-right' : ''
                  }`}>
                    <div className={`inline-block p-4 rounded-2xl shadow-lg transform hover:scale-[1.02] transition-all duration-300 ${
                      message.type === 'bot'
                        ? 'bg-gray-700/50 border border-gray-600 text-gray-100 rounded-tl-sm'
                        : 'bg-gray-700/50 border border-gray-600 text-gray-100 rounded-tr-sm'
                    }`}>
                      <div>
                        <MarkdownLoader content={message.content} />
                      </div>
                    </div>
                    <p className={`text-xs text-gray-500 mt-2 ${
                      message.type === 'user' ? 'text-right' : 'text-left'
                    }`}>
                      {message.timestamp.toLocaleTimeString()}
                    </p>
                  </div>
                </div>
              ))}

              {/* Typing Indicator */}
              {isTyping && (
                <div className="flex items-start space-x-4">
                  <div className="flex-shrink-0 w-10 h-10 rounded-full bg-gradient-to-r from-blue-500 to-purple-600 flex items-center justify-center animate-pulse">
                    <Bot className="h-5 w-5 text-white" />
                  </div>
                  <div className="flex-1">
                    <div className="inline-block p-4 bg-gray-700/50 border border-gray-600 rounded-2xl rounded-tl-sm">
                      <div className="flex space-x-1">
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="border-t border-gray-700 p-6 bg-gray-800/50 backdrop-blur-sm rounded-b-2xl">
              <form onSubmit={handleSendMessage} className="flex space-x-4">
                <div className="flex-1 relative group">
                  <Code className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5 group-hover:text-blue-400 transition-colors duration-300" />
                  <input
                    ref={inputRef}
                    type="text"
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    placeholder="Ask anything about your codebase..."
                    className="w-full pl-12 pr-4 py-4 bg-gray-700/50 border border-gray-600 text-white rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-300 backdrop-blur-sm hover:border-blue-500/50 hover:shadow-lg hover:shadow-blue-500/10"
                    disabled={isTyping}
                  />
                </div>
                <button
                  type="submit"
                  disabled={!inputMessage.trim() || isTyping}
                  className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white p-4 rounded-xl transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed hover:scale-105 hover:shadow-lg hover:shadow-blue-500/25 flex items-center justify-center min-w-[60px]"
                >
                  <Send className="h-5 w-5" />
                </button>
              </form>
              
              {/* Quick Actions
              <div className="mt-4 flex flex-wrap gap-2">
                {[
                  "How does authentication work?",
                  "Show me the main components",
                  "What are the key functions?",
                  "Explain the project structure"
                ].map((suggestion, index) => (
                  <button
                    key={index}
                    onClick={() => setInputMessage(suggestion)}
                    className="px-3 py-2 text-sm bg-gray-700/50 hover:bg-gray-600/50 text-gray-300 hover:text-white rounded-lg border border-gray-600 hover:border-gray-500 transition-all duration-300 hover:scale-105"
                  >
                    {suggestion}
                  </button>
                ))}
              </div> */}
            </div>
          </div>
        </div>
      </div>

      {/* Info Footer */}
      <div className="fixed bottom-4 right-4 z-50">
        <div className="bg-gray-800/90 backdrop-blur-sm border border-gray-700 rounded-lg p-3 text-sm text-gray-400 animate-fade-in">
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <span>AI Assistant Active</span>
          </div>
        </div>
      </div>

      <style jsx='true'>{`
        @keyframes gradient-x {
          0%, 100% { background-position: 0% 50%; }
          50% { background-position: 100% 50%; }
        }
        @keyframes float {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-20px); }
        }
        @keyframes glow {
          0%, 100% { box-shadow: 0 0 5px rgba(59, 130, 246, 0.3); }
          50% { box-shadow: 0 0 20px rgba(59, 130, 246, 0.6), 0 0 30px rgba(59, 130, 246, 0.4); }
        }
        @keyframes fade-in {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        @keyframes slide-in-up {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-gradient-x { animation: gradient-x 15s ease infinite; }
        .animate-float { animation: float 6s ease-in-out infinite; }
        .animate-glow { animation: glow 3s ease-in-out infinite; }
        .animate-fade-in { animation: fade-in 1s ease-out; }
        .scrollbar-thin {
          scrollbar-width: thin;
        }
        .scrollbar-thumb-gray-600::-webkit-scrollbar-thumb {
          background-color: #4B5563;
          border-radius: 0.375rem;
        }
        .scrollbar-track-gray-800::-webkit-scrollbar-track {
          background-color: #1F2937;
        }
        .scrollbar-thin::-webkit-scrollbar {
          width: 6px;
        }
      `}</style>
    </div>
  );
}
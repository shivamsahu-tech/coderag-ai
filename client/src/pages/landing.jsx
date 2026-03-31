import { Code, Database, Github, MessageCircle, Zap, MessageSquare, Hash, ArrowRight, Brain, Clock } from 'lucide-react';
import { useState, useEffect } from 'react';
import LoadingPage from './Loading';
import { useNavigate } from 'react-router-dom';
import WelcomeModal from '../components/WelcomeModal';

export default function Landing() {
  const [isVisible, setIsVisible] = useState(false);
  const [repoUrl, setRepoUrl] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState("")
  const [reqId, setReqId] = useState("")
  const navigate = useNavigate()

  // useEffect(() => {
  //   Alert("We are using Gemini Free tier API, So if limit already hit, you will not able to use this app.");
  // }, []);


  const joinSession = () => {
    navigate(`/chat/${sessionId}`)
  }

  const processRepo = async () => {
    if (!repoUrl) return;
    const newReqId = Date.now().toString() + Math.random().toString(36).substring(7);
    setReqId(newReqId);
    setIsLoading(true);
    try {
      const baseUrl = (import.meta.env.VITE_SERVER_URL || `http://${window.location.host}`).replace(/\/$/, "");
      const url = `${baseUrl}/api/ingest/`;
      console.log("[Landing] Constructing ingest URL:", url);
      console.log("[Landing] Req ID:", newReqId, "Repo URL:", repoUrl);
      
      const result = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ repo_url: repoUrl, req_id: newReqId })
      });
      console.log("[Landing] Fetch response status:", result.status, result.statusText);

      const res = await result.json();

      if (result.ok && res.status === "success") {
        console.log("Repo processed");
        console.log("res : ", res)
        setSessionId(res.session_id)
      } else {
        console.error("Error processing repo:", res.detail);
        alert(`Please try again or contact with the maintainer | Error : ${res.detail}`);
      }
    } catch (error) {
      console.error("Network error:", error);
      alert("Server not reachable!");
      setIsLoading(false);
    }
  };

  useEffect(() => {
    setIsVisible(true);
  }, []);

  return (
    isLoading ? (
      <LoadingPage sessionId={sessionId} reqId={reqId} />
    ) : (
      <div className="min-h-screen bg-gray-900 relative overflow-hidden">
        <WelcomeModal />
        {/* Animated Grid Background */}
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#374151_1px,transparent_1px),linear-gradient(to_bottom,#374151_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_80%_50%_at_50%_0%,#000_70%,transparent_110%)] animate-pulse"></div>

        {/* Animated gradient overlay */}
        <div className="absolute inset-0 bg-gradient-to-br from-blue-900/20 via-purple-900/20 to-gray-900/40 animate-gradient-x"></div>

        {/* Floating particles */}
        <div className="absolute inset-0">
          {[...Array(20)].map((_, i) => (
            <div
              key={i}
              className="absolute w-1 h-1 bg-blue-400/30 rounded-full animate-float"
              style={{
                left: `${Math.random() * 100}%`,
                top: `${Math.random() * 100}%`,
                animationDelay: `${Math.random() * 5}s`,
                animationDuration: `${3 + Math.random() * 4}s`
              }}
            />
          ))}
        </div>

        {/* Navigation */}
        <nav className="bg-gray-800/90 backdrop-blur-md border-b border-gray-700 sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center py-4">
              <div className={`flex items-center space-x-3 transform transition-all duration-1000 ${isVisible ? 'translate-x-0 opacity-100' : '-translate-x-10 opacity-0'
                }`}>
                <div className="bg-gradient-to-r from-blue-500 to-purple-600 p-2 rounded-lg animate-glow">
                  <Code className="h-6 w-6 text-white" />
                </div>
                <h1 className="text-2xl font-bold text-white">
                  CodeRAG Agent
                </h1>
              </div>
              <div className={`flex space-x-6 transform transition-all duration-1000 delay-200 ${isVisible ? 'translate-x-0 opacity-100' : 'translate-x-10 opacity-0'
                }`}>
                <a href="#about" className="text-gray-300 hover:text-white transition-colors duration-300 hover:glow">About</a>
                <a href="#features" className="text-gray-300 hover:text-white transition-colors duration-300 hover:glow">Features</a>
                <a href="https://github.com/shivamsahu-tech/coderag-ai" className="text-gray-300 hover:text-white transition-colors duration-300 hover:glow"><Github /></a>
              </div>
            </div>
          </div>
        </nav>

        {/* Hero Section */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-16 relative z-10">
          <div className="text-center">
            <h1 className={`text-5xl font-bold text-white mb-6 transform transition-all duration-1000 delay-300 ${isVisible ? 'translate-y-0 opacity-100' : 'translate-y-10 opacity-0'
              }`}>
              Chat with Your
              <span className="bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent animate-gradient-text"> Codebase</span>
            </h1>
            <p className={`text-xl text-gray-300 mb-12 max-w-3xl mx-auto transform transition-all duration-1000 delay-500 ${isVisible ? 'translate-y-0 opacity-100' : 'translate-y-10 opacity-0'
              }`}>
              Transform any GitHub repository into an intelligent AI assistant. Ask questions, explore code structure,
              and get instant insights about your projects using advanced RAG technology.
            </p>

            {/* Features Grid */}
            <div className="grid md:grid-cols-3 gap-8 mb-16">
              {[
                { icon: Github, title: "Repository Analysis", desc: "Automatically clones and analyzes your entire GitHub repository structure", delay: "delay-700" },
                { icon: Database, title: "Vector Embeddings", desc: "Creates semantic embeddings for intelligent code understanding", delay: "delay-900" },
                { icon: MessageCircle, title: "Natural Chat", desc: "Chat naturally about your code with context-aware responses", delay: "delay-1000" }
              ].map((feature, index) => (
                <div
                  key={index}
                  className={`bg-gray-800/50 backdrop-blur-sm p-6 rounded-xl border border-gray-700 hover:border-blue-500/50 hover:shadow-2xl hover:shadow-blue-500/10 transition-all duration-500 hover:scale-105 group transform ${isVisible ? 'translate-y-0 opacity-100' : 'translate-y-10 opacity-0'
                    } ${feature.delay}`}
                >
                  <div className="bg-gradient-to-r from-blue-500/20 to-purple-600/20 w-12 h-12 rounded-lg flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform duration-300">
                    <feature.icon className="h-6 w-6 text-blue-400 group-hover:text-blue-300 transition-colors duration-300" />
                  </div>
                  <h3 className="text-lg font-semibold mb-2 text-white group-hover:text-blue-300 transition-colors duration-300">{feature.title}</h3>
                  <p className="text-gray-400 group-hover:text-gray-300 transition-colors duration-300">{feature.desc}</p>
                </div>
              ))}
            </div>








            {/* Input Form */}
            <div className={`max-w-4xl mx-auto transform transition-all duration-1000 delay-1200 ${isVisible ? 'translate-y-0 opacity-100' : 'translate-y-10 opacity-0'
              }`}>
              <div className="grid md:grid-cols-2 gap-6">
                {/* Create New Session */}
                <div className="space-y-4 p-6 rounded-2xl bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-sm border border-gray-700/50 hover:border-blue-500/50 transition-all duration-300">
                  <div className="flex items-center space-x-2 mb-4">
                    <div className="h-10 w-10 rounded-lg bg-blue-500/10 flex items-center justify-center">
                      <Github className="h-5 w-5 text-blue-400" />
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-white">Create New Session</h3>
                      <p className="text-xs text-gray-400">Start with a GitHub repository</p>
                    </div>
                  </div>

                  <div className="relative group">
                    <Github className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5 group-hover:text-blue-400 transition-colors duration-300" />
                    <input
                      type="url"
                      value={repoUrl}
                      onChange={(e) => setRepoUrl(e.target.value)}
                      placeholder="https://github.com/user/repo"
                      className="w-full pl-12 pr-4 py-3 text-sm border border-gray-600 bg-gray-800/50 text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-300 backdrop-blur-sm hover:border-blue-500/50"
                    />
                  </div>

                  <button
                    onClick={processRepo}
                    disabled={!repoUrl.trim()}
                    className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white font-semibold py-3 px-6 rounded-lg transform hover:scale-[1.02] transition-all duration-300 flex items-center justify-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed hover:shadow-xl hover:shadow-blue-500/25"
                  >
                    <Zap className="h-4 w-4" />
                    <span>Generate Assistant</span>
                  </button>
                </div>

                {/* Join Existing Session */}
                <div className="space-y-4 p-6 rounded-2xl bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-sm border border-gray-700/50 hover:border-blue-500/50 transition-all duration-300">
                  <div className="flex items-center space-x-2 mb-4">
                    <div className="h-10 w-10 rounded-lg bg-blue-500/10 flex items-center justify-center">
                      <MessageSquare className="h-5 w-5 text-blue-400" />
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-white">Join Existing Session</h3>
                      <p className="text-xs text-gray-400">Continue with a session ID</p>
                    </div>
                  </div>

                  <div className="relative group">
                    <Hash className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5 group-hover:text-blue-400 transition-colors duration-300" />
                    <input
                      type="text"
                      value={sessionId}
                      onChange={(e) => setSessionId(e.target.value)}
                      placeholder="Enter session ID"
                      className="w-full pl-12 pr-4 py-3 text-sm border border-gray-600 bg-gray-800/50 text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-300 backdrop-blur-sm hover:border-blue-500/50"
                    />
                  </div>

                  <button
                    onClick={joinSession}
                    disabled={!sessionId.trim()}
                    className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white font-semibold py-3 px-6 rounded-lg transform hover:scale-[1.02] transition-all duration-300 flex items-center justify-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed hover:shadow-xl hover:shadow-blue-500/25"
                  >
                    <ArrowRight className="h-4 w-4" />
                    <span>Join Session</span>
                  </button>
                </div>
              </div>

              <p className="text-sm text-gray-400 mt-6 text-center animate-fade-in-up">
                Your repository will be analyzed securely. We don't store your code permanently.
              </p>
            </div>












          </div>
        </div>

        {/* How It Works Section */}
        <div id='about' className="relative z-10 py-20 bg-gray-800/30 backdrop-blur-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-16">
              <h2 className="text-4xl font-bold text-white mb-4 animate-fade-in">How It Works</h2>
              <p className="text-xl text-gray-300 max-w-2xl mx-auto animate-fade-in-up">
                Get your AI-powered codebase assistant up and running in just three simple steps
              </p>
            </div>

            <div className="grid md:grid-cols-3 gap-12 mb-16">
              {[
                { num: "1", title: "Submit Repository", desc: "Paste your GitHub repository URL and let our system analyze your codebase structure and dependencies." },
                { num: "2", title: "AI Processing", desc: "Our AI creates semantic embeddings of your code, understanding context, patterns, and relationships." },
                { num: "3", title: "Start Chatting", desc: "Ask questions about your code, get explanations, find bugs, or explore implementation details instantly." }
              ].map((step, index) => (
                <div key={index} className="text-center group hover:scale-105 transition-all duration-500 animate-slide-in-up" style={{ animationDelay: `${index * 200}ms` }}>
                  <div className="bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-full w-12 h-12 flex items-center justify-center mx-auto mb-6 text-xl font-bold group-hover:shadow-lg group-hover:shadow-blue-500/50 transition-all duration-300 animate-bounce-slow">
                    {step.num}
                  </div>
                  <h3 className="text-xl font-semibold mb-4 text-white group-hover:text-blue-300 transition-colors duration-300">{step.title}</h3>
                  <p className="text-gray-400 group-hover:text-gray-300 transition-colors duration-300">{step.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Use Cases Section */}
        <div className="relative z-10 py-20">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-16">
              <h2 className="text-4xl font-bold text-white mb-4 animate-fade-in">Perfect For</h2>
              <p className="text-xl text-gray-300 max-w-2xl mx-auto animate-fade-in-up">
                Whether you're onboarding, debugging, or exploring, CodeRAG Agent adapts to your needs
              </p>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
              {[
                { emoji: "👨‍💻", title: "Developers", desc: "Quickly understand unfamiliar codebases and find relevant code sections" },
                { emoji: "👥", title: "Teams", desc: "Onboard new team members faster with instant code explanations" },
                { emoji: "🔍", title: "Code Review", desc: "Get context about code changes and understand implementation decisions" },
                { emoji: "📚", title: "Learning", desc: "Study open-source projects and understand complex architectures" }
              ].map((useCase, index) => (
                <div
                  key={index}
                  className="bg-gray-800/50 backdrop-blur-sm p-6 rounded-xl border border-gray-700 hover:border-purple-500/50 hover:shadow-2xl hover:shadow-purple-500/10 transition-all duration-500 hover:scale-105 group animate-slide-in-up"
                  style={{ animationDelay: `${index * 100}ms` }}
                >
                  <div className="text-2xl mb-4 group-hover:scale-110 transition-transform duration-300">{useCase.emoji}</div>
                  <h3 className="text-lg font-semibold mb-2 text-white group-hover:text-purple-300 transition-colors duration-300">{useCase.title}</h3>
                  <p className="text-gray-400 text-sm group-hover:text-gray-300 transition-colors duration-300">{useCase.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Features Details */}
        <div id='features' className="relative z-10 py-20 bg-gray-800/30 backdrop-blur-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-16">
              <h2 className="text-4xl font-bold text-white mb-4 animate-fade-in">Powerful Features</h2>
              <p className="text-xl text-gray-300 max-w-2xl mx-auto animate-fade-in-up">
                Advanced AI capabilities designed specifically for code understanding
              </p>
            </div>

            <div className="grid lg:grid-cols-2 gap-12 items-center">
              <div className="animate-slide-in-left">
                <div className="space-y-8">
                  {[
                    { icon: Code, title: "Intelligent Code Search", desc: "Find functions, classes, and patterns using natural language queries instead of exact syntax matching." },
                    { icon: Database, title: "Context-Aware Responses", desc: "Get answers that understand your entire codebase context, not just isolated code snippets." },
                    { icon: Brain, title: "Agentic Retrieval", desc: "Autonomous AI agents intelligently search and retrieve relevant code snippets, documentation, and patterns across your repository." },
                    { icon: Clock, title: "Chat Memories", desc: "Conversations are remembered across sessions, providing consistent context and building on previous discussions for deeper insights." },
                    { icon: Zap, title: "Lightning Fast", desc: "Powered by advanced vector embeddings for instant responses, even on large repositories." },
                  ].map((feature, index) => (
                    <div key={index} className="flex items-start space-x-4 group hover:scale-105 transition-all duration-300">
                      <div className="bg-gradient-to-r from-blue-500/20 to-purple-600/20 p-3 rounded-lg flex-shrink-0 group-hover:shadow-lg group-hover:shadow-blue-500/30 transition-all duration-300">
                        <feature.icon className="h-6 w-6 text-blue-400 group-hover:text-blue-300 transition-colors duration-300" />
                      </div>
                      <div>
                        <h3 className="text-xl font-semibold mb-2 text-white group-hover:text-blue-300 transition-colors duration-300">{feature.title}</h3>
                        <p className="text-gray-400 group-hover:text-gray-300 transition-colors duration-300">{feature.desc}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              <div className="bg-gray-900 rounded-2xl p-8 text-white border border-gray-700 hover:border-blue-500/50 hover:shadow-2xl hover:shadow-blue-500/20 transition-all duration-500 animate-slide-in-right">
                <div className="space-y-4">
                  <div className="flex items-center space-x-2 text-gray-400">
                    <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
                    <div className="w-3 h-3 bg-yellow-500 rounded-full animate-pulse" style={{ animationDelay: '0.5s' }}></div>
                    <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse" style={{ animationDelay: '1s' }}></div>
                    <span className="ml-4 text-sm animate-typing">CodeRAG Agent Chat</span>
                  </div>
                  <div className="bg-gray-800 rounded-lg p-4 space-y-3 border border-gray-700">
                    <div className="text-blue-400 animate-fade-in">You:</div>
                    <div className="text-gray-300 animate-typing">"Find all places where we handle payment processing and show me potential race conditions"</div>
                    <div className="text-green-400 mt-4 animate-fade-in" style={{ animationDelay: '2s' }}>AI:</div>
                    <div className="text-gray-300"> The authentication system uses JWT tokens with a middleware pattern. Here's the flow: <br />

                      1. `services/payment.js` Line 45: Missing transaction lock during balance check <br />
                      2. `api/checkout.js` Line 128: Concurrent order creation without mutex <br />
                      3. `webhooks/stripe.js` Line 67: Event handling lacks idempotency key validation <br />
                      4. `models/Order.js` Line 203: Status update lacks optimistic locking mechanism <br />
                      5. `utils/refund.js` Line 89: Refund amount calculation reads stale inventory data <br />
                      6. `controllers/subscription.js` Line 156: Renewal process allows duplicate charges

                      All of these could cause data inconsistencies under high load. I can show you the exact code patterns and suggest atomic operation fixes with database-level locking. Want to dive deeper into any specific file?</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* CTA Section */}
        <div className="relative z-10 py-20">
          <div className="max-w-4xl mx-auto text-center px-4 sm:px-6 lg:px-8">
            <h2 className="text-4xl font-bold text-white mb-6 animate-fade-in">Ready to Transform Your Development Workflow?</h2>
            <p className="text-xl text-gray-300 mb-8 max-w-2xl mx-auto animate-fade-in-up">
              Join thousands of developers who are already using AI to understand code faster and build better software.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center animate-slide-in-up">
              <button className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white font-semibold py-4 px-8 rounded-xl transition-all duration-300 flex items-center space-x-2 hover:scale-105 hover:shadow-2xl hover:shadow-blue-500/25 animate-glow"
                onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
              >
                <span>Get Started Free</span>
                <Zap className="h-5 w-5 animate-bounce" />
              </button>
              <a href='https://github.com/shivamsahu-tech/coderag-ai/blob/main/README.md' className="border border-gray-600 hover:border-blue-500 text-gray-300 hover:text-white font-semibold py-4 px-8 rounded-xl transition-all duration-300 hover:scale-105 hover:shadow-lg hover:shadow-blue-500/20">
                View Documentation
              </a>
            </div>
          </div>
        </div>

        {/* Footer */}
        <footer className="relative z-10 bg-gray-900 border-t border-gray-800 text-white py-12">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="grid md:grid-cols-4 gap-8">
              <div className="md:col-span-2 animate-slide-in-left">
                <div className="flex items-center space-x-3 mb-4">
                  <div className="bg-gradient-to-r from-blue-500 to-purple-600 p-2 rounded-lg animate-glow">
                    <Code className="h-6 w-6 text-white" />
                  </div>
                  <h3 className="text-2xl font-bold">CodeRAG Agent</h3>
                </div>
                <p className="text-gray-400 mb-6 max-w-md">
                  Making codebases more accessible through intelligent AI-powered conversations.
                  Understand any repository instantly.
                </p>
                <div className="flex space-x-4">
                  <a href='https://github.com/shivamsahu-tech/coderag-ai' className="text-gray-400 hover:text-white transition-colors duration-300 hover:scale-110 transform">
                    <Github className="h-5 w-5" />
                  </a>
                  <button className="text-gray-400 hover:text-white transition-colors duration-300 hover:scale-110 transform">
                    <MessageCircle className="h-5 w-5" />
                  </button>
                </div>
              </div>
              <div className="animate-slide-in-up" style={{ animationDelay: '200ms' }}>
                <h4 className="font-semibold mb-4 text-white">Product</h4>
                <ul className="space-y-2 text-gray-400">
                  <li><a href="#" className="hover:text-white transition-colors duration-300">Features</a></li>
                  <li><a href="#" className="hover:text-white transition-colors duration-300">Pricing</a></li>
                  <li><a href="#" className="hover:text-white transition-colors duration-300">API</a></li>
                  <li><a href="#" className="hover:text-white transition-colors duration-300">Documentation</a></li>
                </ul>
              </div>
              <div className="animate-slide-in-up" style={{ animationDelay: '400ms' }}>
                <h4 className="font-semibold mb-4 text-white">Support</h4>
                <ul className="space-y-2 text-gray-400">
                  <li><a href="#" className="hover:text-white transition-colors duration-300">Help Center</a></li>
                  <li><a href="#" className="hover:text-white transition-colors duration-300">Contact Us</a></li>
                  <li><a href="#" className="hover:text-white transition-colors duration-300">Status</a></li>
                  <li><a href="#" className="hover:text-white transition-colors duration-300">Privacy</a></li>
                </ul>
              </div>
            </div>
            <div className="border-t border-gray-800 mt-12 pt-8 text-center animate-fade-in">
              <p className="text-gray-400">&copy; 2024 CodeRAG Agent. All rights reserved.</p>
            </div>
          </div>
        </footer>

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
        @keyframes gradient-text {
          0%, 100% { background-position: 0% 50%; }
          50% { background-position: 100% 50%; }
        }
        @keyframes pulse-slow {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.8; }
        }
        @keyframes bounce-slow {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-5px); }
        }
        @keyframes fade-in {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        @keyframes fade-in-up {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes slide-in-up {
          from { opacity: 0; transform: translateY(30px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes slide-in-left {
          from { opacity: 0; transform: translateX(-30px); }
          to { opacity: 1; transform: translateX(0); }
        }
        @keyframes slide-in-right {
          from { opacity: 0; transform: translateX(30px); }
          to { opacity: 1; transform: translateX(0); }
        }
        .animate-gradient-x { animation: gradient-x 15s ease infinite; }
        .animate-float { animation: float 6s ease-in-out infinite; }
        .animate-glow { animation: glow 3s ease-in-out infinite; }
        .animate-gradient-text { 
          background-size: 200% 200%;
          animation: gradient-text 3s ease infinite; 
        }
        .animate-pulse-slow { animation: pulse-slow 3s ease-in-out infinite; }
        .animate-bounce-slow { animation: bounce-slow 2s ease-in-out infinite; }
        .animate-fade-in { animation: fade-in 1s ease-out; }
        .animate-fade-in-up { animation: fade-in-up 1s ease-out; }
        .animate-slide-in-up { animation: slide-in-up 0.8s ease-out; }
        .animate-slide-in-left { animation: slide-in-left 0.8s ease-out; }
        .animate-slide-in-right { animation: slide-in-right 0.8s ease-out; }
        .animate-typing { animation: typing 2s steps(40, end); }
      `}</style>
      </div>
    ));
}
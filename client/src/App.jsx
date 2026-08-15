import Landing from "./pages/landing";
import ChatPage from "./pages/chat";
import { Routes, Route } from "react-router-dom";
import { useEffect } from "react";

export default function App() {

  useEffect(() => {
    // Wake up the server
    const baseUrl = (import.meta.env.VITE_SERVER_URL || `http://${window.location.host}`).replace(/\/$/, "");
    fetch(`${baseUrl}/health`).catch(err => console.error("Failed to wake up server:", err));
  }, []);

  return (
    <Routes>
      <Route path="/" element={ <Landing />} />
      <Route path="/chat/:sessionId" element={<ChatPage />} />
    </Routes> 
  )
}
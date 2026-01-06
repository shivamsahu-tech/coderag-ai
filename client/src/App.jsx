import Landing from "./pages/landing";
import ChatPage from "./pages/chat";
import { Routes, Route } from "react-router-dom";



export default function App() {

  

  return (
    <Routes>
      <Route path="/" element={ <Landing />} />
      <Route path="/chat/:sessionId" element={<ChatPage />} />
    </Routes> 
  )
}
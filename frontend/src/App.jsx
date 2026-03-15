import { Routes, Route } from 'react-router-dom';
import Home from './pages/Home';
import UploadPage from './pages/UploadPage';
import ResultsPage from './pages/ResultsPage';
import './App.css'


function App() {
  return(
    <div className="app">
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/upload" element={<UploadPage />} />
        <Route path="/results" element={<ResultsPage />} />
      </Routes>
    </div>
  )
}

export default App

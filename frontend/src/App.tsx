import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import DocumentList from './pages/DocumentList';
import DocumentEditor from './pages/DocumentEditor';
import './App.css';

function App() {
    return (
        <Router>
            <Routes>
                <Route path="/" element={<DocumentList />} />
                <Route path="/doc/:docId" element={<DocumentEditor />} />
            </Routes>
        </Router>
    );
}

export default App;

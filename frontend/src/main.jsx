// import react module
import React from 'react';
// import react dom
import ReactDOM from 'react-dom/client';
// import main app
import App from './App';
// import global styles
import './index.css';

// mount root component
ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App /> {/* render application */}
  </React.StrictMode>
);

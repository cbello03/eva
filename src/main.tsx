import React from 'react';
import ReactDOM from 'react-dom/client';
import { App } from './app/App';

// Buscamos el div con id "root" en el index.html y montamos nuestra App ahí
const rootElement = document.getElementById('root');

if (rootElement) {
  ReactDOM.createRoot(rootElement).render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
}
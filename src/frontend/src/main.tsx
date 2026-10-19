import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import '@fontsource/inter/400.css';
import '@fontsource/inter/500.css';
import '@fontsource/inter/600.css';
import '@fontsource/inter/700.css';
import '@radix-ui/themes/styles.css';
import { Theme } from '@radix-ui/themes';
import './index.css';
import App from './App';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <Theme accentColor="red" grayColor="slate" radius="large" scaling="100%" appearance="light">
    <BrowserRouter>
      <App />
    </BrowserRouter>
    </Theme>
  </React.StrictMode>,
);

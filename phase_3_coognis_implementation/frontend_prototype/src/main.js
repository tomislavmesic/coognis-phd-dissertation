import { createApp } from 'vue';
import App from './App.vue';
import router from './router';
import './assets/scss/main.scss';
import { initTheme } from './services/themeService';

initTheme();
createApp(App).use(router).mount('#app');

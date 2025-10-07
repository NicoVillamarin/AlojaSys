import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

// Importar archivos de traducción
import es from './locales/es.json';
import en from './locales/en.json';
import pt from './locales/pt.json';

const resources = {
  es: {
    translation: es
  },
  en: {
    translation: en
  },
  pt: {
    translation: pt
  }
};

i18n
  .use(initReactI18next)
  .init({
    resources,
    lng: localStorage.getItem('preferred-language') || 'es', // idioma guardado o español por defecto
    fallbackLng: 'es', // idioma de respaldo
    interpolation: {
      escapeValue: false // React ya escapa los valores
    }
  });

export default i18n;

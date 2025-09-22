/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        aloja: {
          // Marca
          navy: "#0A304A",     // Azul Petróleo
          navy2: "#002D62",    // Alternativa Navy
          gold: "#D4AF37",     // Dorado Acento
          gold2: "#FFD700",    // Mostaza Acento

          // Neutros sugeridos
          white: "#FFFFFF",
          gray: {
            50: "#F5F5F5",     // Fondo secundario
            100: "#EEEEEE",
            800: "#333333",    // Texto cuerpo
          },
        },
      },
    },
  },
  plugins: [],
};



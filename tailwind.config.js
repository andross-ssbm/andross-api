/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
      "./templates/**/*.html",
      "./templates/*.html",
      "./static/src/**/*.js"
  ],
  theme: {
      fontFamily: {
        'sans': ['Inter']
      },
      colors: {
          'white': '#FFFFFFFF',
          'background-md': '#36393f',
          'background-dark': '#3a3d42',
          'dark-theme-highlight': '#2b2d31',
          'slate': '#939599',
          'win-green': '#2ecc40',
          'loss-red': '#ff4d00',
          'slippi-green': '#21BA45'
      },
      extend: {},
  },
  plugins: [],
}


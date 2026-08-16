/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        // System stack — no external font loading, fast and clean
        sans: ['ui-sans-serif', 'system-ui', '-apple-system', 'Inter', 'sans-serif'],
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'],
      },
      colors: {
        // A restrained, government-data-viewer palette. The green
        // is used sparingly for "confirmed sponsorship" affirmatives.
        ink: '#0f172a',
        paper: '#fafaf9',
        rule: '#e5e5e5',
        accent: '#0f766e',   // teal-700, used for the sponsorship counts
        muted: '#64748b',
      },
    },
  },
  plugins: [],
};

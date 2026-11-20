/** @type {import('tailwindcss').Config} */

// A small, muted palette. Every Tailwind colour name used in the app is
// remapped onto one of these families, so class names stay the same while
// the look changes in one place.
const paper = {
  // warm greys (replaces slate / gray / zinc / neutral / stone)
  50: '#f7f6f3',
  100: '#efede8',
  200: '#e2dfd8',
  300: '#ccc8bf',
  400: '#a29d92',
  500: '#7a756b',
  600: '#5c5850',
  700: '#46433d',
  800: '#2f2d29',
  900: '#1f1e1b',
  950: '#151412',
};

const ink = {
  // petrol blue: primary actions, focus, selection
  50: '#f2f5f7',
  100: '#e1e8ed',
  200: '#c3d1db',
  300: '#9bb2c2',
  400: '#6d8ca2',
  500: '#4d6f87',
  600: '#3a5a71',
  700: '#2f4a5e',
  800: '#283e4e',
  900: '#233542',
  950: '#15212a',
};

const denim = {
  // theory classes / informational
  50: '#f1f4f9',
  100: '#e2e8f2',
  200: '#c6d2e5',
  300: '#9fb2d0',
  400: '#7690b8',
  500: '#58739d',
  600: '#465d82',
  700: '#3a4c6a',
  800: '#323f57',
  900: '#2c3649',
  950: '#1c2230',
};

const plum = {
  // labs
  50: '#f7f3f6',
  100: '#eee4ec',
  200: '#dccad8',
  300: '#c2a5bb',
  400: '#a27c98',
  500: '#865f7c',
  600: '#6f4c66',
  700: '#5c3f55',
  800: '#4d3647',
  900: '#422f3d',
  950: '#261a23',
};

const moss = {
  // success / published
  50: '#f3f6f1',
  100: '#e3eadf',
  200: '#c8d6c0',
  300: '#a3bb98',
  400: '#7d9c70',
  500: '#5f7f53',
  600: '#4a6641',
  700: '#3c5236',
  800: '#33432e',
  900: '#2c3828',
  950: '#161f14',
};

const brick = {
  // errors / clashes / destructive
  50: '#fbf3f1',
  100: '#f5e2de',
  200: '#eac3bb',
  300: '#da9b8f',
  400: '#c57263',
  500: '#ad5545',
  600: '#934536',
  700: '#79392d',
  800: '#653129',
  900: '#552c25',
  950: '#2e1411',
};

const ochre = {
  // warnings / drafts / breaks
  50: '#fbf7ee',
  100: '#f4ead2',
  200: '#e8d3a4',
  300: '#d8b672',
  400: '#c89b4c',
  500: '#b08337',
  600: '#92692b',
  700: '#755226',
  800: '#614425',
  900: '#523a22',
  950: '#2e1f10',
};

export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['"IBM Plex Sans"', 'system-ui', 'sans-serif'],
        mono: ['"IBM Plex Mono"', 'ui-monospace', 'monospace'],
      },
      colors: {
        primary: ink,
        indigo: ink,
        slate: paper,
        gray: paper,
        zinc: paper,
        neutral: paper,
        stone: paper,
        blue: denim,
        sky: denim,
        cyan: denim,
        purple: plum,
        violet: plum,
        fuchsia: plum,
        pink: plum,
        emerald: moss,
        green: moss,
        teal: moss,
        lime: moss,
        rose: brick,
        red: brick,
        amber: ochre,
        orange: ochre,
        yellow: ochre,
      },
    },
  },
  plugins: [],
};

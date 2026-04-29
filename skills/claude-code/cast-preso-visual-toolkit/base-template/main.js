import 'reveal.js/dist/reveal.css';
import './theme.css';
import Reveal from 'reveal.js';
import Notes from 'reveal.js/plugin/notes/notes.esm.js';
import Highlight from 'reveal.js/plugin/highlight/highlight.esm.js';
import Zoom from 'reveal.js/plugin/zoom/zoom.esm.js';

// Callout mode: ?callout=none|manual|automatic (default: manual)
const CALLOUT_MODE = new URLSearchParams(location.search).get('callout') || 'manual';

if (CALLOUT_MODE === 'none') {
  document.body.classList.add('no-animations');
} else if (CALLOUT_MODE === 'automatic') {
  document.body.classList.add('timed-animations');
  // Set auto-advance on callout fragments that don't already have it
  document.querySelectorAll('.callout.fragment:not([data-autoslide])').forEach(el => {
    el.setAttribute('data-autoslide', '2000');
  });
}

const deck = new Reveal();
deck.initialize({
  width: 1920,
  height: 1080,
  margin: 0.04,
  hash: true,
  history: true,
  overview: true,
  navigationMode: 'default',
  controls: true,
  controlsBackArrows: 'visible',
  pdfSeparateFragments: false,
  pdfMaxPagesPerSlide: 1,
  plugins: [Notes, Highlight, Zoom],
});

// Prevent flash of unstyled content
deck.on('ready', () => {
  document.querySelector('.reveal').style.visibility = 'visible';
});

// FALLBACK: If data-autoslide per-fragment is not supported in reveal.js 5.x,
// uncomment the following block and remove the setAttribute loop above:
//
// if (CALLOUT_MODE === 'automatic') {
//   deck.on('fragmentshown', (event) => {
//     if (event.fragment.classList.contains('callout')) {
//       setTimeout(() => deck.next(), 2000);
//     }
//   });
// }

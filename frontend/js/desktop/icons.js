// Pixel icons on a 16×16 grid, drawn crisp at any size. Colours come from CSS classes
// (desktop.css), so every colour stays a token.

const svg = (body) =>
  `<svg class="px-icon" viewBox="0 0 16 16" shape-rendering="crispEdges" aria-hidden="true">${body}</svg>`;

export const folderIcon = () =>
  svg(`
    <rect class="px-lavender" x="2" y="14" width="14" height="1"/>
    <rect class="px-lavender" x="15" y="5" width="1" height="10"/>
    <rect class="px-pink-deep" x="1" y="2" width="6" height="3"/>
    <rect class="px-pink-deep" x="1" y="4" width="14" height="10"/>
    <rect class="px-pink" x="1" y="6" width="14" height="8"/>
    <rect class="px-cream" x="2" y="7" width="12" height="1"/>
    <path class="px-line" d="M1.5 13.5V2.5H6.5L7.5 4.5H14.5V13.5ZM1.5 6.5H14.5"/>
  `);

export const documentIcon = () =>
  svg(`
    <rect class="px-lavender" x="4" y="15" width="10" height="1"/>
    <rect class="px-lavender" x="13" y="4" width="1" height="11"/>
    <rect class="px-cream" x="3" y="1" width="10" height="14"/>
    <path class="px-pink-deep" d="M10 1L13 4H10Z"/>
    <rect class="px-ink-soft" x="5" y="6" width="6" height="1"/>
    <rect class="px-ink-soft" x="5" y="8" width="6" height="1"/>
    <rect class="px-ink-soft" x="5" y="10" width="4" height="1"/>
    <path class="px-line" d="M3.5 1.5H10.5L12.5 3.5V14.5H3.5ZM10.5 1.5V3.5H12.5"/>
  `);

export const chatIcon = () =>
  svg(`
    <rect class="px-lavender" x="1" y="2" width="14" height="10"/>
    <rect class="px-cream" x="3" y="4" width="10" height="6"/>
    <rect class="px-pink-deep" x="5" y="5" width="6" height="3"/>
    <rect class="px-pink-deep" x="6" y="8" width="1" height="1"/>
    <rect class="px-cream" x="6" y="6" width="1" height="1"/>
    <rect class="px-cream" x="9" y="6" width="1" height="1"/>
    <rect class="px-purple" x="6" y="12" width="4" height="1"/>
    <rect class="px-purple" x="4" y="13" width="8" height="1"/>
    <path class="px-line" d="M1.5 2.5H14.5V11.5H1.5ZM4.5 13.5H11.5"/>
  `);

// Set which side we are: "red" or "blue"
const side = document.body.getAttribute('data-side') || 'red'; // default to red
const jsonFile = `json/${side}-beers.json`;
let currentRefreshToken = null;

// --- TEXT RESIZE ---
function autoResizeText(selector, maxSize = 80, minSize = 12, step = 1) {
  const elements = document.querySelectorAll(selector);
  elements.forEach(el => {
    el.style.fontSize = '';
    el.style.whiteSpace = 'nowrap';
    el.style.overflow = 'visible';
    el.style.textOverflow = 'unset';
    let fontSize = maxSize;
    el.style.fontSize = fontSize + 'px';
    while ((el.scrollWidth > el.clientWidth) && fontSize > minSize) {
      fontSize -= step;
      el.style.fontSize = fontSize + 'px';
      void el.offsetWidth; // force reflow
    }
  });
}


function resizeTextAll() {
  autoResizeText('.beer-name-wrapper', 72, 16);
  autoResizeText('.beer-info', 36, 12);
}

// --- LOGO STYLE ---
function styleTaplistLogo({ shadow, face, highlight }) {
  const logo = document.getElementById('taplist-logo');
  if (!logo) return;
  let attempts = 0, maxAttempts = 25;
  function tryTheme() {
    const svgDoc = logo.contentDocument;
    if (!svgDoc) {
      if (attempts++ < maxAttempts) return setTimeout(tryTheme, 50);
      return;
    }
    const shadowEl = svgDoc.querySelector('.logo-shadow');
    const faceEl = svgDoc.querySelector('.logo-face');
    const highlightEl = svgDoc.querySelector('.logo-highlight');
    if (shadowEl && faceEl && highlightEl) {
      shadowEl.style.fill = shadow;
      faceEl.style.fill = face;
      highlightEl.style.fill = highlight;
    } else if (attempts++ < maxAttempts) {
      setTimeout(tryTheme, 50);
    }
  }
  setTimeout(tryTheme, 50);
}

window.addEventListener('DOMContentLoaded', () => {
  const logo = document.getElementById('taplist-logo');
  if (logo) {
    logo.addEventListener('load', () => {
      styleTaplistLogo({
        shadow: getComputedStyle(document.body).getPropertyValue('--logo-shadow').trim(),
        face: getComputedStyle(document.body).getPropertyValue('--logo-face').trim(),
        highlight: getComputedStyle(document.body).getPropertyValue('--logo-highlight').trim()
      });
    });
    if (logo.contentDocument && logo.contentDocument.readyState === 'complete') {
      styleTaplistLogo({
        shadow: getComputedStyle(document.body).getPropertyValue('--logo-shadow').trim(),
        face: getComputedStyle(document.body).getPropertyValue('--logo-face').trim(),
        highlight: getComputedStyle(document.body).getPropertyValue('--logo-highlight').trim()
      });
    }
  }
});

// --- POPULATE MAIN DATA ---
Promise.all([
  fetch(jsonFile, { cache: 'no-store' }).then(res => res.json()),
  fetch('json/beer-database.json').then(res => res.json())
])
.then(([data, masterList]) => {
  // 1. Apply theme
  document.body.setAttribute('data-theme', data.theme || 'default');
  void document.body.offsetWidth; // Force reflow for new CSS vars

  // 1.5. Theme the taplist logo!
  const logo = document.getElementById('taplist-logo');
  if (logo) {
    if (logo.contentDocument && logo.contentDocument.readyState === 'complete') {
      styleTaplistLogo({
        shadow: getComputedStyle(document.body).getPropertyValue('--logo-shadow').trim(),
        face: getComputedStyle(document.body).getPropertyValue('--logo-face').trim(),
        highlight: getComputedStyle(document.body).getPropertyValue('--logo-highlight').trim()
      });
    }
    logo.addEventListener('load', () => {
      styleTaplistLogo({
        shadow: getComputedStyle(document.body).getPropertyValue('--logo-shadow').trim(),
        face: getComputedStyle(document.body).getPropertyValue('--logo-face').trim(),
        highlight: getComputedStyle(document.body).getPropertyValue('--logo-highlight').trim()
      });
    });
  }

  // 2. Refresh token logic (on initial load)
  if (currentRefreshToken === null) {
    currentRefreshToken = data.refreshToken;
  } else if (data.refreshToken !== currentRefreshToken) {
    location.reload();
  }

  // 3. Render beer list
  const beers = data.beers; // [{id, soldOut}, ...]
  const logoPlaceholders = document.querySelectorAll('.cell img.logo, .cell object.logo');
  const texts = document.querySelectorAll('.cell.text .text');

  beers.forEach((tap, i) => {
    const beer = masterList.find(b => b.id === tap.id);
    if (!beer) {
      console.warn(`Beer not found for tap id: ${tap.id}`);
      return;
    }

    const logoImg = logoPlaceholders[i];
    const text = texts[i];
    if (!logoImg || !text) return;

    const objectEl = document.createElement('object');
    objectEl.setAttribute('type', 'image/svg+xml');
    objectEl.setAttribute('data', `/logos/${beer.logoPath}`);
    objectEl.classList.add('logo');
    objectEl.style.width = '100%';
    objectEl.style.height = '100%';
    if (tap.soldOut === true) objectEl.classList.add('sold-out');

    logoImg.replaceWith(objectEl);

    objectEl.addEventListener('load', () => {
      let attempts = 0;
      const maxAttempts = 10;
      function tryStyleLogo() {
        const svgDoc = objectEl.contentDocument;
        if (svgDoc) {
          const logoFace = svgDoc.querySelector('.logo-face');
          const color = getComputedStyle(document.body).getPropertyValue('--logo-face').trim();
          if (logoFace) logoFace.style.fill = color;
        } else if (attempts < maxAttempts) {
          attempts++;
          setTimeout(tryStyleLogo, 100);
        }
      }
      tryStyleLogo();
    });

    const soldOut = tap.soldOut === true;
    text.innerHTML = `
      <div class="beer-name-wrapper ${soldOut ? 'sold-out' : ''}">
        <span class="beer-name-combined">
          <span class="brewery">${beer.brewery}</span>
          <span class="beer-title">${beer.title}</span>
        </span>
      </div>
      <div class="beer-info ${soldOut ? 'sold-out' : ''}">
        ${soldOut ? 'TEMPORARILY SOLD OUT' : `${beer.city}, ${beer.state} • ${beer.style} • ${beer.abv}% ABV`}
      </div>
    `;
  });

  // Run resize logic after render
  requestAnimationFrame(resizeTextAll);
});

// --- REFRESH TOKEN CHECKER ---
function checkRefresh() {
  fetch(jsonFile, { cache: 'no-store' })
    .then(res => res.json())
    .then(data => {
      if (currentRefreshToken === null) {
        currentRefreshToken = data.refreshToken;
      } else if (data.refreshToken !== currentRefreshToken) {
        location.reload();
      }
    });
}

checkRefresh();
setInterval(checkRefresh, 10000); // Check every 10 seconds

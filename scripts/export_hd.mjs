import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { findChrome, ChromeVisualBrowser } from 'file:///C:/Users/Julian/.agents/skills/archify/bin/visual-check.mjs';

async function evaluate(cdp, sessionId, expression, awaitPromise = false) {
  const response = await cdp.send('Runtime.evaluate', {
    expression,
    awaitPromise,
    returnByValue: true,
  }, sessionId);
  if (response.exceptionDetails) {
    throw new Error(response.exceptionDetails.exception?.description
      || response.exceptionDetails.text
      || 'Runtime.evaluate failed');
  }
  return response.result?.value;
}

async function exportHD() {
  const chromePath = findChrome();
  if (!chromePath) throw new Error('Chrome not found');

  console.log('Using Chrome:', chromePath);
  const browser = new ChromeVisualBrowser(chromePath);
  const sessionId = await browser.sessionPromise;

  try {
    const htmlPath = path.resolve('assets/arquitectura-ecoguide.html');
    const url = pathToFileURL(htmlPath);
    url.searchParams.set('theme', 'light');

    // 1920 viewport with 3x scale factor = true Ultra HD
    await browser.cdp.send('Emulation.setDeviceMetricsOverride', {
      width: 1920,
      height: 1080,
      deviceScaleFactor: 3,
      mobile: false,
    }, sessionId);

    const loaded = browser.cdp.waitFor('Page.loadEventFired', sessionId);
    await browser.cdp.send('Page.navigate', { url: url.href }, sessionId);
    await loaded;

    // Wait for fonts and Archify layout stability
    await evaluate(browser.cdp, sessionId, `(function() {
      document.documentElement.setAttribute('data-motion', 'still');
      const panel = document.querySelector('.diagram-container');
      if (panel) panel.setAttribute('data-detail-level', 'read');
      return (document.fonts ? document.fonts.ready : Promise.resolve()).then(() => {
        if (window.Archify && Archify.layoutStability && typeof Archify.layoutStability.whenStable === 'function') {
          return Archify.layoutStability.whenStable();
        }
      }).then(() => new Promise(r => setTimeout(r, 600)));
    })()`, true);

    // Get the exact bounding box of the diagram SVG
    const rect = await evaluate(browser.cdp, sessionId, `(function() {
      const svg = document.querySelector('.diagram-stage svg') || document.querySelector('svg');
      if (!svg) return null;
      const b = svg.getBoundingClientRect();
      return {
        x: Math.max(0, b.left - 16),
        y: Math.max(0, b.top - 16),
        width: b.width + 32,
        height: b.height + 32
      };
    })()`);

    console.log('Diagram bounding box:', rect);

    // Capture screenshot clipped to the diagram with 3x scale factor
    const capture = await browser.cdp.send('Page.captureScreenshot', {
      format: 'png',
      fromSurface: true,
      captureBeyondViewport: false,
      clip: rect ? {
        x: rect.x,
        y: rect.y,
        width: rect.width,
        height: rect.height,
        scale: 1, // deviceScaleFactor: 3 already scales it by 3x!
      } : undefined,
    }, sessionId);

    const pngBuffer = Buffer.from(capture.data, 'base64');
    fs.writeFileSync('assets/arquitectura-ecoguide.png', pngBuffer);
    console.log('Saved assets/arquitectura-ecoguide.png (size:', pngBuffer.length, 'bytes)');

    // Also extract standalone SVG
    const svgData = await evaluate(browser.cdp, sessionId, `(function() {
      var svg = document.querySelector('.diagram-stage svg') || document.querySelector('svg');
      if (!svg) return null;
      var styleTexts = [];
      var styles = document.querySelectorAll('style');
      for (var i = 0; i < styles.length; i++) {
        styleTexts.push(styles[i].textContent);
      }
      var clone = svg.cloneNode(true);
      var styleEl = document.createElementNS('http://www.w3.org/2000/svg', 'style');
      styleEl.textContent = styleTexts.join('\\n');
      clone.insertBefore(styleEl, clone.firstChild);
      clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
      return clone.outerHTML;
    })()`);

    if (svgData) {
      fs.writeFileSync('assets/arquitectura-ecoguide.svg', svgData, 'utf-8');
      console.log('Saved assets/arquitectura-ecoguide.svg (size:', svgData.length, 'bytes)');
    }

  } finally {
    try {
      await browser.cdp.send('Browser.close');
    } catch (e) {}
    try {
      await browser.close();
    } catch (e) {}
  }
}

exportHD().catch(err => {
  console.error('Export error:', err);
  process.exit(1);
});

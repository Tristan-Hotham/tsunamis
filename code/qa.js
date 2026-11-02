// QA: open index.html at desktop and phone widths, log console errors, take screenshots to qa/.
// Run from the study root with a static server (python3 -m http.server 8811; set PORT to change).
// MapLibre comes from a local npm copy (the CDN is not reachable from the build container); tiles and fonts are blocked
// here, so the screenshots show the offline base map (Natural Earth outlines and plate boundaries). NOML=1 blocks
// MapLibre too, to check that the page degrades gracefully.
const { chromium } = require("playwright");
const ML = process.env.MAPLIBRE_DIST || "/tmp/ml/node_modules/maplibre-gl/dist";
const fs = require("fs");
(async () => {
  fs.mkdirSync("qa", { recursive: true });
  const b = await chromium.launch({ args: ["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"] });
  const errs = [];
  const sizes = process.env.ONLY ? [[process.env.ONLY, process.env.ONLY === "phone" ? 390 : 1280, 860]] : [["desktop", 1280, 900], ["phone", 390, 844]];
  for (const [nm, vw, vh] of sizes) {
    const p = await b.newPage({ viewport: { width: vw, height: vh }, deviceScaleFactor: nm === "phone" ? 2 : 1 });
    await p.route(/arcgisonline|googleapis|gstatic/, r => r.abort());
    if (process.env.NOML) await p.route(/maplibre-gl/, r => r.abort());
    else {
      await p.route(/maplibre-gl@[\d.]+\/dist\/maplibre-gl\.js/, r => r.fulfill({ path: ML + "/maplibre-gl.js", contentType: "application/javascript" }));
      await p.route(/maplibre-gl@[\d.]+\/dist\/maplibre-gl\.css/, r => r.fulfill({ path: ML + "/maplibre-gl.css", contentType: "text/css" }));
    }
    p.on("console", m => { if (m.type() === "error" && !/ERR_FAILED|net::|Failed to load resource|AJAXError|tile/i.test(m.text())) errs.push(nm + ": " + m.text()); });
    p.on("pageerror", e => errs.push(nm + " pageerror: " + e.message));
    await p.goto("http://localhost:" + (process.env.PORT || 8811) + "/index.html", { waitUntil: "load" });
    await p.waitForTimeout(3500);
    const tag = process.env.NOML ? "noml_" : "";
    await p.screenshot({ path: `qa/${tag}${nm}_top.png` });
    const idle = () => p.evaluate(() => new Promise(r => { if (!window.map || !map.loaded) return r(); let done = false; const fin = () => { if (!done) { done = true; r(); } }; map.once("idle", fin); map.triggerRepaint(); setTimeout(fin, 40000); }));
    const shot = async (sel, f) => { await p.locator(sel).scrollIntoViewIfNeeded(); await p.waitForTimeout(500); if (!process.env.NOML && /atlas|map/.test(sel)) await idle(); await p.locator(sel).screenshot({ path: `qa/${tag}${nm}_${f}.png` }); };
    await shot("#atlas", "map");
    if (!process.env.NOML) {
      await p.evaluate(() => { const r = document.getElementById("yr"); r.value = 560; r.dispatchEvent(new Event("input")); });
      await p.waitForTimeout(900); await shot("#atlas", "map_1890s");
      await p.click('#modeRow [data-m="near"]'); await p.waitForTimeout(900); await shot("#atlas", "map_near");
      await p.click('#modeRow [data-m="upto"]');
      await p.click("#play"); await p.waitForTimeout(1500); await p.click("#play");
      await p.click('#tourRow [data-k="chile"]'); await p.waitForTimeout(3000); await shot("#atlas", "tour_chile");
      await p.click('#tourRow [data-k="sumatra"]'); await p.waitForTimeout(3000); await shot("#atlas", "tour_sumatra");
      await p.click('#tourRow [data-k="lituya"]'); await p.waitForTimeout(3000); await shot("#atlas", "tour_lituya");
      await p.click('#sizeRow [data-s="height"]'); await p.waitForTimeout(800); await p.click(".back"); await p.waitForTimeout(400);
      await p.evaluate(() => map.jumpTo({ center: [160, 18], zoom: 1 })); await p.waitForTimeout(900); await shot("#atlas", "size_height");
      await p.click('#sizeRow [data-s="deaths"]');
      await p.fill("#q", "Lisbon"); await p.waitForTimeout(400); await p.keyboard.press("Enter"); await p.waitForTimeout(3000); await shot("#atlas", "search_lisbon");
      await p.click("#causeRow .btn:nth-child(5)"); await p.waitForTimeout(700); await shot("#atlas", "cause_landslide"); await p.click("#causeRow .btn:nth-child(2)");
      await p.click(".lyrBtn"); await p.waitForTimeout(300); await p.locator('.lyrPanel [data-k="cities"]').check(); await p.waitForTimeout(500); await shot("#map", "layers_panel"); await p.click(".lyrBtn");
      // click the source at the map centre for a popup
      await p.click(".back").catch(() => {});
      await p.evaluate(() => { setV(1000); map.jumpTo({ center: [142.4, 38.3], zoom: 4 }); }); await p.waitForTimeout(1200);
      const hit = await p.evaluate(() => { const f = map.queryRenderedFeatures({ layers: ["ev"] }); if (!f.length) return null; const c = f.find(x => EV[x.properties.i].id === 5413) || f[0]; const xy = map.project(c.geometry.coordinates); const r = map.getContainer().getBoundingClientRect(); return [r.left + xy.x, r.top + xy.y]; });
      if (hit) { await p.mouse.click(hit[0], hit[1]); await p.waitForTimeout(1200); await shot("#atlas", "popup"); }
      else errs.push(nm + ": no sources rendered");
      const nf = await p.evaluate(() => [map.queryRenderedFeatures({ layers: ["ev"] }).length, RU ? RU.rows.length : 0]); console.log(nm, "sources rendered here, runups loaded:", nf);
    }
    for (const c of ["causeChart", "oceanChart", "runupChart", "travelChart", "farTable", "deathChart", "centuryChart", "countryChart"]) await shot("#" + c, c);
    if (nm === "phone" && !process.env.NOML) {
      await p.click("#theme"); await p.waitForTimeout(1200); await shot("#atlas", "dark_map"); await shot("#centuryChart", "dark_century");
      await p.locator("#atlas").scrollIntoViewIfNeeded(); await p.click(".mfs-btn"); await p.waitForTimeout(1500); await p.screenshot({ path: `qa/${nm}_fullscreen.png` });
      await p.click(".mfs-btn"); await p.waitForTimeout(600);
    }
    const ov = await p.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    console.log(nm, "horizontal overflow px:", ov);
    await p.close();
  }
  console.log("errors:", errs.length ? errs : "none");
  await b.close();
})();

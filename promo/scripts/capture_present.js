const { chromium } = require('playwright');
const path = process.argv[2], out = process.argv[3];
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  await p.route('**/*', r => r.request().url().startsWith('file:') ? r.continue() : r.abort());
  p.on('pageerror', e => console.log('ERR', e.message.slice(0,200)));
  await p.goto('file://' + path);
  await p.waitForTimeout(800);
  const info = await p.evaluate(() => {
    _AUTH.approved = true; document.body.classList.add('auth-ok');
    const g = document.getElementById('authGate'); if (g) g.style.display = 'none';
    const names = ['アオイ','カイト','ミサキ','レン','ユウ','シオン','ハル','ナギ','リツ','サク','トワ','ミオ','ソラ','ケイ','ヒナ'];
    session = { id: 'demo', name: 'DEMO' };
    N = 15;
    players = names.map((n, i) => ({ name: n, alpha: ALPHA[i], origIdx: i }));
    barsPerSector = 6; totalTurns = 5; turnMinutes = 10;
    rulesConfig = Object.assign({ ...DEFAULT_RULES_CONFIG }, { prizeMode: 'B' });
    initBars = Array(N * barsPerSector).fill(true);
    // deterministic pseudo-random removal over turns
    let seed = 7; const rnd = () => (seed = (seed * 9301 + 49297) % 233280) / 233280;
    turnSnapshots = { 0: [...initBars] };
    for (let t = 1; t <= 5; t++) {
      const prev = [...turnSnapshots[t - 1]];
      for (let k = 0; k < 9; k++) prev[Math.floor(rnd() * prev.length)] = false;
      turnSnapshots[t] = prev;
    }
    finalBars = [...turnSnapshots[5]];
    chips = Array(N).fill(0).map((_, i) => [14, 9, 3, 22, 6, 11, 2, 17, 8, 13, 5, 19, 7, 4, 15][i]);
    chipsConfirmed = true;
    placeHistory = [];
    buildSlides();
    for (const id of ['sessionOverlay', 'loadingOverlay', 'startPickerModal', 'disconnectModal']) { const e = document.getElementById(id); if (e) e.style.display = 'none'; }
    return slides.map((s, i) => i + ':' + s.type + (s.ruleId ? '/' + s.ruleId : '') + (s.turn ? '/t' + s.turn : ''));
  });
  console.log(info.join(' '));
  for (let i = 0; i < info.length; i++) {
    await p.evaluate(i => { curSlide = i; renderSlide(); }, i);
    await p.waitForTimeout(1200);
    await p.screenshot({ path: `${out}/s${String(i).padStart(2, '0')}_${info[i].split(':')[1].replace(/\//g, '_')}.png` });
  }
  await b.close();
})();

/* Injected into every mock test at build time.
   build_manifest.py also patches each test's own submit function so that it calls
   window.__vpCapture(...) with the questions, the user's answers and the time left.
   This file saves that result into the app's storage, adds a "Home" button on the
   result screen and protects against leaving a running test with the back button. */
(function () {
  var KEY = 'vpair_records';
  var saved = false;
  var started = false;

  var m = location.pathname.match(/m(\d+)\.html/i);
  var setNo = m ? parseInt(m[1], 10) : null;

  // remember that the test was started (click on a "Start" button)
  document.addEventListener('click', function (e) {
    var el = e.target && e.target.closest ? e.target.closest('button') : null;
    if (el && /start/i.test((el.id || '') + ' ' + (el.textContent || ''))) started = true;
  }, true);

  // called from the patched submit function of each test
  window.__vpCapture = function (qs, chosen, timeLeft, total) {
    if (saved) return;
    saved = true;
    try { record(qs, chosen, timeLeft, total); }
    catch (e) { try { console.log('vpair record failed', e); } catch (_) {} }
    try { addHomeButton(); } catch (e) {}
  };

  function record(qs, chosen, timeLeft, total) {
    var score = 0, c = 0, w = 0, s = 0;
    var subjects = [], subj = [], max = [], rows = [];
    for (var i = 0; i < qs.length; i++) {
      var q = qs[i];
      var si = subjects.indexOf(q.subject);
      if (si < 0) { subjects.push(q.subject); subj.push(0); max.push(0); si = subjects.length - 1; }
      var ch = Number(chosen(i)) || 0;
      var v;
      if (!ch) { v = 0; s++; }
      else if (ch === q.answer || (q.alt && ch === q.alt)) { v = 4; c++; }
      else { v = -1; w++; }
      score += v; subj[si] += v; max[si] += 4;
      rows.push([q.id, si, ch, q.answer]);
    }
    var now = Date.now();
    var rec = {
      id: now, set: setNo, title: document.title, ts: now,
      score: score, max: qs.length * 4,
      correct: c, wrong: w, skipped: s,
      subjects: subjects, subj: subj, subjMax: max,
      timeSec: Math.max(0, (Number(total) || 0) - (Number(timeLeft) || 0)),
      qs: rows
    };
    var list = [];
    try { list = JSON.parse(localStorage.getItem(KEY) || '[]'); if (!Array.isArray(list)) list = []; } catch (e) { list = []; }
    list.push(rec);
    localStorage.setItem(KEY, JSON.stringify(list));
  }

  function addHomeButton() {
    if (document.getElementById('vp-home')) return;
    var b = document.createElement('button');
    b.id = 'vp-home';
    b.textContent = '← Home · result saved';
    b.style.cssText = 'position:fixed;left:50%;bottom:16px;transform:translateX(-50%);z-index:2147483647;' +
      'padding:12px 20px;border-radius:999px;border:1px solid rgba(255,255,255,.25);background:#0F1530;color:#fff;' +
      'font:600 14px system-ui,sans-serif;box-shadow:0 8px 24px rgba(0,0,0,.4);cursor:pointer';
    b.onclick = function () {
      try { sessionStorage.setItem('vpair_goto', 'records'); } catch (e) {}
      history.go(-2);
      setTimeout(function () { location.href = '../index.html#records'; }, 900);
    };
    document.body.appendChild(b);
  }

  // Back button: ask before leaving a running test
  try { history.pushState({ vp: 1 }, ''); } catch (e) {}
  window.addEventListener('popstate', function () {
    if (started && !saved) {
      if (!confirm('Leave the test? Your progress will be lost.')) {
        try { history.pushState({ vp: 1 }, ''); } catch (e) {}
        return;
      }
    }
    history.back();
  });
})();
          

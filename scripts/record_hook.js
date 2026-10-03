/* Injected into every mock test at build time.
   Saves the result to the app's storage when the test is submitted,
   and protects against leaving a running test with the phone's back button. */
(function () {
  var KEY = 'vpair_records';
  var saved = false;
  var orig = window.submitTest;
  if (typeof orig !== 'function') return;

  var m = location.pathname.match(/m(\d+)\.html/i);
  var setNo = m ? parseInt(m[1], 10) : null;

  window.submitTest = function () {
    var r = orig.apply(this, arguments);
    if (!saved) {
      saved = true;
      try { record(); } catch (e) { try { console.log('record failed', e); } catch (_) {} }
    }
    try { addHomeButton(); } catch (e) {}
    return r;
  };

  function record() {
    var score = 0, c = 0, w = 0, s = 0;
    var subjects = [], subj = [], max = [], qs = [];
    QUESTIONS.forEach(function (q) {
      var si = subjects.indexOf(q.subject);
      if (si < 0) { subjects.push(q.subject); subj.push(0); max.push(0); si = subjects.length - 1; }
      var ch = responses[q.id], v;
      if (ch === undefined) { v = 0; s++; }
      else if (ch === q.answer) { v = 4; c++; }
      else { v = -1; w++; }
      score += v; subj[si] += v; max[si] += 4;
      qs.push([q.id, si, ch === undefined ? 0 : ch, q.answer]);
    });
    var now = Date.now();
    var rec = {
      id: now, set: setNo, title: document.title, ts: now,
      score: score, max: QUESTIONS.length * 4,
      correct: c, wrong: w, skipped: s,
      subjects: subjects, subj: subj, subjMax: max,
      timeSec: TOTAL_TIME_SECONDS - timeLeft,
      qs: qs
    };
    var list = [];
    try { list = JSON.parse(localStorage.getItem(KEY) || '[]'); if (!Array.isArray(list)) list = []; } catch (e) { list = []; }
    list.push(rec);
    localStorage.setItem(KEY, JSON.stringify(list));
  }

  function addHomeButton() {
    var rs = document.getElementById('result-screen');
    if (!rs || document.getElementById('vp-home')) return;
    var b = document.createElement('button');
    b.id = 'vp-home';
    b.className = 'action';
    b.style.cssText = 'width:100%;margin:0 0 12px;padding:12px';
    b.textContent = '← Back to Home (result saved in Test Records)';
    b.onclick = function () {
      try { sessionStorage.setItem('vpair_goto', 'records'); } catch (e) {}
      history.go(-2);
      setTimeout(function () { location.href = '../index.html#records'; }, 900);
    };
    rs.insertBefore(b, rs.firstChild);
  }

  // Back button: ask before leaving a running test
  try { history.pushState({ vp: 1 }, ''); } catch (e) {}
  window.addEventListener('popstate', function () {
    var started = document.getElementById('start-screen').style.display === 'none';
    var done = document.getElementById('result-screen').style.display === 'block';
    if (started && !done) {
      if (!confirm('Leave the test? Your progress will be lost.')) {
        try { history.pushState({ vp: 1 }, ''); } catch (e) {}
        return;
      }
    }
    history.back();
  });
})();

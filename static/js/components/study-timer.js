/**
 * LSStudy — Cronômetro global.
 *
 * Conversa com:
 *   GET  study:current_session   -> {active:false} | {active:true, id, status, ...}
 *   POST study:start_session     -> {session_id} | 409 {active_session}
 *   POST study:pause_session     -> {success, session}
 *   POST study:resume_session    -> {success, session}
 *   POST study:end_session       -> {success, hours, duration}
 *   GET  study:api_contests      -> [{id,name}]
 *   GET  study:api_materias  <id>-> [{id,name}]
 *   GET  study:api_assuntos  <id>-> [{id,name}]
 */
(function () {
  'use strict';

  const root = document.getElementById('study-timer');
  if (!root) return;

  const URLS = {
    current:  root.dataset.currentUrl,
    start:    root.dataset.startUrl,
    pause:    root.dataset.pauseUrl,
    resume:   root.dataset.resumeUrl,
    end:      root.dataset.endUrl,
    contests: root.dataset.contestsUrl,
    materias: root.dataset.materiasUrl,   // contém /0/ como placeholder
    assuntos: root.dataset.assuntosUrl,   // idem
  };

  let session = null;         // objeto serializado pela API
  let tickInterval = null;

  // ---------- elementos ----------
  const idleEl     = root.querySelector('[data-idle]');
  const activeEl   = root.querySelector('[data-active]');
  const modalEl    = root.querySelector('[data-modal]');
  const elapsedEl  = root.querySelector('[data-elapsed]');
  const subjectEl  = root.querySelector('[data-subject]');
  const topicEl    = root.querySelector('[data-topic]');
  const indicatorEl= root.querySelector('.study-timer__indicator');
  const btnPause   = root.querySelector('[data-action="pause"]');
  const btnResume  = root.querySelector('[data-action="resume"]');
  const btnStart   = root.querySelector('[data-action="start"]');
  const selContest = root.querySelector('[data-select="contest"]');
  const selSubject = root.querySelector('[data-select="subject"]');
  const selTopic   = root.querySelector('[data-select="topic"]');

  // ---------- HTTP ----------
  function getCookie(name) {
    const m = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return m ? decodeURIComponent(m.pop()) : '';
  }

  async function postForm(url, data) {
    const res = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'X-CSRFToken': getCookie('csrftoken'),
        'X-Requested-With': 'XMLHttpRequest',
      },
      body: new URLSearchParams(data).toString(),
      credentials: 'same-origin',
    });
    let json = null;
    try { json = await res.json(); } catch (_) {}
    if (!res.ok) {
      const err = new Error((json && json.error) || ('HTTP ' + res.status));
      err.status = res.status;
      err.payload = json;
      throw err;
    }
    return json;
  }

  async function getJson(url) {
    const res = await fetch(url, {
      headers: { 'X-Requested-With': 'XMLHttpRequest' },
      credentials: 'same-origin',
    });
    if (!res.ok) throw new Error('HTTP ' + res.status);
    return res.json();
  }

  // ---------- helpers ----------
  function fmtHMS(total) {
    total = Math.max(0, Math.floor(total));
    const h = Math.floor(total / 3600);
    const m = Math.floor((total % 3600) / 60);
    const s = total % 60;
    const pad = n => String(n).padStart(2, '0');
    return pad(h) + ':' + pad(m) + ':' + pad(s);
  }

  function elapsedSeconds(sess) {
    const startMs = new Date(sess.start_time).getTime();
    const refMs = (sess.status === 'PAUSED' && sess.paused_at)
      ? new Date(sess.paused_at).getTime()
      : Date.now();
    const raw = (refMs - startMs) / 1000 - (sess.total_paused_seconds || 0);
    return Math.max(0, raw);
  }

  function render() {
    if (!session || !session.active) {
      idleEl.hidden = false;
      activeEl.hidden = true;
      stopTick();
      return;
    }
    idleEl.hidden = true;
    activeEl.hidden = false;

    subjectEl.textContent = session.subject_name || '—';
    topicEl.textContent   = session.topic_name   || '—';
    indicatorEl.dataset.status = session.status === 'PAUSED' ? 'paused' : 'running';

    const paused = session.status === 'PAUSED';
    btnPause.hidden  = paused;
    btnResume.hidden = !paused;

    elapsedEl.textContent = fmtHMS(elapsedSeconds(session));
  }

  function startTick() {
    stopTick();
    tickInterval = setInterval(() => {
      if (!session || !session.active) return;
      elapsedEl.textContent = fmtHMS(elapsedSeconds(session));
    }, 1000);
  }
  function stopTick() {
    if (tickInterval) { clearInterval(tickInterval); tickInterval = null; }
  }

  // ---------- estado ----------
  async function sync() {
    try {
      const data = await getJson(URLS.current);
      session = (data && data.active) ? data : null;
      render();
      if (session) startTick();
    } catch (e) {
      console.error('[study-timer] sync falhou', e);
    }
  }

  // ---------- modal ----------
  async function openModal() {
    modalEl.hidden = false;
    selSubject.disabled = true;
    selSubject.innerHTML = '<option value="">Primeiro selecione um estudo</option>';
    selTopic.disabled = true;
    selTopic.innerHTML = '<option value="">Primeiro selecione uma matéria</option>';
    btnStart.disabled = true;

    selContest.innerHTML = '<option value="">Carregando...</option>';
    try {
      const contests = await getJson(URLS.contests);
      selContest.innerHTML = '<option value="">Selecione...</option>';
      contests.forEach(c => {
        const o = document.createElement('option');
        o.value = c.id; o.textContent = c.name;
        selContest.appendChild(o);
      });
    } catch (e) {
      selContest.innerHTML = '<option value="">Erro ao carregar</option>';
      console.error('[study-timer] contests', e);
    }
  }
  function closeModal() { modalEl.hidden = true; }

  async function onContestChange() {
    const id = selContest.value;
    selSubject.disabled = true;
    selSubject.innerHTML = '<option value="">Carregando...</option>';
    selTopic.disabled = true;
    selTopic.innerHTML = '<option value="">Primeiro selecione uma matéria</option>';
    btnStart.disabled = true;
    if (!id) return;

    const url = URLS.materias.replace('/0/', '/' + id + '/');
    try {
      const list = await getJson(url);
      selSubject.innerHTML = '<option value="">Selecione...</option>';
      list.forEach(m => {
        const o = document.createElement('option');
        o.value = m.id; o.textContent = m.name;
        selSubject.appendChild(o);
      });
      selSubject.disabled = false;
    } catch (e) {
      selSubject.innerHTML = '<option value="">Erro ao carregar</option>';
      console.error('[study-timer] materias', e);
    }
  }

  async function onSubjectChange() {
    const id = selSubject.value;
    selTopic.disabled = true;
    selTopic.innerHTML = '<option value="">Carregando...</option>';
    btnStart.disabled = true;
    if (!id) return;

    const url = URLS.assuntos.replace('/0/', '/' + id + '/');
    try {
      const list = await getJson(url);
      selTopic.innerHTML = '<option value="">Selecione...</option>';
      list.forEach(a => {
        const o = document.createElement('option');
        o.value = a.id; o.textContent = a.name;
        selTopic.appendChild(o);
      });
      selTopic.disabled = false;
    } catch (e) {
      selTopic.innerHTML = '<option value="">Erro ao carregar</option>';
      console.error('[study-timer] assuntos', e);
    }
  }

  function onTopicChange() { btnStart.disabled = !selTopic.value; }

  // ---------- ações ----------
  async function onStart() {
    const topicId = selTopic.value;
    if (!topicId) return;
    btnStart.disabled = true;
    try {
      await postForm(URLS.start, { topic: topicId });
      closeModal();
      await sync();
    } catch (e) {
      // 409 = já existe sessão ativa. Backend devolve a sessão viva: usamos ela.
      if (e.status === 409 && e.payload && e.payload.active_session) {
        closeModal();
        session = e.payload.active_session;
        session.active = true;
        render();
        startTick();
      } else {
        alert('Erro ao iniciar: ' + e.message);
        btnStart.disabled = false;
      }
    }
  }

  async function onPause() {
    try {
      const data = await postForm(URLS.pause, {});
      session = Object.assign({}, data.session, { active: true });
      render();
    } catch (e) { alert('Erro ao pausar: ' + e.message); }
  }

  async function onResume() {
    try {
      const data = await postForm(URLS.resume, {});
      session = Object.assign({}, data.session, { active: true });
      render();
      startTick();
    } catch (e) { alert('Erro ao retomar: ' + e.message); }
  }

  async function onFinish() {
    if (!confirm('Finalizar a sessão atual?')) return;
    try {
      await postForm(URLS.end, {});
      stopTick();
      session = null;
      render();
    } catch (e) { alert('Erro ao finalizar: ' + e.message); }
  }

  // ---------- wire ----------
  root.addEventListener('click', ev => {
    const el = ev.target.closest('[data-action]');
    if (!el || !root.contains(el)) return;
    const a = el.dataset.action;
    if (a === 'open-start-modal') { ev.preventDefault(); openModal(); }
    else if (a === 'close-modal') { ev.preventDefault(); closeModal(); }
    else if (a === 'start')  { ev.preventDefault(); onStart(); }
    else if (a === 'pause')  { ev.preventDefault(); onPause(); }
    else if (a === 'resume') { ev.preventDefault(); onResume(); }
    else if (a === 'finish') { ev.preventDefault(); onFinish(); }
  });

  if (selContest) selContest.addEventListener('change', onContestChange);
  if (selSubject) selSubject.addEventListener('change', onSubjectChange);
  if (selTopic)   selTopic.addEventListener('change',   onTopicChange);

  if (modalEl) {
    modalEl.addEventListener('click', ev => { if (ev.target === modalEl) closeModal(); });
  }
  document.addEventListener('keydown', ev => {
    if (ev.key === 'Escape' && modalEl && !modalEl.hidden) closeModal();
  });

  // boot + ressincroniza ao voltar para a aba
  sync();
  document.addEventListener('visibilitychange', () => { if (!document.hidden) sync(); });
})();

/* ============================================
   RESUME CHECKER — Main JavaScript
   ============================================ */

document.addEventListener('DOMContentLoaded', () => {

  // Page fade-in
  document.body.classList.add('page-loaded');

  // Theme Toggle Logic
  function initTheme() {
    const toggle = document.getElementById('themeToggle');
    if (!toggle) return;

    const setTheme = (theme) => {
      document.documentElement.setAttribute('data-theme', theme);
      localStorage.setItem('theme', theme);
      const icon = toggle.querySelector('i');
      if (icon) {
        icon.setAttribute('data-lucide', theme === 'dark' ? 'sun' : 'moon');
        if (typeof lucide !== 'undefined') lucide.createIcons();
      }
    };

    toggle.addEventListener('click', () => {
      const current = document.documentElement.getAttribute('data-theme') || 'dark';
      setTheme(current === 'dark' ? 'light' : 'dark');
    });

    // Initial icon state
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
    const icon = toggle.querySelector('i');
    if (icon) {
      icon.setAttribute('data-lucide', currentTheme === 'dark' ? 'sun' : 'moon');
      if (typeof lucide !== 'undefined') lucide.createIcons();
    }
  }
  initTheme();

  // Gradient mesh background on landing + dashboard
  if (document.querySelector('.landing-hero') || document.getElementById('dashboardGreeting')) {
    document.body.classList.add('gradient-bg');
  }

  // ============================================================
  // COUNT-UP ANIMATION
  // ============================================================
  function countUp(el, target, duration) {
    if (!el) return;
    const startTime = performance.now();
    function easeOutQuart(t) { return 1 - Math.pow(1 - t, 4); }
    function step(now) {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      el.textContent = Math.round(easeOutQuart(progress) * target) + '%';
      if (progress < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }

  // ============================================================
  // AUTH HELPERS
  // ============================================================

  async function apiFetch(url, options = {}) {
    const headers = { ...(options.headers || {}) };
    if (options.method && options.method.toUpperCase() !== 'GET') {
      const csrf = document.cookie.split('; ')
        .find(r => r.startsWith('csrf_access_token='))?.split('=')[1];
      if (csrf) headers['X-CSRF-TOKEN'] = decodeURIComponent(csrf);
    }
    const r = await fetch(url, { credentials: 'include', ...options, headers });
    const data = await r.json().catch(() => ({}));
    return { ok: r.ok, status: r.status, data };
  }

  async function fetchMe() {
    const { ok, data } = await apiFetch('/api/auth/me');
    return ok ? data : null;
  }

  function requireAuth(onUser) {
    fetchMe()
      .then(user => {
        if (!user) { window.location.href = 'auth.html'; return; }
        onUser(user);
      })
      .catch(() => { window.location.href = 'auth.html'; });
  }

  function getGreeting() {
    const h = new Date().getHours();
    if (h < 12) return 'morning';
    if (h < 17) return 'afternoon';
    return 'evening';
  }

  function showAuthError(form, msg) {
    let errEl = form.querySelector('.auth-error');
    if (!errEl) {
      errEl = document.createElement('p');
      errEl.className = 'auth-error';
      errEl.style.cssText = 'color:#ef4444;font-size:0.82rem;margin:0.5rem 0 0;text-align:center';
      form.appendChild(errEl);
    }
    errEl.textContent = msg;
  }

  // ============================================================
  // TOAST
  // ============================================================
  let _toastTimer = null;
  function showToast(msg, type = '') {
    let el = document.getElementById('_globalToast');
    if (!el) {
      el = document.createElement('div');
      el.id = '_globalToast';
      el.className = 'toast';
      document.body.appendChild(el);
    }
    el.textContent = msg;
    el.className = `toast${type ? ' toast-' + type : ''}`;
    requestAnimationFrame(() => el.classList.add('show'));
    clearTimeout(_toastTimer);
    _toastTimer = setTimeout(() => {
      el.classList.remove('show');
    }, type === 'error' ? 4000 : 2000);
  }

  // ============================================================
  // REPORT HELPERS
  // ============================================================

  function escHtml(s) {
    return String(s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  function scoreColor(score) {
    if (score >= 70) return 'green';
    if (score >= 50) return 'amber';
    return 'red';
  }

  function iconForType(type) {
    const m = { keyword:'<i data-lucide="key" style="width:16px;height:16px;"></i>', achievement:'<i data-lucide="trophy" style="width:16px;height:16px;"></i>', ats:'<i data-lucide="trending-up" style="width:16px;height:16px;"></i>', soft_skills:'<i data-lucide="message-square" style="width:16px;height:16px;"></i>', completeness:'<i data-lucide="clipboard-list" style="width:16px;height:16px;"></i>', general:'<i data-lucide="lightbulb" style="width:16px;height:16px;"></i>' };
    return m[type] || '<i data-lucide="lightbulb" style="width:16px;height:16px;"></i>';
  }

  function badgeForPriority(p) {
    if (p === 'high')   return '<span class="badge badge-danger">High</span>';
    if (p === 'medium') return '<span class="badge badge-warning">Medium</span>';
    return '<span class="badge badge-primary">Low</span>';
  }

  // ---- Score card tooltips ----
  const SCORE_TOOLTIPS = {
    keyword:      'Overlap with industry keywords and job description terms',
    achievement:  'Action verbs and quantified results in bullet points',
    ats:          'ATS compatibility — sections, formatting, word count',
    soft_skills:  'Soft skill terms detected (leadership, teamwork, etc.)',
    completeness: 'Presence of all key resume sections',
    jd_match:     'Semantic similarity between your resume and the job description (FAISS)',
  };

  // ---- loadReportData: renders all report sections from the API response ----
  function loadReportData(report) {
    console.log('[ResumeAI] report data:', report);
    const scores   = report.scores   || {};
    const metadata = report.metadata || {};

    // Hero gauge — job title + candidate name
    const jobTitleEl = document.getElementById('reportJobTitle');
    if (jobTitleEl) jobTitleEl.textContent = report.job_title || 'Resume Report';

    const candidateEl = document.getElementById('reportCandidateName');
    if (candidateEl && metadata.name) candidateEl.textContent = metadata.name;

    // Grade badge
    const gradeEl = document.getElementById('reportGrade');
    if (gradeEl && scores.grade) {
      const cls = scores.final >= 85 ? 'badge-success'
                : scores.final >= 70 ? 'badge-primary'
                : scores.final >= 55 ? 'badge-warning'
                : 'badge-danger';
      gradeEl.innerHTML = `<span class="badge ${cls}">${escHtml(scores.grade)}</span>`;
    }

    // Summary blockquote
    const summaryEl = document.getElementById('reportSummaryText');
    if (summaryEl && report.summary_paragraph) {
      summaryEl.textContent = report.summary_paragraph;
    }

    // ---- Score cards (5 modules + optional jd_match) ----
    const scoresGrid = document.getElementById('scoresGrid');
    if (scoresGrid) {
      const modules = [
        { key: 'keyword',      label: 'Keyword Match',     weight: '30%' },
        { key: 'achievement',  label: 'Achievement Impact', weight: '25%' },
        { key: 'ats',          label: 'ATS Compatibility',  weight: '20%' },
        { key: 'soft_skills',  label: 'Soft Skills',        weight: '15%' },
        { key: 'completeness', label: 'Completeness',       weight: '10%' },
      ];

      // Add jd_match card only if present
      if (scores.jd_match !== undefined && scores.jd_match !== null) {
        modules.push({ key: 'jd_match', label: 'Semantic Match (RAG)', weight: 'JD' });
      }

      scoresGrid.innerHTML = modules.map(m => {
        const val = scores[m.key] ?? 0;
        const col = scoreColor(val);

        let extra = '';
        if (m.key === 'completeness') {
          const wc  = metadata.word_count || 0;
          const bc  = metadata.bullet_count || 0;
          const wcOk = wc >= 300 && wc <= 1400;
          extra = `<div class="completeness-stats">${bc} bullets | <span class="${wcOk ? 'good' : 'bad'}">${wc} words</span></div>`;
        }

        const tip = SCORE_TOOLTIPS[m.key] || '';
        return `
          <div class="score-card has-tooltip">
            <div class="score-card-header">
              <span class="score-card-label">${escHtml(m.label)}</span>
              <span class="score-card-weight">${escHtml(m.weight)}</span>
            </div>
            <div class="score-card-value ${col}">${val}%</div>
            <div class="score-mini-bar">
              <div class="score-mini-bar-fill ${col}" style="width:${val}%"></div>
            </div>
            ${extra}
            ${tip ? `<div class="tooltip-text">${escHtml(tip)}</div>` : ''}
          </div>`;
      }).join('');
    }

    // ---- Found keywords ----
    const foundEl = document.getElementById('foundKeywordsTags');
    if (foundEl) {
      const found = scores.found_keywords || [];
      if (found.length) {
        foundEl.innerHTML = found.map(k => `<span class="pill pill-green">${escHtml(k)}</span>`).join('');
        foundEl.querySelectorAll('.pill').forEach((p, i) => {
          p.style.animationDelay = `${i * 30}ms`;
          p.classList.add('pill-pop');
        });
      } else {
        foundEl.innerHTML = '<span style="color:var(--muted);font-size:0.82rem">None detected</span>';
      }
    }

    // ---- Missing keywords (scores level — plain strings) ----
    const missingEl = document.getElementById('missingKeywordsTags');
    if (missingEl) {
      const missing = scores.missing_keywords || [];
      if (missing.length) {
        missingEl.innerHTML = missing.map(k => `<span class="pill pill-red">${escHtml(k)}</span>`).join('');
        missingEl.querySelectorAll('.pill').forEach((p, i) => {
          p.style.animationDelay = `${i * 30}ms`;
          p.classList.add('pill-pop');
        });
      } else {
        missingEl.innerHTML = '<span style="color:var(--muted);font-size:0.82rem">None — great job!</span>';
      }
    }

    // ---- Soft skills ----
    const softEl = document.getElementById('softSkillsTags');
    if (softEl) {
      const soft = scores.soft_found || [];
      if (soft.length) {
        softEl.innerHTML = soft.map(s => `<span class="pill pill-blue">${escHtml(s)}</span>`).join('');
        softEl.querySelectorAll('.pill').forEach((p, i) => {
          p.style.animationDelay = `${i * 30}ms`;
          p.classList.add('pill-pop');
        });
      } else {
        softEl.innerHTML = '<span style="color:var(--muted);font-size:0.82rem">None detected</span>';
      }
    }

    // ---- ATS penalties ----
    const atsPenSection = document.getElementById('atsPenaltiesSection');
    const atsPenEl      = document.getElementById('atsPenaltiesTags');
    const penalties     = scores.ats_penalties || [];
    if (atsPenSection && atsPenEl) {
      if (penalties.length) {
        atsPenSection.style.display = '';
        atsPenEl.innerHTML = penalties.map(p =>
          `<span class="ats-chip">⚠ ${escHtml(p)}</span>`
        ).join('');
      } else {
        atsPenSection.style.display = 'none';
      }
    }

    // ---- AI Suggestions (quick_win + suggestions[]) ----
    const explSection = document.getElementById('explanationsSection');
    if (explSection) {
      let html = '<div class="suggestions-header"><h2>AI Suggestions</h2></div>';

      if (report.quick_win) {
        html += `
          <div class="quick-win-box">
            <div class="qw-icon">⚡</div>
            <div>
              <h4>Quick Win</h4>
              <p>${escHtml(report.quick_win)}</p>
            </div>
          </div>`;
      }

      const suggestions = [...(report.suggestions || [])].sort((a, b) => {
        const order = { high: 0, medium: 1, low: 2 };
        return (order[a.priority] ?? 1) - (order[b.priority] ?? 1);
      });

      if (suggestions.length) {
        suggestions.forEach(s => {
          html += `
            <div class="suggestion-card ${escHtml(s.priority || 'low')}">
              <div class="sug-icon">${iconForType(s.type)}</div>
              <div class="sug-body">
                <h4>${escHtml(s.title)} ${badgeForPriority(s.priority)}</h4>
                <p>${escHtml(s.detail)}</p>
                ${s.example ? `<div class="sug-example"><strong>Example</strong>${escHtml(s.example)}</div>` : ''}
              </div>
            </div>`;
        });
      } else {
        html += `
          <div class="suggestions-empty">
            <span class="se-icon">✅</span>
            Your resume looks strong! No major issues found.
          </div>`;
      }

      explSection.innerHTML = html;
    }

    // ---- Improvement list (missing keywords objects + ATS penalties) ----
    const suggSection = document.getElementById('suggestionsSection');
    if (suggSection) {
      let html = '<h2>Improvement Checklist</h2>';
      const items = [];

      (report.missing_keywords || []).forEach(({ keyword, where_to_add }) => {
        items.push(`
          <div class="improvement-item">
            <span class="imp-dot danger"></span>
            <span class="imp-text">Add keyword: <strong>${escHtml(keyword)}</strong>${where_to_add ? ' — ' + escHtml(where_to_add) : ''}</span>
            <span class="badge badge-danger">High</span>
          </div>`);
      });

      penalties.forEach(p => {
        items.push(`
          <div class="improvement-item">
            <span class="imp-dot warning"></span>
            <span class="imp-text">${escHtml(p)}</span>
            <span class="badge badge-warning">Medium</span>
          </div>`);
      });

      if (!items.length) {
        items.push(`
          <div class="improvement-item">
            <span class="imp-dot" style="background:var(--success)"></span>
            <span class="imp-text">No critical keyword or ATS issues found — great work!</span>
          </div>`);
      }

      suggSection.innerHTML = html + items.join('');
    }
  }

  // ============================================================
  // HISTORY NORMALISER
  // Maps a MongoDB report document (from /api/resume/history) to the
  // same shape loadReportData() and the copy button expect.
  // ============================================================
  function normaliseHistoryDoc(doc) {
    const ai = doc.ai || {};
    return {
      report_id:        doc._id,
      job_title:        doc.jobTitle || 'Resume',
      scores:           doc.scores   || {},
      metadata:         doc.metadata || {},
      jd_analysis:      null,
      suggestions:      ai.suggestions      || [],
      missing_keywords: ai.missing_keywords || [],
      quick_win:        ai.quick_win        || '',
      summary_paragraph: ai.summary_paragraph || '',
    };
  }

  // ============================================================
  // REPORT PAGE — sessionStorage first, then history API fallback
  // ============================================================
  let reportData = null;
  if (document.querySelector('.report-page')) {
    window.scrollTo(0, 0);
    try {
      const stored = sessionStorage.getItem('lastReport');
      if (stored) reportData = JSON.parse(stored);
    } catch {}

    function showReportEmptyState() {
      const heroEl = document.querySelector('.report-hero');
      if (heroEl) {
        heroEl.innerHTML = `
          <div style="text-align:center;padding:2rem">
            <div style="margin-bottom:1rem"><i data-lucide="file-x" style="width:48px;height:48px;color:var(--muted)"></i></div>
            <h2>No report yet</h2>
            <p style="color:var(--sub);margin:0.5rem 0 1.5rem">Upload a resume to see your analysis here.</p>
            <a href="onboarding.html" class="btn btn-primary">Analyze Resume →</a>
          </div>`;
      }
      const copyBtn = document.getElementById('copyReportBtn');
      if (copyBtn) copyBtn.style.display = 'none';
    }

    function initReportPage(data) {
      reportData = data;
      loadReportData(data);

      // Gauge animation + glow + pulse
      const gaugeFill   = document.getElementById('gaugeFill');
      const gaugeNumber = document.getElementById('gaugeNumber');
      const gaugeSvg    = document.querySelector('.gauge-container svg');
      if (gaugeFill) {
        const circumference = 2 * Math.PI * 90;
        const target = (data.scores) ? data.scores.final : 0;
        setTimeout(() => {
          gaugeFill.style.strokeDashoffset = circumference - (target / 100) * circumference;
          if (gaugeNumber) countUp(gaugeNumber, target, target * 22);
          // Apply glow + pulse after animation settles
          setTimeout(() => {
            if (gaugeSvg) {
              const glowClass = target >= 70 ? 'glow-green' : target >= 55 ? 'glow-amber' : 'glow-red';
              gaugeSvg.classList.add(glowClass, 'pulse');
            }
          }, target * 22 + 300);
        }, 600);
      }

      // Staggered score card entrance + countUp per card
      setTimeout(() => {
        document.querySelectorAll('.score-card').forEach((card, i) => {
          setTimeout(() => {
            card.style.transitionDelay = '0ms';
            card.classList.add('card-animate-in');
            // Count up the value inside the card
            const valEl = card.querySelector('.score-card-value');
            if (valEl) {
              const match = valEl.textContent.match(/(\d+)/);
              if (match) countUp(valEl, parseInt(match[1], 10), 800);
            }
          }, i * 80);
        });
      }, 400);

      // Animate mini bars
      setTimeout(() => {
        document.querySelectorAll('.score-mini-bar-fill').forEach(bar => {
          const w = bar.style.width;
          bar.style.width = '0';
          requestAnimationFrame(() => { bar.style.width = w; });
        });
      }, 800);

      // Copy Report button
      const copyBtn = document.getElementById('copyReportBtn');
      if (copyBtn) {
        copyBtn.style.display = '';
        copyBtn.addEventListener('click', () => {
          const s = data.scores   || {};
          const m = data.metadata || {};
          const text = [
            'Resume Screening Report',
            `Name: ${m.name || 'Unknown'} | Job: ${data.job_title || 'Unknown'}`,
            `Overall Score: ${s.final}/100 (${s.grade})`,
            `Keyword: ${s.keyword}% | Achievement: ${s.achievement}% | ATS: ${s.ats}% | Soft Skills: ${s.soft_skills}% | Completeness: ${s.completeness}%`,
            `Quick Win: ${data.quick_win || 'N/A'}`,
            `Summary: ${data.summary_paragraph || 'N/A'}`,
          ].join('\n');
          navigator.clipboard.writeText(text)
            .then(() => showToast('Copied!', 'success'))
            .catch(() => showToast('Copy failed — try again', 'error'));
        });
      }
    }

    requireAuth(async () => {
      if (reportData) {
        initReportPage(reportData);
      } else {
        // Fallback: load most recent report from history API
        try {
          const { ok, data } = await apiFetch('/api/resume/history');
          if (ok && Array.isArray(data) && data.length) {
            const normalised = normaliseHistoryDoc(data[0]);
            sessionStorage.setItem('lastReport', JSON.stringify(normalised));
            initReportPage(normalised);
          } else {
            showReportEmptyState();
          }
        } catch {
          showReportEmptyState();
        }
      }
      // Init cover letter after report is loaded (reportData is set by initReportPage)
      initCoverLetter();
    });

    // ── Cover Letter Generator ──────────────────────────────────────
    function initCoverLetter() {
      const section     = document.getElementById('coverLetterSection');
      const controls    = document.getElementById('clControls');
      const signinMsg   = document.getElementById('clSigninMsg');
      const generateBtn = document.getElementById('clGenerateBtn');
      const skeleton    = document.getElementById('clSkeleton');
      const result      = document.getElementById('clResult');
      const textarea    = document.getElementById('clTextarea');
      const wordCount   = document.getElementById('clWordCount');
      const copyBtn     = document.getElementById('clCopyBtn');
      const downloadBtn = document.getElementById('clDownloadBtn');
      const regenBtn    = document.getElementById('clRegenBtn');
      const toneBtns    = document.querySelectorAll('.cl-tone-btn');
      if (!section) return;

      // Determine if user has a report_id (authenticated + saved)
      const rid = reportData?.report_id;
      if (!rid) {
        controls.style.display = 'none';
        signinMsg.style.display = '';
        return;
      }

      let selectedTone = 'professional';

      toneBtns.forEach(btn => {
        btn.addEventListener('click', () => {
          toneBtns.forEach(b => b.classList.remove('active'));
          btn.classList.add('active');
          selectedTone = btn.dataset.tone;
        });
      });

      async function generate() {
        generateBtn.disabled = true;
        if (regenBtn) regenBtn.disabled = true;
        result.style.display = 'none';
        skeleton.style.display = '';

        try {
          const { ok, data } = await apiFetch('/api/resume/cover-letter', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ report_id: rid, tone: selectedTone }),
          });

          skeleton.style.display = 'none';

          if (!ok) {
            showToast(data.error || 'Generation failed — please try again', 'error');
          } else {
            textarea.value = data.cover_letter || '';
            updateWordCount();
            result.style.display = '';
            // Update download filename with job title
            if (downloadBtn) {
              const safe = (data.job_title || 'cover_letter').replace(/[^a-z0-9_\-]/gi, '_');
              downloadBtn.dataset.filename = `${safe}_cover_letter.txt`;
            }
          }
        } catch {
          skeleton.style.display = 'none';
          showToast('Generation failed — please try again', 'error');
        } finally {
          generateBtn.disabled = false;
          if (regenBtn) regenBtn.disabled = false;
        }
      }

      function updateWordCount() {
        const words = textarea.value.trim().split(/\s+/).filter(Boolean).length;
        if (wordCount) wordCount.textContent = `${words} word${words !== 1 ? 's' : ''}`;
      }

      generateBtn.addEventListener('click', generate);
      regenBtn?.addEventListener('click', generate);

      textarea?.addEventListener('input', updateWordCount);

      copyBtn?.addEventListener('click', () => {
        navigator.clipboard.writeText(textarea.value)
          .then(() => showToast('Copied!', 'success'))
          .catch(() => showToast('Copy failed — try again', 'error'));
      });

      downloadBtn?.addEventListener('click', () => {
        const filename = downloadBtn.dataset.filename || 'cover_letter.txt';
        const blob = new Blob([textarea.value], { type: 'text/plain' });
        const url  = URL.createObjectURL(blob);
        const a    = document.createElement('a');
        a.href = url; a.download = filename;
        a.click();
        URL.revokeObjectURL(url);
      });
    }
  }

  // ============================================================
  // HISTORY LIST PAGE (history.html)
  // ============================================================
  if (document.querySelector('.history-page')) {
    function relativeDate(iso) {
      if (!iso) return '';
      const diff = Date.now() - new Date(iso).getTime();
      const mins  = Math.floor(diff / 60000);
      const hours = Math.floor(diff / 3600000);
      const days  = Math.floor(diff / 86400000);
      const weeks = Math.floor(days / 7);
      if (mins  < 60)  return `${mins}m ago`;
      if (hours < 24)  return `${hours}h ago`;
      if (days  < 7)   return `${days} day${days !== 1 ? 's' : ''} ago`;
      if (weeks < 5)   return `${weeks} week${weeks !== 1 ? 's' : ''} ago`;
      return new Date(iso).toLocaleDateString();
    }

    function shortDate(iso) {
      if (!iso) return '';
      return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    }

    function buildTrendChart(data) {
      const trendSection = document.getElementById('trendSection');
      const trendStats   = document.getElementById('trendStats');
      const trendSingleMsg = document.getElementById('trendSingleMsg');
      if (!trendSection || data.length === 0) return;

      trendSection.style.display = '';

      // ── Stat cards ──
      const scores  = data.map(r => r.scores?.final ?? 0);
      const bestIdx = scores.indexOf(Math.max(...scores));
      const best    = data[bestIdx];
      const latest  = data[0]; // sorted newest-first from API

      trendStats.innerHTML = `
        <div class="trend-stat-card">
          <div class="trend-stat-label">Best Score</div>
          <div class="trend-stat-value" style="color:var(--success)">${best.scores?.final ?? '—'}%</div>
          <div class="trend-stat-sub">${escHtml(best.jobTitle || 'Unknown')}</div>
        </div>
        <div class="trend-stat-card">
          <div class="trend-stat-label">Latest Score</div>
          <div class="trend-stat-value" style="color:var(--blue)">${latest.scores?.final ?? '—'}%</div>
          <div class="trend-stat-sub">${shortDate(latest.createdAt)}</div>
        </div>
        <div class="trend-stat-card">
          <div class="trend-stat-label">Total Screenings</div>
          <div class="trend-stat-value" style="color:var(--text)">${data.length}</div>
          <div class="trend-stat-sub">all time</div>
        </div>`;

      // ── Chart — chronological order (oldest first) ──
      const chrono   = [...data].reverse();
      const labels   = chrono.map(r => shortDate(r.createdAt));
      const vals     = chrono.map(r => r.scores?.final ?? 0);
      const ptColors = vals.map(v => v >= 70 ? '#22c55e' : v >= 55 ? '#f59e0b' : '#ef4444');

      if (data.length === 1) trendSingleMsg.style.display = '';

      const ctx = document.getElementById('trendChart').getContext('2d');
      new Chart(ctx, {
        type: 'line',
        data: {
          labels,
          datasets: [{
            label: 'Score',
            data: vals,
            borderColor: '#3b82f6',
            borderWidth: 2.5,
            pointBackgroundColor: ptColors,
            pointBorderColor: ptColors,
            pointRadius: 6,
            pointHoverRadius: 8,
            fill: true,
            backgroundColor: 'rgba(59,130,246,0.10)',
            tension: 0.35,
          }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: true,
          interaction: { mode: 'index', intersect: false },
          plugins: {
            legend: { display: false },
            tooltip: {
              backgroundColor: '#1e1e1e',
              borderColor: '#333',
              borderWidth: 1,
              titleColor: '#f1f5f9',
              bodyColor: '#94a3b8',
              padding: 10,
              callbacks: {
                title: (items) => {
                  const r = chrono[items[0].dataIndex];
                  return r.jobTitle || 'Resume';
                },
                label: (item) => {
                  const r = chrono[item.dataIndex];
                  const grade = r.scores?.grade || '';
                  return [`Score: ${item.raw}%`, `Grade: ${grade}`, `Date: ${shortDate(r.createdAt)}`];
                },
              },
            },
          },
          scales: {
            x: {
              grid: { color: '#222222' },
              ticks: { color: '#888888', font: { size: 11 } },
            },
            y: {
              min: 0, max: 100,
              grid: { color: '#222222' },
              ticks: { color: '#888888', font: { size: 11 }, callback: v => v + '%' },
            },
          },
        },
      });
    }

    function buildSparkline(canvas, scores) {
      const ctx = canvas.getContext('2d');
      const color = scores[scores.length - 1] >= 70 ? '#22c55e'
                  : scores[scores.length - 1] >= 55 ? '#f59e0b' : '#ef4444';
      new Chart(ctx, {
        type: 'line',
        data: {
          labels: scores.map((_, i) => i),
          datasets: [{ data: scores, borderColor: color, borderWidth: 1.5,
            pointRadius: 0, fill: false, tension: 0.4 }],
        },
        options: {
          responsive: false,
          animation: false,
          plugins: { legend: { display: false }, tooltip: { enabled: false } },
          scales: { x: { display: false }, y: { display: false, min: 0, max: 100 } },
        },
      });
    }

    requireAuth(async () => {
      const listEl = document.getElementById('historyPageList');
      if (!listEl) return;

      listEl.innerHTML = '<p style="color:var(--muted);font-size:0.875rem">Loading reports…</p>';

      try {
        const { ok, data } = await apiFetch('/api/resume/history');
        if (!ok || !Array.isArray(data) || !data.length) {
          listEl.innerHTML = `
            <div style="text-align:center;padding:3rem 1rem;color:var(--muted)">
              <div style="margin-bottom:1rem"><i data-lucide="inbox" style="width:40px;height:40px;color:var(--muted)"></i></div>
              <p>No reports yet. <a href="onboarding.html" style="color:var(--blue)">Analyze your first resume →</a></p>
            </div>`;
          if (typeof lucide !== 'undefined') lucide.createIcons();
          return;
        }

        // Build trend section
        buildTrendChart(data);

        // Group by jobTitle to detect repeated titles for sparklines
        const titleGroups = {};
        data.forEach(r => {
          const t = (r.jobTitle || 'Untitled').toLowerCase();
          if (!titleGroups[t]) titleGroups[t] = [];
          titleGroups[t].push(r.scores?.final ?? 0);
        });

        listEl.innerHTML = data.map(r => {
          const score    = r.scores?.final ?? null;
          const grade    = r.scores?.grade ?? '';
          const col      = score === null ? 'muted' : score >= 70 ? 'green' : score >= 55 ? 'amber' : 'red';
          const name     = r.metadata?.name || 'Resume';
          const title    = r.jobTitle || 'Untitled';
          const date     = relativeDate(r.createdAt);
          const gradeCls = score >= 85 ? 'badge-success' : score >= 70 ? 'badge-primary' : score >= 55 ? 'badge-warning' : 'badge-danger';
          const group    = titleGroups[(title).toLowerCase()] || [];
          const hasSpark = group.length > 1;

          const rightHtml = hasSpark
            ? `<div class="hrc-sparkline"><canvas data-spark="${escHtml(JSON.stringify(group.slice().reverse()))}" width="56" height="32"></canvas></div>
               <span class="hrc-score score-card-value ${col}" style="font-size:1.4rem">${score !== null ? score + '%' : '—'}</span>`
            : `<span class="hrc-score score-card-value ${col}" style="font-size:1.4rem">${score !== null ? score + '%' : '—'}</span>
               <span class="badge ${gradeCls}">${escHtml(grade)}</span>`;

          return `
            <div class="history-report-card" data-id="${escHtml(r._id)}" style="cursor:pointer">
              <div class="hrc-left">
                <div class="hrc-title">${escHtml(title)}</div>
                <div class="hrc-meta">${escHtml(name)} · ${date}</div>
              </div>
              <div class="hrc-right">${rightHtml}</div>
            </div>`;
        }).join('');

        // Draw sparklines
        listEl.querySelectorAll('canvas[data-spark]').forEach(canvas => {
          try {
            const scores = JSON.parse(canvas.dataset.spark);
            buildSparkline(canvas, scores);
          } catch {}
        });

        // Click to load report
        listEl.querySelectorAll('.history-report-card').forEach(card => {
          card.addEventListener('click', () => {
            const id  = card.dataset.id;
            const doc = data.find(r => r._id === id);
            if (!doc) return;
            const normalised = normaliseHistoryDoc(doc);
            sessionStorage.setItem('lastReport', JSON.stringify(normalised));
            window.location.href = 'report.html';
          });
        });

        if (typeof lucide !== 'undefined') lucide.createIcons();
      } catch {
        listEl.innerHTML = '<p style="color:var(--danger);font-size:0.875rem">Failed to load reports. Please try again.</p>';
      }
    });
  }

  // ============================================================
  // AUTH TABS
  // ============================================================
  const authTabs  = document.querySelectorAll('.auth-tab');
  const loginForm  = document.getElementById('loginForm');
  const signupForm = document.getElementById('signupForm');
  const authHeader = document.querySelector('.auth-header');

  if (authTabs.length) {
    fetchMe().then(user => { if (user) window.location.href = 'dashboard.html'; }).catch(() => {});

    if (window.location.hash === '#signup') switchAuthTab('signup');

    authTabs.forEach(tab => {
      tab.addEventListener('click', () => switchAuthTab(tab.dataset.tab));
    });

    function switchAuthTab(tabName) {
      authTabs.forEach(t => t.classList.toggle('active', t.dataset.tab === tabName));
      document.querySelectorAll('.auth-error').forEach(el => { el.textContent = ''; });
      if (tabName === 'login') {
        loginForm?.classList.remove('hidden');
        signupForm?.classList.add('hidden');
        if (authHeader) {
          authHeader.querySelector('h2').textContent = 'Welcome back';
          authHeader.querySelector('p').textContent  = 'Continue optimizing your resume';
        }
      } else {
        loginForm?.classList.add('hidden');
        signupForm?.classList.remove('hidden');
        if (authHeader) {
          authHeader.querySelector('h2').textContent = 'Create account';
          authHeader.querySelector('p').textContent  = 'Start optimizing your resume today';
        }
      }
    }

    loginForm?.addEventListener('submit', async e => {
      e.preventDefault();
      const btn = loginForm.querySelector('button[type=submit]');
      btn.disabled = true; btn.textContent = 'Logging in…';
      try {
        const { ok, data } = await apiFetch('/api/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            email:    document.getElementById('login-email').value.trim(),
            password: document.getElementById('login-password').value,
          }),
        });
        if (ok) { window.location.href = 'dashboard.html'; }
        else    { showAuthError(loginForm, data.error || 'Login failed'); btn.disabled = false; btn.textContent = 'Log In'; }
      } catch {
        showAuthError(loginForm, 'Network error. Please try again.');
        btn.disabled = false; btn.textContent = 'Log In';
      }
    });

    signupForm?.addEventListener('submit', async e => {
      e.preventDefault();
      const btn = signupForm.querySelector('button[type=submit]');
      btn.disabled = true; btn.textContent = 'Creating account…';
      try {
        const { ok, data } = await apiFetch('/api/auth/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            name:            document.getElementById('signup-name').value.trim(),
            email:           document.getElementById('signup-email').value.trim(),
            password:        document.getElementById('signup-password').value,
            currentRole:     document.getElementById('signup-role').value.trim(),
            experienceYears: document.getElementById('signup-experience').value,
            linkedInUrl:     document.getElementById('signup-linkedin').value.trim(),
          }),
        });
        if (ok) { window.location.href = 'dashboard.html'; }
        else    { showAuthError(signupForm, data.error || 'Registration failed'); btn.disabled = false; btn.textContent = 'Create Account'; }
      } catch {
        showAuthError(signupForm, 'Network error. Please try again.');
        btn.disabled = false; btn.textContent = 'Create Account';
      }
    });
  }

  // ============================================================
  // LANDING PAGE — auth check for navbar swap
  // ============================================================
  const landingHero = document.querySelector('.landing-hero');
  if (landingHero) {
    fetchMe().then(user => {
      if (user) {
        const navActions = document.getElementById('navActions');
        if (navActions) {
          navActions.innerHTML = `
            <a href="dashboard.html" class="btn btn-primary btn-sm">Go to Dashboard →</a>
            <button class="btn btn-secondary btn-sm" id="landingLogoutBtn">Sign Out</button>`;
          document.getElementById('landingLogoutBtn')?.addEventListener('click', () => {
            fetch('/api/auth/logout', { method: 'POST', credentials: 'include' })
              .finally(() => { window.location.href = 'auth.html'; });
          });
        }
      }
    }).catch(() => {});
  }

  // ============================================================
  // DASHBOARD — auth guard, profile, upload, history
  // ============================================================
  const dashboardGreeting = document.getElementById('dashboardGreeting');
  if (dashboardGreeting) {
    requireAuth(user => {
      const firstName = user.name ? user.name.split(' ')[0] : 'there';
      dashboardGreeting.innerHTML = `Good ${getGreeting()}, ${firstName} <i data-lucide="sun" style="display:inline-block; vertical-align:-3px; width:28px; height:28px; color:var(--warning)"></i>`;
      lucide.createIcons();

      const fullNameEl = document.getElementById('userFullName');
      if (fullNameEl) fullNameEl.textContent = user.name || '';

      const avatarEl = document.getElementById('userAvatar');
      if (avatarEl) avatarEl.textContent = user.name ? user.name.charAt(0).toUpperCase() : '?';

      const titleEl = document.getElementById('userTitle');
      if (titleEl) titleEl.textContent = user.role || 'Member';

      // Load history
      loadDashHistory();
    });

    // Dashboard upload zone
    const dashZone      = document.getElementById('dashUploadZone');
    const dashFileInput = document.getElementById('dashFileInput');
    const dashFileInfo  = document.getElementById('dashFileInfo');
    const dashFileName  = document.getElementById('dashFileName');
    const dashFileSize  = document.getElementById('dashFileSize');
    const dashScreenBtn = document.getElementById('dashScreenBtn');
    const dashJobTitle  = document.getElementById('dashJobTitle');
    const dashJdText    = document.getElementById('dashJdText');
    const dashSkeleton  = document.getElementById('dashSkeleton');
    const dashUploadArea = document.getElementById('dashUploadArea');
    let dashFile = null;

    function enableDashBtn() {
      if (dashScreenBtn) dashScreenBtn.disabled = !(dashFile && dashJobTitle?.value.trim());
    }

    dashJobTitle?.addEventListener('input', enableDashBtn);

    if (dashZone) {
      dashZone.addEventListener('click', () => dashFileInput?.click());
      dashZone.addEventListener('dragover', e => { e.preventDefault(); dashZone.classList.add('dragover'); });
      dashZone.addEventListener('dragleave', () => dashZone.classList.remove('dragover'));
      dashZone.addEventListener('drop', e => {
        e.preventDefault(); dashZone.classList.remove('dragover');
        handleDashFile(e.dataTransfer.files[0]);
      });
    }
    dashFileInput?.addEventListener('change', () => handleDashFile(dashFileInput.files[0]));

    function handleDashFile(file) {
      if (!file) return;
      dashFile = file;
      if (dashFileName) dashFileName.textContent = file.name;
      if (dashFileSize) dashFileSize.textContent = (file.size / 1024).toFixed(0) + ' KB';
      if (dashFileInfo) dashFileInfo.classList.remove('hidden');
      enableDashBtn();
    }

    dashScreenBtn?.addEventListener('click', async () => {
      // Client-side validation
      if (!dashFile) {
        if (dashZone) {
          dashZone.classList.remove('shake');
          void dashZone.offsetWidth; // reflow to re-trigger
          dashZone.classList.add('shake');
          dashZone.addEventListener('animationend', () => dashZone.classList.remove('shake'), { once: true });
        }
        showToast('Please upload a resume file (PDF or DOCX)', 'error');
        return;
      }
      if (!dashJobTitle?.value.trim()) {
        showToast('Please enter a job title', 'error');
        dashJobTitle?.focus();
        return;
      }

      dashScreenBtn.disabled = true;
      if (dashUploadArea) dashUploadArea.classList.add('hidden');
      if (dashSkeleton)   dashSkeleton.classList.remove('hidden');

      const fd = new FormData();
      fd.append('resume', dashFile);
      fd.append('job_title', dashJobTitle?.value.trim() || '');
      fd.append('job_description', dashJdText?.value.trim() || '');

      try {
        const { ok, data } = await apiFetch('/api/resume/analyze', { method: 'POST', body: fd });
        if (ok) {
          sessionStorage.setItem('lastReport', JSON.stringify(data));
          window.location.href = 'report.html';
        } else {
          if (dashSkeleton)   dashSkeleton.classList.add('hidden');
          if (dashUploadArea) dashUploadArea.classList.remove('hidden');
          dashScreenBtn.disabled = false;
          showToast(data.error || 'Analysis failed. Please try again.', 'error');
        }
      } catch {
        if (dashSkeleton)   dashSkeleton.classList.add('hidden');
        if (dashUploadArea) dashUploadArea.classList.remove('hidden');
        dashScreenBtn.disabled = false;
        showToast('Network error. Please check your connection.', 'error');
      }
    });
  }

  async function loadDashHistory() {
    const historyList = document.getElementById('historyList');
    if (!historyList) return;
    try {
      const { ok, data } = await apiFetch('/api/resume/history');
      if (!ok || !data.length) {
        historyList.innerHTML = `
          <div style="text-align:center;padding:1.5rem 0.5rem;color:var(--muted)">
            <div style="margin-bottom:0.5rem"><i data-lucide="inbox" style="width:28px;height:28px;color:var(--muted)"></i></div>
            <p style="font-size:0.82rem;line-height:1.5">No screenings yet.<br>Upload your first resume to get started.</p>
            <div style="font-size:1.2rem;margin-top:0.75rem;color:var(--border)">← try it on the left</div>
          </div>`;
        return;
      }
      const items = data.slice(0, 3).map(r => {
        const score  = r.scores?.final ?? '—';
        const grade  = r.scores?.grade ?? '';
        const date   = r.createdAt ? new Date(r.createdAt).toLocaleDateString() : '';
        const title  = r.jobTitle || 'Resume';
        const col    = typeof score === 'number' ? scoreColor(score) : 'muted';
        return `
          <div class="history-item">
            <div>
              <div class="history-item-title">${escHtml(title)}</div>
              <div class="history-item-date">${date}</div>
            </div>
            <div style="text-align:right">
              <span class="score-card-value ${col}" style="font-size:1.1rem">${score}%</span>
              ${grade ? `<div style="font-size:0.7rem;color:var(--muted);margin-top:0.1rem">${escHtml(grade)}</div>` : ""}
            </div>
          </div>`;
      });
      historyList.innerHTML = items.join('');
    } catch {
      historyList.innerHTML = '<p style="font-size:0.82rem;color:var(--muted)">Could not load history.</p>';
    }
  }

  // ============================================================
  // ONBOARDING PAGE
  // ============================================================
  if (document.querySelector('.onboarding-page')) {
    requireAuth(() => {});
  }

  // ============================================================
  // LOGOUT
  // ============================================================
  document.getElementById('logoutBtn')?.addEventListener('click', () => {
    fetch('/api/auth/logout', { method: 'POST', credentials: 'include' })
      .finally(() => { window.location.href = 'auth.html'; });
  });
  document.getElementById('sidebarLogout')?.addEventListener('click', () => {
    fetch('/api/auth/logout', { method: 'POST', credentials: 'include' })
      .finally(() => { window.location.href = 'auth.html'; });
  });

  // ============================================================
  // ONBOARDING STEPS
  // ============================================================
  let selectedFile = null;

  const steps          = [document.getElementById('step1'), document.getElementById('step2'), document.getElementById('step3')];
  const stepIndicators = document.querySelectorAll('.onboarding-step-indicator');
  const lines          = [document.getElementById('line1'), document.getElementById('line2')];

  function goToStep(n) {
    steps.forEach((s, i) => { if (s) s.classList.toggle('hidden', i !== n); });
    stepIndicators.forEach((ind, i) => {
      ind.classList.remove('active', 'done');
      if (i < n) ind.classList.add('done');
      if (i === n) ind.classList.add('active');
    });
    lines.forEach((l, i) => { if (l) l.classList.toggle('done', i < n); });
    if (n === 2) startAnalysis();
  }

  // Step 1 — validate
  const step1Next     = document.getElementById('step1Next');
  const jobTitleInput = document.getElementById('step1-job-title');
  const jobDescInput  = document.getElementById('step1-job-desc');

  function validateStep1() {
    if (step1Next && jobTitleInput && jobDescInput) {
      step1Next.disabled = !(jobTitleInput.value.trim() && jobDescInput.value.trim());
    }
  }
  jobTitleInput?.addEventListener('input', validateStep1);
  jobDescInput?.addEventListener('input', validateStep1);
  validateStep1();
  step1Next?.addEventListener('click', () => goToStep(1));

  // Step 2 — upload
  const uploadZone = document.getElementById('uploadZone');
  const fileInput  = document.getElementById('fileInput');
  const fileInfo   = document.getElementById('fileInfo');
  const fileName   = document.getElementById('fileName');
  const fileSize   = document.getElementById('fileSize');
  const step2Next  = document.getElementById('step2Next');
  const step2Back  = document.getElementById('step2Back');

  if (uploadZone) {
    uploadZone.addEventListener('click', () => fileInput?.click());
    uploadZone.addEventListener('dragover', e => { e.preventDefault(); uploadZone.classList.add('dragover'); });
    uploadZone.addEventListener('dragleave', () => uploadZone.classList.remove('dragover'));
    uploadZone.addEventListener('drop', e => {
      e.preventDefault(); uploadZone.classList.remove('dragover');
      handleFile(e.dataTransfer.files[0]);
    });
  }
  fileInput?.addEventListener('change', () => handleFile(fileInput.files[0]));

  function handleFile(file) {
    if (!file) return;
    selectedFile = file;
    if (fileName) fileName.textContent = file.name;
    if (fileSize) fileSize.textContent = (file.size / 1024).toFixed(0) + ' KB';
    if (fileInfo) fileInfo.classList.remove('hidden');
    if (step2Next) step2Next.disabled = false;
  }

  step2Back?.addEventListener('click', () => goToStep(0));
  step2Next?.addEventListener('click', () => goToStep(2));

  // Step 3 — analysis
  async function startAnalysis() {
    const ring        = document.getElementById('analysisProgress');
    const percentEl   = document.getElementById('analysisPercent');
    const pSteps      = ['pStep1','pStep2','pStep3','pStep4'].map(id => document.getElementById(id));
    const finishBtn   = document.getElementById('step3Finish');
    const step3El     = document.getElementById('step3');
    const circumference = 2 * Math.PI * 72;

    if (!selectedFile) {
      const msg = document.createElement('p');
      msg.style.cssText = 'color:#ef4444;text-align:center;margin-top:1rem;font-size:0.875rem';
      msg.textContent = 'No file selected. Please go back and upload your resume.';
      step3El?.appendChild(msg);
      return;
    }

    let vis = 0;
    const animInterval = setInterval(() => {
      if (vis < 85) {
        vis++;
        if (percentEl) percentEl.textContent = vis + '%';
        if (ring) ring.style.strokeDashoffset = circumference - (vis / 100) * circumference;
        if (vis === 25) { pSteps[0]?.classList.replace('active','done'); pSteps[1]?.classList.add('active'); }
        if (vis === 50) { pSteps[1]?.classList.replace('active','done'); pSteps[2]?.classList.add('active'); }
        if (vis === 75) { pSteps[2]?.classList.replace('active','done'); pSteps[3]?.classList.add('active'); }
      }
    }, 80);

    const formData = new FormData();
    formData.append('resume', selectedFile);
    if (jobTitleInput) formData.append('job_title', jobTitleInput.value.trim());
    if (jobDescInput)  formData.append('job_description', jobDescInput.value.trim());

    let result;
    try {
      result = await apiFetch('/api/resume/analyze', { method: 'POST', body: formData });
    } catch {
      result = { ok: false, data: { error: 'Network error. Please check your connection.' } };
    }

    clearInterval(animInterval);

    if (result.ok) {
      const finishAnim = setInterval(() => {
        vis++;
        if (percentEl) percentEl.textContent = vis + '%';
        if (ring) ring.style.strokeDashoffset = circumference - (vis / 100) * circumference;
        if (vis >= 100) {
          clearInterval(finishAnim);
          pSteps[3]?.classList.replace('active','done');
          sessionStorage.setItem('lastReport', JSON.stringify(result.data));
          if (finishBtn) {
            finishBtn.href = 'report.html';
            finishBtn.textContent = 'View Report →';
            finishBtn.classList.remove('hidden');
          }
        }
      }, 20);
    } else {
      if (percentEl) percentEl.textContent = '✗';
      if (ring) ring.style.strokeDashoffset = circumference * 0.5;
      const errEl = document.createElement('p');
      errEl.style.cssText = 'color:#ef4444;text-align:center;margin-top:1.25rem;font-size:0.875rem';
      errEl.textContent = result.data?.error || 'Analysis failed. Please try again.';
      step3El?.appendChild(errEl);
      if (finishBtn) {
        finishBtn.href = 'onboarding.html';
        finishBtn.textContent = '← Try Again';
        finishBtn.classList.remove('hidden');
      }
    }
  }

  // ============================================================
  // SIDEBAR TOGGLE
  // ============================================================
  document.getElementById('sidebarToggle')?.addEventListener('click', () => {
    document.getElementById('sidebar')?.classList.toggle('open');
  });

  // ============================================================
  // AI CHAT — real /api/chat calls
  // ============================================================
  const aiFab        = document.getElementById('aiFab');
  const aiChatPopup  = document.getElementById('aiChatPopup');
  const closeChatBtn = document.getElementById('closeChatBtn');
  const openChatBtn  = document.getElementById('openChatBtn');
  const clearChatBtn = document.getElementById('clearChatBtn');
  const chatInput    = document.getElementById('chatInput');
  const chatSendBtn  = document.getElementById('chatSendBtn');
  const chatMessages = document.getElementById('chatMessages');

  let chatInitialized = false;

  function toggleChat() {
    if (!aiChatPopup) return;
    const opening = !aiChatPopup.classList.contains('open');
    aiChatPopup.classList.toggle('open');
    if (opening && !chatInitialized) {
      chatInitialized = true;
      initChat();
    }
  }

  aiFab?.addEventListener('click', toggleChat);
  closeChatBtn?.addEventListener('click', toggleChat);
  openChatBtn?.addEventListener('click', toggleChat);

  async function initChat() {
    // If report is in sessionStorage, send a silent context message first
    try {
      const stored = sessionStorage.getItem('lastReport');
      if (stored) {
        const r = JSON.parse(stored);
        const s = r.scores || {};
        const gaps = (r.missing_keywords || []).slice(0, 3).map(k =>
          typeof k === 'object' ? k.keyword : k
        ).join(', ');
        const contextMsg = `Context: The user's resume scored ${s.final}/100 (${s.grade}). Job: ${r.job_title || 'Unknown'}. Top gaps: ${gaps || 'none'}. Quick win: ${r.quick_win || 'none'}`;
        await apiFetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: contextMsg }),
        });
      }
    } catch {}

    // Load history
    await loadChatHistory();
  }

  async function loadChatHistory() {
    if (!chatMessages) return;
    try {
      const { ok, data } = await apiFetch('/api/chat');
      if (!ok || !Array.isArray(data) || !data.length) {
        // Show empty state
        const hasReport = !!sessionStorage.getItem('lastReport');
        chatMessages.innerHTML = `
          <div class="chat-empty-state">
            <div class="chat-empty-icon"><i data-lucide="message-circle" style="width:48px;height:48px;color:var(--muted)"></i></div>
            Ask me anything about your resume.${hasReport ? ' I have full context from your last analysis.' : ''}
          </div>`;
        return;
      }
      // Clear default greeting bubble, then render history
      chatMessages.innerHTML = '';
      data.forEach(m => appendBubble(m.role === 'assistant' ? 'bot' : 'user', m.content));
      chatMessages.scrollTop = chatMessages.scrollHeight;
    } catch {}
  }

  function appendBubble(role, text) {
    if (!chatMessages) return;
    const div = document.createElement('div');
    div.className = `chat-msg ${role}`;
    div.textContent = text;
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return div;
  }

  async function sendChatMessage() {
    const msg = chatInput?.value.trim();
    if (!msg || !chatMessages) return;
    chatInput.value = '';

    appendBubble('user', msg);

    const loadingEl = document.createElement('div');
    loadingEl.className = 'chat-typing-dots';
    loadingEl.innerHTML = '<span></span><span></span><span></span>';
    chatMessages.appendChild(loadingEl);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    try {
      const { ok, data } = await apiFetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: msg }),
      });
      loadingEl.remove();
      appendBubble('bot', ok ? (data.reply || 'No response.') : (data.error || 'Something went wrong.'));
    } catch {
      loadingEl.remove();
      appendBubble('bot', 'Connection error. Please try again.');
    }
  }

  chatSendBtn?.addEventListener('click', sendChatMessage);
  chatInput?.addEventListener('keydown', e => { if (e.key === 'Enter') sendChatMessage(); });

  clearChatBtn?.addEventListener('click', async () => {
    try {
      await apiFetch('/api/chat', { method: 'DELETE' });
      if (chatMessages) {
        chatMessages.innerHTML = '';
        appendBubble('bot', 'Chat history cleared. How can I help you?');
      }
      chatInitialized = false;
    } catch {}
  });

  // ============================================================
  // LANDING SCORE RING ANIMATION (hero)
  // ============================================================
  const heroRing     = document.getElementById('heroRingProgress');
  const heroScoreNum = document.getElementById('heroScoreNum');
  if (heroRing) {
    const circumference = 2 * Math.PI * 110;
    const target = 90;
    setTimeout(() => {
      heroRing.style.strokeDashoffset = circumference - (target / 100) * circumference;
      let count = 0;
      const counter = setInterval(() => {
        count++;
        if (heroScoreNum) heroScoreNum.textContent = count + '%';
        if (count >= target) clearInterval(counter);
      }, 18);
    }, 500);
  }

});

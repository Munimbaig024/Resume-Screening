/* ============================================
   RESUME CHECKER — Main JavaScript
   ============================================ */

document.addEventListener('DOMContentLoaded', () => {

  // ---- Auth Tabs ----
  const authTabs = document.querySelectorAll('.auth-tab');
  const loginForm = document.getElementById('loginForm');
  const signupForm = document.getElementById('signupForm');
  const authHeader = document.querySelector('.auth-header');

  if (authTabs.length) {
    // Check hash on load
    if (window.location.hash === '#signup') {
      switchAuthTab('signup');
    }

    authTabs.forEach(tab => {
      tab.addEventListener('click', () => switchAuthTab(tab.dataset.tab));
    });

    function switchAuthTab(tabName) {
      authTabs.forEach(t => t.classList.toggle('active', t.dataset.tab === tabName));
      if (tabName === 'login') {
        loginForm.classList.remove('hidden');
        signupForm.classList.add('hidden');
        authHeader.querySelector('h2').textContent = 'Welcome Back';
        authHeader.querySelector('p').textContent = 'Continue optimizing your resume';
      } else {
        loginForm.classList.add('hidden');
        signupForm.classList.remove('hidden');
        authHeader.querySelector('h2').textContent = 'Create Account';
        authHeader.querySelector('p').textContent = 'Start optimizing your resume today';
      }
    }

    // Form submissions
    if (loginForm) {
      loginForm.addEventListener('submit', e => {
        e.preventDefault();
        window.location.href = 'dashboard.html';
      });
    }
    if (signupForm) {
      signupForm.addEventListener('submit', e => {
        e.preventDefault();
        window.location.href = 'onboarding.html';
      });
    }
  }

  // ---- Onboarding Steps ----
  const steps = [document.getElementById('step1'), document.getElementById('step2'), document.getElementById('step3')];
  const stepIndicators = document.querySelectorAll('.onboarding-step-indicator');
  const lines = [document.getElementById('line1'), document.getElementById('line2')];
  let currentStep = 0;

  function goToStep(n) {
    steps.forEach((s, i) => {
      if (s) s.classList.toggle('hidden', i !== n);
    });
    stepIndicators.forEach((ind, i) => {
      ind.classList.remove('active', 'done');
      if (i < n) ind.classList.add('done');
      if (i === n) ind.classList.add('active');
    });
    lines.forEach((l, i) => {
      if (l) l.classList.toggle('done', i < n);
    });
    currentStep = n;

    // Trigger analysis on step 3
    if (n === 2) startAnalysis();
  }

  // Step 1 — Industry selection
  const industryCards = document.querySelectorAll('.industry-card');
  const step1Next = document.getElementById('step1Next');
  industryCards.forEach(card => {
    card.addEventListener('click', () => {
      industryCards.forEach(c => c.classList.remove('selected'));
      card.classList.add('selected');
      if (step1Next) step1Next.disabled = false;
    });
  });
  if (step1Next) {
    step1Next.addEventListener('click', () => goToStep(1));
  }

  // Step 2 — Upload
  const uploadZone = document.getElementById('uploadZone');
  const fileInput = document.getElementById('fileInput');
  const fileInfo = document.getElementById('fileInfo');
  const fileName = document.getElementById('fileName');
  const fileSize = document.getElementById('fileSize');
  const step2Next = document.getElementById('step2Next');
  const step2Back = document.getElementById('step2Back');

  if (uploadZone) {
    uploadZone.addEventListener('click', () => fileInput.click());
    uploadZone.addEventListener('dragover', e => { e.preventDefault(); uploadZone.classList.add('dragover'); });
    uploadZone.addEventListener('dragleave', () => uploadZone.classList.remove('dragover'));
    uploadZone.addEventListener('drop', e => {
      e.preventDefault();
      uploadZone.classList.remove('dragover');
      handleFile(e.dataTransfer.files[0]);
    });
  }
  if (fileInput) {
    fileInput.addEventListener('change', () => handleFile(fileInput.files[0]));
  }

  function handleFile(file) {
    if (!file) return;
    if (fileName) fileName.textContent = file.name;
    if (fileSize) fileSize.textContent = (file.size / 1024).toFixed(0) + ' KB';
    if (fileInfo) fileInfo.classList.remove('hidden');
    if (step2Next) step2Next.disabled = false;
  }

  if (step2Back) step2Back.addEventListener('click', () => goToStep(0));
  if (step2Next) step2Next.addEventListener('click', () => goToStep(2));

  // Step 3 — Analysis Progress
  function startAnalysis() {
    const ring = document.getElementById('analysisProgress');
    const percentEl = document.getElementById('analysisPercent');
    const pSteps = [document.getElementById('pStep1'), document.getElementById('pStep2'), document.getElementById('pStep3'), document.getElementById('pStep4')];
    const finishBtn = document.getElementById('step3Finish');
    const circumference = 2 * Math.PI * 72; // r=72
    let progress = 0;

    const interval = setInterval(() => {
      progress += 1;
      if (percentEl) percentEl.textContent = progress + '%';
      if (ring) ring.style.strokeDashoffset = circumference - (progress / 100) * circumference;

      // Step transitions
      if (progress >= 25) { pSteps[0]?.classList.replace('active', 'done'); pSteps[1]?.classList.add('active'); }
      if (progress >= 50) { pSteps[1]?.classList.replace('active', 'done'); pSteps[2]?.classList.add('active'); }
      if (progress >= 75) { pSteps[2]?.classList.replace('active', 'done'); pSteps[3]?.classList.add('active'); }

      if (progress >= 100) {
        clearInterval(interval);
        pSteps[3]?.classList.replace('active', 'done');
        if (finishBtn) finishBtn.classList.remove('hidden');
      }
    }, 60);
  }

  // ---- Landing Score Ring Animation ----
  const heroRing = document.getElementById('heroRingProgress');
  const heroScoreNum = document.getElementById('heroScoreNum');
  if (heroRing) {
    const circumference = 2 * Math.PI * 110; // r=110
    const target = 90;
    setTimeout(() => {
      heroRing.style.strokeDashoffset = circumference - (target / 100) * circumference;
      // Animate counter
      let count = 0;
      const counter = setInterval(() => {
        count += 1;
        if (heroScoreNum) heroScoreNum.textContent = count + '%';
        if (count >= target) clearInterval(counter);
      }, 18);
    }, 500);
  }

  // ---- Report Gauge Animation ----
  const gaugeFill = document.getElementById('gaugeFill');
  const gaugeNumber = document.getElementById('gaugeNumber');
  if (gaugeFill) {
    const circumference = 2 * Math.PI * 90; // r=90
    const target = 67;
    setTimeout(() => {
      gaugeFill.style.strokeDashoffset = circumference - (target / 100) * circumference;
      let count = 0;
      const counter = setInterval(() => {
        count += 1;
        if (gaugeNumber) gaugeNumber.textContent = count + '%';
        if (count >= target) clearInterval(counter);
      }, 22);
    }, 600);
  }

  // ---- Report Metric Bars Animation ----
  const metricBars = document.querySelectorAll('.metric-bar-fill');
  if (metricBars.length) {
    setTimeout(() => {
      metricBars.forEach(bar => {
        bar.style.width = bar.dataset.width + '%';
      });
    }, 800);
  }

  // ---- Sidebar Toggle ----
  const sidebarToggle = document.getElementById('sidebarToggle');
  const sidebar = document.getElementById('sidebar');
  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener('click', () => sidebar.classList.toggle('open'));
  }

  // ---- AI Chat Popup ----
  const aiFab = document.getElementById('aiFab');
  const aiChatPopup = document.getElementById('aiChatPopup');
  const closeChatBtn = document.getElementById('closeChatBtn');
  const openChatBtn = document.getElementById('openChatBtn');
  const chatInput = document.getElementById('chatInput');
  const chatSendBtn = document.getElementById('chatSendBtn');
  const chatMessages = document.getElementById('chatMessages');

  function toggleChat() {
    if (aiChatPopup) aiChatPopup.classList.toggle('open');
  }

  if (aiFab) aiFab.addEventListener('click', toggleChat);
  if (closeChatBtn) closeChatBtn.addEventListener('click', toggleChat);
  if (openChatBtn) openChatBtn.addEventListener('click', toggleChat);

  function sendChatMessage() {
    const msg = chatInput?.value.trim();
    if (!msg) return;

    // Add user message
    const userBubble = document.createElement('div');
    userBubble.className = 'chat-msg user';
    userBubble.textContent = msg;
    chatMessages?.appendChild(userBubble);
    chatInput.value = '';

    // Scroll down
    chatMessages.scrollTop = chatMessages.scrollHeight;

    // Simulate bot response
    setTimeout(() => {
      const botBubble = document.createElement('div');
      botBubble.className = 'chat-msg bot';
      const responses = [
        "Great question! For your industry, I'd recommend highlighting quantifiable achievements and using action verbs like 'Spearheaded', 'Optimized', and 'Implemented'.",
        "Based on your resume, consider adding more keywords related to your target role. Check the Keyword Analysis section of your report for specifics.",
        "A professional summary at the top can make a big difference. Keep it to 2-3 sentences focusing on your experience level and key strengths.",
        "Try organizing your skills into categories (Programming Languages, Frameworks, Tools) — ATS systems parse this format more reliably.",
        "Remember, each bullet point in your experience should follow the pattern: Action Verb + Task + Quantifiable Result."
      ];
      botBubble.textContent = responses[Math.floor(Math.random() * responses.length)];
      chatMessages?.appendChild(botBubble);
      chatMessages.scrollTop = chatMessages.scrollHeight;
    }, 800);
  }

  if (chatSendBtn) chatSendBtn.addEventListener('click', sendChatMessage);
  if (chatInput) {
    chatInput.addEventListener('keydown', e => {
      if (e.key === 'Enter') sendChatMessage();
    });
  }

});

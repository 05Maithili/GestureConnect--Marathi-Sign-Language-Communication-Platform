/**
 * GestureConnect - Translation Controller
 * Coordinates UI inputs, speech recognition, translation API requests, player updates, and statistics.
 */

document.addEventListener('DOMContentLoaded', () => {
  const textInput = document.getElementById('translation-text-input');
  const languageSelect = document.getElementById('input-language-select');
  const btnTranslate = document.getElementById('btn-translate');
  const btnClear = document.getElementById('btn-clear-text');
  const samplePills = document.querySelectorAll('.gc-sample-pill');
  const charCounter = document.getElementById('char-counter');
  const speedSelect = document.getElementById('player-speed-select');
  const processingBox = document.getElementById('processing-state-box');

  // Speech elements
  const btnSpeechTranslate = document.getElementById('btn-speech-translate');
  const btnSpeechRerecord = document.getElementById('btn-speech-rerecord');
  const speechTranscriptBox = document.getElementById('speech-transcript-box');
  const speechTranscriptText = document.getElementById('speech-transcript-text');
  const speechDetectedLang = document.getElementById('speech-detected-lang');
  const micPulseRing = document.getElementById('mic-pulse-ring');
  const waveformVisualizer = document.getElementById('waveform-visualizer');

  // Stats elements
  const statInVocab = document.getElementById('stat-in-vocab');
  const statFingerspelled = document.getElementById('stat-fingerspelled');
  const statTotalSigns = document.getElementById('stat-total-signs');
  const statLatency = document.getElementById('stat-latency');
  const mappingTraceBox = document.getElementById('mapping-trace-box');
  const mappingTraceText = document.getElementById('mapping-trace-text');

  // Initialize Player
  const player = new SignPlayer('sign-video-player', {
    signBadgeId: 'current-sign-badge',
    counterBadgeId: 'sign-counter-badge',
    btnPlayId: 'btn-player-play',
    btnPrevId: 'btn-player-prev',
    btnNextId: 'btn-player-next',
    btnReplayId: 'btn-player-replay',
    chipsContainerId: 'tokens-analysis-container'
  });

  // Mode Selection Logic
  const modePhase1 = document.getElementById('mode-phase1');
  const modePhase2 = document.getElementById('mode-phase2');
  const phase2EmptyState = document.getElementById('phase2-empty-state');
  const signVideoPlayer = document.getElementById('sign-video-player');
  const playerOverlay = document.querySelector('.gc-player-overlay');
  
  function updatePhaseMode() {
    if (modePhase2 && modePhase2.checked) {
      if (signVideoPlayer) signVideoPlayer.style.display = 'none';
      if (playerOverlay) playerOverlay.style.display = 'none';
      if (phase2EmptyState) phase2EmptyState.classList.remove('d-none');
      // Stop playback if switching
      if (player) player.togglePlay();
    } else {
      if (signVideoPlayer) signVideoPlayer.style.display = 'block';
      if (playerOverlay) playerOverlay.style.display = 'block';
      if (phase2EmptyState) phase2EmptyState.classList.add('d-none');
    }
  }

  if (modePhase1) modePhase1.addEventListener('change', updatePhaseMode);
  if (modePhase2) modePhase2.addEventListener('change', updatePhaseMode);
  updatePhaseMode();

  // Speed selector
  if (speedSelect) {
    speedSelect.addEventListener('change', (e) => {
      player.setSpeed(e.target.value);
    });
  }

  // Character counter
  if (textInput && charCounter) {
    textInput.addEventListener('input', () => {
      charCounter.textContent = `${textInput.value.length} / 500 characters`;
    });
  }

  // Initialize Speech Input
  const speechManager = new SpeechInputManager({
    micBtnId: 'btn-speech-mic',
    statusId: 'speech-status-text',
    transcriptId: 'translation-text-input',
    languageSelectId: 'input-language-select',
    onTranscriptReady: (transcript, detectedLang) => {
      // Auto-determine language if not provided
      if (!detectedLang) {
        const devanagari = (transcript.match(/[\u0900-\u097F]/g) || []).length;
        const latin = (transcript.match(/[a-zA-Z]/g) || []).length;
        detectedLang = (latin >= devanagari && latin > 0) ? 'en' : 'mr';
      }

      if (speechTranscriptBox && speechTranscriptText) {
        speechTranscriptBox.classList.remove('d-none');
        speechTranscriptText.textContent = transcript;
      }
      if (speechDetectedLang) {
        speechDetectedLang.textContent = (detectedLang === 'en') ? 'English (en)' : 'Marathi (मराठी)';
        speechDetectedLang.className = `badge ${detectedLang === 'en' ? 'bg-info-subtle text-info-emphasis' : 'bg-primary-subtle text-primary'}`;
      }
      if (languageSelect) {
        languageSelect.value = detectedLang;
      }
      if (textInput) {
        textInput.value = transcript;
        if (charCounter) charCounter.textContent = `${transcript.length} / 500 characters`;
      }
      executeTranslation(transcript, 'speech', detectedLang);
    }
  });

  // Wire Speech action buttons
  if (btnSpeechTranslate) {
    btnSpeechTranslate.addEventListener('click', () => {
      const text = (speechTranscriptText && speechTranscriptText.textContent) 
        ? speechTranscriptText.textContent.trim() 
        : (textInput ? textInput.value.trim() : '');
      if (!text) {
        showNotification('Please speak your sentence first.', 'info');
        return;
      }
      executeTranslation(text, 'speech');
    });
  }


  if (btnSpeechRerecord) {
    btnSpeechRerecord.addEventListener('click', () => {
      if (speechTranscriptBox) speechTranscriptBox.classList.add('d-none');
      const micBtn = document.getElementById('btn-speech-mic');
      if (micBtn) micBtn.click();
    });
  }

  // Sample phrases clicks
  samplePills.forEach(pill => {
    pill.addEventListener('click', (e) => {
      e.preventDefault();
      const lang = pill.dataset.lang || 'mr';
      const text = pill.dataset.text || '';
      
      if (languageSelect) languageSelect.value = lang;
      if (textInput) {
        textInput.value = text;
        if (charCounter) charCounter.textContent = `${text.length} / 500 characters`;
      }
      // Switch to text tab if needed
      const textTabBtn = document.getElementById('text-tab');
      if (textTabBtn) textTabBtn.click();

      executeTranslation(text, 'text');
    });
  });

  // Clear button
  if (btnClear) {
    btnClear.addEventListener('click', () => {
      if (textInput) {
        textInput.value = '';
        if (charCounter) charCounter.textContent = '0 / 500 characters';
        textInput.focus();
      }
    });
  }

  // Translate button
  if (btnTranslate) {
    btnTranslate.addEventListener('click', () => {
      const text = textInput ? textInput.value.trim() : '';
      if (!text) {
        showNotification('Please enter or speak text to translate.', 'info');
        return;
      }
      
      // Unlock the video player on user interaction
      if (player && player.video) {
        player.video.muted = true;
        // Start a dummy play/pause to unlock autoplay for this document
        const unlockPromise = player.video.play();
        if (unlockPromise !== undefined) {
          unlockPromise.then(() => {
            player.video.pause();
          }).catch(err => {
            console.warn('[Phase1] unlock failed:', err);
          });
        }
      }

      executeTranslation(text, 'text');
    });
  }

  // Allow Ctrl+Enter to trigger translation
  if (textInput) {
    textInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        btnTranslate.click();
      }
    });
  }

  function executeTranslation(text, inputMode = 'text', langOverride = null) {
    if (!text || !text.trim()) return;

    let selectedLang = langOverride || (languageSelect ? languageSelect.value : 'auto');

    // Intelligent script-level language detection if auto
    if (selectedLang === 'auto') {
      const devanagari = (text.match(/[\u0900-\u097F]/g) || []).length;
      const latin = (text.match(/[a-zA-Z]/g) || []).length;
      selectedLang = (latin >= devanagari && latin > 0) ? 'en' : 'mr';
    }

    // Show loading state & processing steps
    if (btnTranslate) {
      btnTranslate.disabled = true;
      btnTranslate.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status"></span>Translating...';
    }

    if (processingBox) {
      processingBox.classList.remove('d-none');
    }

    fetch('/api/translate/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
        // 'X-CSRFToken': CSRF_TOKEN // Not needed if we use simple view, or we fetch it dynamically. Assuming it's injected if needed or API allows.
      },
      body: JSON.stringify({
        text: text,
        language: selectedLang,
        mode: (modePhase2 && modePhase2.checked) ? 'phase2' : 'phase1'
      })
    })
    .then(res => res.json())
    .then(data => {
      console.log('[Phase1] API response:', data);
      if (data.success) {
        console.log('[Phase1] video_sequence:', data.video_sequence);
        // Load into player
        player.loadSequence(data.tokens, data.video_sequence);

        // Update statistics and badges
        const statDetectedLang = document.getElementById('stat-detected-lang');
        if (statDetectedLang) {
          const langMap = {'en': 'English', 'mr': 'Marathi (मराठी)'};
          statDetectedLang.textContent = langMap[data.detected_language] || data.detected_language;
        }

        if (statInVocab) statInVocab.textContent = (data.available_signs || []).length;
        
        const statUnknown = document.getElementById('stat-unknown');
        if (statUnknown) statUnknown.textContent = (data.unknown_words || []).length;

        // Update word analysis summary text
        const wordAnalysisSummary = document.getElementById('word-analysis-summary');
        if (wordAnalysisSummary) {
           wordAnalysisSummary.textContent = `${(data.available_signs || []).length} signs available • ${(data.unknown_words || []).length} words unavailable`;
        }

        // English mapping trace or fallback (remove old mapping logic to match new API)
        if (mappingTraceBox) mappingTraceBox.classList.add('d-none');

        // Notification if OOV words
        if (data.unknown_words && data.unknown_words.length > 0) {
          showNotification(`Unavailable words: "${data.unknown_words.join(', ')}".`, 'warning');
        }
      } else if (data.status === 'error' && data.errors) {
        let errorMsg = Object.values(data.errors).flat().join(' ');
        showNotification(errorMsg || 'Validation failed. Please try again.', 'error');
      } else {
        showNotification(data.error || 'Translation failed. Please try again.', 'error');
      }
    })
    .catch(err => {
      console.error('Translation API error:', err);
      showNotification('Network or server error during translation.', 'error');
    })
    .finally(() => {
      if (btnTranslate) {
        btnTranslate.disabled = false;
        btnTranslate.innerHTML = '<i class="bi bi-arrow-repeat me-1"></i> Translate to ISL';
      }
      setTimeout(() => {
        if (processingBox) processingBox.classList.add('d-none');
      }, 1500);
    });
  }

  // Check URL query param ?q=... (e.g. from Dashboard or History Replay)
  const urlParams = new URLSearchParams(window.location.search);
  const initialQuery = urlParams.get('q');
  if (initialQuery && initialQuery.trim()) {
    if (textInput) {
      textInput.value = initialQuery.trim();
      if (charCounter) charCounter.textContent = `${initialQuery.length} / 500 characters`;
    }
    executeTranslation(initialQuery.trim(), 'text');
  }
});

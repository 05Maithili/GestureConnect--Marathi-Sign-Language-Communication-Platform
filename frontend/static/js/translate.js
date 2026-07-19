/**
 * GestureConnect - Translation Controller
 * Coordinates UI inputs, translation API requests, player updates, and statistics.
 */

document.addEventListener('DOMContentLoaded', () => {
  const textInput = document.getElementById('translation-text-input');
  const languageSelect = document.getElementById('input-language-select');
  const btnTranslate = document.getElementById('btn-translate');
  const btnClear = document.getElementById('btn-clear-text');
  const samplePills = document.querySelectorAll('.gc-sample-pill');

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
    chipsContainerId: 'sign-chips-container'
  });

  // Initialize Speech Input
  const speechManager = new SpeechInputManager({
    micBtnId: 'btn-speech-mic',
    statusId: 'speech-status-text',
    transcriptId: 'translation-text-input',
    languageSelectId: 'input-language-select',
    onTranscriptReady: (transcript) => {
      executeTranslation(transcript, 'speech');
    }
  });

  // Sample phrases clicks
  samplePills.forEach(pill => {
    pill.addEventListener('click', (e) => {
      e.preventDefault();
      const lang = pill.dataset.lang || 'mr';
      const text = pill.dataset.text || '';
      
      if (languageSelect) languageSelect.value = lang;
      if (textInput) textInput.value = text;
      executeTranslation(text, 'text');
    });
  });

  // Clear button
  if (btnClear) {
    btnClear.addEventListener('click', () => {
      if (textInput) textInput.value = '';
      textInput.focus();
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

  function executeTranslation(text, inputMode = 'text') {
    if (!text || !text.trim()) return;

    const selectedLang = languageSelect ? languageSelect.value : 'auto';

    // Show loading state
    if (btnTranslate) {
      btnTranslate.disabled = true;
      btnTranslate.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status"></span>Translating...';
    }

    fetch('/api/translate/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': CSRF_TOKEN
      },
      body: JSON.stringify({
        text: text,
        language: selectedLang,
        input_mode: inputMode
      })
    })
    .then(res => res.json())
    .then(data => {
      if (data.status === 'success') {
        // Load into player
        player.loadSequence(data.sign_sequence);

        // Update statistics
        const stats = data.stats || {};
        if (statInVocab) statInVocab.textContent = stats.in_vocabulary_signs || 0;
        if (statFingerspelled) statFingerspelled.textContent = stats.fingerspelled_words || 0;
        if (statTotalSigns) statTotalSigns.textContent = (data.sign_sequence || []).length;
        if (statLatency) statLatency.textContent = `${data.processing_time_ms || 0} ms`;

        // English mapping trace
        if (data.english_mapping_trace && data.english_mapping_trace.length > 0) {
          if (mappingTraceBox) mappingTraceBox.classList.remove('d-none');
          if (mappingTraceText) {
            const traceStr = data.english_mapping_trace
              .map(t => `${t.english} → ${t.marathi} (${t.type})`)
              .join(' | ');
            mappingTraceText.textContent = `English Lexical Mapping: ${traceStr} (Normalized: "${data.normalized_text}")`;
          }
        } else {
          if (mappingTraceBox) mappingTraceBox.classList.add('d-none');
        }

        // Notification if fingerspelling fallback occurred
        if (data.fallback_words && data.fallback_words.length > 0) {
          showNotification(`Out-of-vocabulary word(s) detected: "${data.fallback_words.join(', ')}". Alphabet fingerspelling applied.`, 'info');
        }
      } else {
        showNotification(data.message || 'Translation failed. Please try again.', 'error');
      }
    })
    .catch(err => {
      console.error('Translation API error:', err);
      showNotification('Network or server error during translation.', 'error');
    })
    .finally(() => {
      if (btnTranslate) {
        btnTranslate.disabled = false;
        btnTranslate.innerHTML = '<i class="bi bi-arrow-repeat me-1"></i> Translate';
      }
    });
  }
});

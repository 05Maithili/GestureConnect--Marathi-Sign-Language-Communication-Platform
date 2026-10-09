/**
 * GestureConnect - Speech Recognition Controller
 * Handles Bilingual English (en-IN) and Marathi (mr-IN) voice input.
 * Supports Web Speech API with fallback to audio recording and server-side recognition.
 */

class SpeechInputManager {
  constructor(options = {}) {
    this.btnMic = document.getElementById(options.micBtnId || 'btn-speech-mic');
    this.statusEl = document.getElementById(options.statusId || 'speech-status-text');
    this.promptHeading = document.getElementById('speech-prompt-heading');
    this.transcriptEl = document.getElementById(options.transcriptId || 'translation-text-input');
    this.languageSelector = document.getElementById(options.languageSelectId || 'input-language-select');
    this.pulseRing = document.getElementById('mic-pulse-ring');
    this.waveform = document.getElementById('waveform-visualizer');
    this.onTranscriptReady = options.onTranscriptReady || null;

    this.currentLang = 'en'; // default to English or sync with selector
    this.isRecording = false;
    this.recognition = null;
    this.mediaRecorder = null;
    this.audioChunks = [];

    this.initLanguageControls();
    this.initRecognition();
    this.initEvents();
  }

  initLanguageControls() {
    // Check speech radio buttons (English vs Marathi)
    const voiceLangRadios = document.querySelectorAll('input[name="speechVoiceLang"]');
    if (voiceLangRadios.length > 0) {
      voiceLangRadios.forEach(radio => {
        if (radio.checked) {
          this.currentLang = radio.value;
        }
        radio.addEventListener('change', (e) => {
          if (e.target.checked) {
            this.setVoiceLanguage(e.target.value);
          }
        });
      });
    }

    // Sync from main dropdown if changed
    if (this.languageSelector) {
      this.languageSelector.addEventListener('change', (e) => {
        if (e.target.value === 'en' || e.target.value === 'mr') {
          this.setVoiceLanguage(e.target.value);
        }
      });
    }
  }

  setVoiceLanguage(lang) {
    this.currentLang = (lang === 'mr') ? 'mr' : 'en';

    // Sync radio buttons
    const targetRadio = document.getElementById(`voice-lang-${this.currentLang}`);
    if (targetRadio) targetRadio.checked = true;

    // Sync main language selector
    if (this.languageSelector && (this.languageSelector.value === 'en' || this.languageSelector.value === 'mr')) {
      this.languageSelector.value = this.currentLang;
    }

    // Update status prompt
    if (this.statusEl && !this.isRecording) {
      if (this.currentLang === 'en') {
        this.statusEl.textContent = 'Tap the microphone and speak in English (e.g. "Car expensive", "House quiet").';
      } else {
        this.statusEl.textContent = 'मायक्रोफोनवर टॅप करा आणि मराठीत बोला (उदा. "कार महाग", "घर शांत").';
      }
    }
  }

  getBcp47Code() {
    return (this.currentLang === 'mr') ? 'mr-IN' : 'en-IN';
  }

  detectScript(text) {
    if (!text) return this.currentLang;
    const devanagariMatches = text.match(/[\u0900-\u097F]/g) || [];
    const latinMatches = text.match(/[a-zA-Z]/g) || [];

    if (latinMatches.length > devanagariMatches.length) return 'en';
    if (devanagariMatches.length > 0) return 'mr';
    return this.currentLang;
  }

  initRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      this.recognition = new SpeechRecognition();
      this.recognition.continuous = false;
      this.recognition.interimResults = true;

      this.recognition.onstart = () => {
        this.setRecordingState(true);
        if (this.currentLang === 'en') {
          this.updateStatus('Listening... Speak clearly in English now.');
        } else {
          this.updateStatus('ऐकत आहे... आता स्पष्ट मराठीत बोला.');
        }
      };

      this.recognition.onresult = (event) => {
        let interimTranscript = '';
        let finalTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; ++i) {
          if (event.results[i].isFinal) {
            finalTranscript += event.results[i][0].transcript;
          } else {
            interimTranscript += event.results[i][0].transcript;
          }
        }

        const currentText = (finalTranscript || interimTranscript).trim();
        if (this.transcriptEl) {
          this.transcriptEl.value = currentText;
        }

        if (finalTranscript && finalTranscript.trim()) {
          const detectedLang = this.detectScript(finalTranscript);
          if (this.onTranscriptReady) {
            this.onTranscriptReady(finalTranscript.trim(), detectedLang);
          }
        }
      };

      this.recognition.onerror = (event) => {
        console.warn('Speech recognition error:', event.error);
        this.setRecordingState(false);
        this.updateStatus(`Microphone status: ${event.error}. Click mic to retry or type text.`);
      };

      this.recognition.onend = () => {
        this.setRecordingState(false);
      };
    } else {
      console.info('Web Speech API not natively available in browser. Will use Audio Recorder fallback.');
    }
  }

  initEvents() {
    if (this.btnMic) {
      this.btnMic.addEventListener('click', (e) => {
        e.preventDefault();
        this.toggleListening();
      });
    }
  }

  toggleListening() {
    if (this.isRecording) {
      this.stop();
    } else {
      this.start();
    }
  }

  start() {
    const langCode = this.getBcp47Code();

    if (this.recognition) {
      this.recognition.lang = langCode;
      try {
        this.recognition.start();
      } catch (err) {
        console.warn('Recognition start exception:', err);
      }
    } else {
      // Fallback to MediaRecorder API
      this.startMediaRecorder(langCode);
    }
  }

  stop() {
    if (this.recognition) {
      try {
        this.recognition.stop();
      } catch (err) {}
    }
    if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
      this.mediaRecorder.stop();
    }
    this.setRecordingState(false);
  }

  startMediaRecorder(langCode) {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      showNotification('Audio recording not supported in this browser.', 'error');
      return;
    }

    navigator.mediaDevices.getUserMedia({ audio: true })
      .then(stream => {
        this.mediaRecorder = new MediaRecorder(stream);
        this.audioChunks = [];
        this.setRecordingState(true);
        this.updateStatus(`Recording audio (${langCode})...`);

        this.mediaRecorder.ondataavailable = e => {
          if (e.data.size > 0) this.audioChunks.push(e.data);
        };

        this.mediaRecorder.onstop = () => {
          const audioBlob = new Blob(this.audioChunks, { type: 'audio/wav' });
          this.sendAudioToServer(audioBlob, langCode);
          stream.getTracks().forEach(track => track.stop());
        };

        this.mediaRecorder.start();
      })
      .catch(err => {
        console.error('Microphone access denied:', err);
        showNotification('Microphone permission denied.', 'error');
        this.setRecordingState(false);
      });
  }

  sendAudioToServer(audioBlob, langCode) {
    this.updateStatus('Transcribing speech on server...');
    const formData = new FormData();
    formData.append('audio', audioBlob, 'speech_input.wav');
    formData.append('language', langCode.startsWith('en') ? 'en' : 'mr');

    fetch('/api/speech-to-text/', {
      method: 'POST',
      headers: {
        'X-CSRFToken': CSRF_TOKEN
      },
      body: formData
    })
    .then(res => res.json())
    .then(data => {
      if (data.status === 'success' && data.transcript) {
        if (this.transcriptEl) {
          this.transcriptEl.value = data.transcript;
        }
        const detectedLang = data.language || this.detectScript(data.transcript);
        if (this.onTranscriptReady) {
          this.onTranscriptReady(data.transcript, detectedLang);
        }
      } else {
        showNotification(data.message || 'Speech recognition failed.', 'error');
        this.updateStatus('Could not transcribe audio. Please try again.');
      }
    })
    .catch(err => {
      console.error('STT API error:', err);
      showNotification('Server speech recognition error.', 'error');
      this.updateStatus('Recognition error. Please try again.');
    })
    .finally(() => {
      this.setRecordingState(false);
    });
  }

  setRecordingState(recording) {
    this.isRecording = recording;
    if (this.btnMic) {
      if (recording) {
        this.btnMic.classList.add('recording');
        this.btnMic.innerHTML = '<i class="bi bi-stop-fill"></i>';
        this.btnMic.style.background = 'linear-gradient(135deg, #ef4444, #dc2626)';
        this.btnMic.setAttribute('title', 'Stop Recording');
      } else {
        this.btnMic.classList.remove('recording');
        this.btnMic.innerHTML = '<i class="bi bi-mic"></i>';
        this.btnMic.style.background = 'linear-gradient(135deg, #8b5cf6, #6d28d9)';
        this.btnMic.setAttribute('title', 'Click to Speak');
      }
    }

    if (this.pulseRing) {
      if (recording) this.pulseRing.classList.remove('d-none');
      else this.pulseRing.classList.add('d-none');
    }

    if (this.waveform) {
      if (recording) {
        this.waveform.classList.remove('d-none');
        this.waveform.classList.add('d-flex');
      } else {
        this.waveform.classList.add('d-none');
        this.waveform.classList.remove('d-flex');
      }
    }
  }

  updateStatus(msg) {
    if (this.statusEl) {
      this.statusEl.textContent = msg;
    }
  }
}

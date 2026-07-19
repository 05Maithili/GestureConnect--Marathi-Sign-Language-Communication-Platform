/**
 * GestureConnect - Speech Recognition Controller
 * Handles Marathi (mr-IN) and English (en-IN) voice input.
 * Supports Web Speech API with fallback to audio recording and server-side recognition.
 */

class SpeechInputManager {
  constructor(options = {}) {
    this.btnMic = document.getElementById(options.micBtnId || 'btn-speech-mic');
    this.statusEl = document.getElementById(options.statusId || 'speech-status-text');
    this.transcriptEl = document.getElementById(options.transcriptId || 'speech-transcript-preview');
    this.languageSelector = document.getElementById(options.languageSelectId || 'input-language-select');
    this.onTranscriptReady = options.onTranscriptReady || null;

    this.isRecording = false;
    this.recognition = null;
    this.mediaRecorder = null;
    this.audioChunks = [];

    this.initRecognition();
    this.initEvents();
  }

  initRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      this.recognition = new SpeechRecognition();
      this.recognition.continuous = false;
      this.recognition.interimResults = true;

      this.recognition.onstart = () => {
        this.setRecordingState(true);
        this.updateStatus('Listening... Speak now in Marathi or English.');
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

        const currentText = finalTranscript || interimTranscript;
        if (this.transcriptEl) {
          this.transcriptEl.value = currentText;
        }

        if (finalTranscript && this.onTranscriptReady) {
          this.onTranscriptReady(finalTranscript.trim());
        }
      };

      this.recognition.onerror = (event) => {
        console.warn('Speech recognition error:', event.error);
        this.setRecordingState(false);
        this.updateStatus(`Microphone status: ${event.error}. Try typing or retry.`);
      };

      this.recognition.onend = () => {
        this.setRecordingState(false);
        this.updateStatus('Speech recognition finished.');
      };
    } else {
      console.info('Web Speech API not natively available in browser. Will use Audio Recorder fallback.');
    }
  }

  initEvents() {
    if (this.btnMic) {
      this.btnMic.addEventListener('click', () => this.toggleListening());
    }
  }

  getSelectedLanguageCode() {
    const lang = this.languageSelector ? this.languageSelector.value : 'mr';
    return lang === 'en' ? 'en-IN' : 'mr-IN';
  }

  toggleListening() {
    if (this.isRecording) {
      this.stop();
    } else {
      this.start();
    }
  }

  start() {
    const langCode = this.getSelectedLanguageCode();

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
        this.updateStatus('Recording audio for server speech recognition...');

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
        if (this.transcriptEl) this.transcriptEl.value = data.transcript;
        if (this.onTranscriptReady) this.onTranscriptReady(data.transcript);
        this.updateStatus('Transcription complete.');
      } else {
        this.updateStatus(data.message || 'Speech could not be recognized.');
      }
    })
    .catch(err => {
      console.error('Server STT failed:', err);
      this.updateStatus('Speech-to-text server error. Please type your message.');
    });
  }

  setRecordingState(isRecording) {
    this.isRecording = isRecording;
    if (this.btnMic) {
      if (isRecording) {
        this.btnMic.classList.add('recording');
        this.btnMic.innerHTML = '<i class="bi bi-mic-fill"></i>';
      } else {
        this.btnMic.classList.remove('recording');
        this.btnMic.innerHTML = '<i class="bi bi-mic"></i>';
      }
    }
  }

  updateStatus(msg) {
    if (this.statusEl) {
      this.statusEl.textContent = msg;
    }
  }
}

/**
 * GestureConnect - Sequential Sign Video Player Manager
 * Coordinates smooth playback of individual sign MP4 clips composing sentence-level sign language output.
 */

class SignPlayer {
  constructor(videoElementId, options = {}) {
    this.video = document.getElementById(videoElementId);
    this.currentSignBadge = document.getElementById(options.signBadgeId || 'current-sign-badge');
    this.counterBadge = document.getElementById(options.counterBadgeId || 'sign-counter-badge');
    this.btnPlay = document.getElementById(options.btnPlayId || 'btn-player-play');
    this.btnPrev = document.getElementById(options.btnPrevId || 'btn-player-prev');
    this.btnNext = document.getElementById(options.btnNextId || 'btn-player-next');
    this.btnReplay = document.getElementById(options.btnReplayId || 'btn-player-replay');
    this.chipsContainer = document.getElementById(options.chipsContainerId || 'sign-chips-container');
    this.placeholderCanvas = document.getElementById(options.placeholderCanvasId || 'player-placeholder-canvas');

    this.sequence = [];
    this.currentIndex = -1;
    this.isPlaying = false;
    this.playbackSpeed = 1.0;

    this.initEvents();
  }

  initEvents() {
    if (!this.video) return;

    // When current sign video clip finishes, play next in sequence
    this.video.addEventListener('ended', () => {
      if (this.currentIndex < this.sequence.length - 1) {
        this.next();
      } else {
        this.isPlaying = false;
        this.updatePlayButton();
        this.highlightChip(this.currentIndex);
      }
    });

    this.video.addEventListener('error', (e) => {
      console.warn('Video asset load error, showing canvas fallback:', e);
      this.handleVideoError();
    });

    if (this.btnPlay) {
      this.btnPlay.addEventListener('click', () => this.togglePlay());
    }
    if (this.btnPrev) {
      this.btnPrev.addEventListener('click', () => this.previous());
    }
    if (this.btnNext) {
      this.btnNext.addEventListener('click', () => this.next());
    }
    if (this.btnReplay) {
      this.btnReplay.addEventListener('click', () => this.replay());
    }
  }

  loadSequence(signSequence) {
    this.sequence = signSequence || [];
    this.currentIndex = -1;
    this.isPlaying = false;

    this.renderChips();

    if (this.sequence.length > 0) {
      this.setIndex(0, true);
    } else {
      this.resetPlayerState();
    }
  }

  renderChips() {
    if (!this.chipsContainer) return;
    this.chipsContainer.innerHTML = '';

    if (this.sequence.length === 0) {
      this.chipsContainer.innerHTML = '<span class="text-muted small fst-italic">No signs translated yet.</span>';
      return;
    }

    this.sequence.forEach((sign, idx) => {
      const chip = document.createElement('button');
      const isFallback = sign.is_fallback;
      chip.className = `gc-sign-chip ${isFallback ? 'fallback' : ''}`;
      chip.id = `chip-sign-${idx}`;
      
      const term = sign.marathi_term || sign.char || sign.english_gloss || sign.sign_id;
      const typeLabel = isFallback ? '🔤 ' : '';
      chip.innerHTML = `${typeLabel}<span>${term}</span>`;
      chip.title = `${sign.sign_id} (${sign.english_gloss || ''})`;

      chip.addEventListener('click', () => {
        this.setIndex(idx, true);
      });

      this.chipsContainer.appendChild(chip);
    });
  }

  highlightChip(index) {
    if (!this.chipsContainer) return;
    const allChips = this.chipsContainer.querySelectorAll('.gc-sign-chip');
    allChips.forEach((c, idx) => {
      if (idx === index) {
        c.classList.add('active');
        c.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
      } else {
        c.classList.remove('active');
      }
    });
  }

  setIndex(index, autoPlay = true) {
    if (index < 0 || index >= this.sequence.length) return;

    this.currentIndex = index;
    const sign = this.sequence[this.currentIndex];

    // Update Indicators
    if (this.currentSignBadge) {
      const term = sign.marathi_term || sign.char || sign.english_gloss;
      const gloss = sign.english_gloss ? ` • ${sign.english_gloss}` : '';
      const fallbackBadge = sign.is_fallback ? ' [Fingerspelling]' : '';
      this.currentSignBadge.textContent = `${term}${gloss}${fallbackBadge}`;
    }

    if (this.counterBadge) {
      this.counterBadge.textContent = `Sign ${this.currentIndex + 1} of ${this.sequence.length}`;
    }

    this.highlightChip(this.currentIndex);
    this.updateNavButtons();

    // Load and play video clip
    if (this.video && sign.animation_url) {
      this.video.src = sign.animation_url;
      this.video.playbackRate = this.playbackSpeed;
      this.video.load();

      if (autoPlay) {
        const playPromise = this.video.play();
        if (playPromise !== undefined) {
          playPromise
            .then(() => {
              this.isPlaying = true;
              this.updatePlayButton();
            })
            .catch(err => {
              console.warn('Autoplay prevented or video not yet loaded:', err);
              this.isPlaying = false;
              this.updatePlayButton();
            });
        }
      } else {
        this.isPlaying = false;
        this.updatePlayButton();
      }
    }
  }

  next() {
    if (this.currentIndex < this.sequence.length - 1) {
      this.setIndex(this.currentIndex + 1, true);
    }
  }

  previous() {
    if (this.currentIndex > 0) {
      this.setIndex(this.currentIndex - 1, true);
    }
  }

  togglePlay() {
    if (!this.video || this.sequence.length === 0) return;

    if (this.video.paused) {
      this.video.play();
      this.isPlaying = true;
    } else {
      this.video.pause();
      this.isPlaying = false;
    }
    this.updatePlayButton();
  }

  replay() {
    if (this.sequence.length > 0) {
      this.setIndex(0, true);
    }
  }

  updatePlayButton() {
    if (!this.btnPlay) return;
    if (this.isPlaying) {
      this.btnPlay.innerHTML = '<i class="bi bi-pause-fill"></i> Pause';
    } else {
      this.btnPlay.innerHTML = '<i class="bi bi-play-fill"></i> Play';
    }
  }

  updateNavButtons() {
    if (this.btnPrev) {
      this.btnPrev.disabled = this.currentIndex <= 0;
    }
    if (this.btnNext) {
      this.btnNext.disabled = this.currentIndex >= this.sequence.length - 1;
    }
  }

  resetPlayerState() {
    if (this.currentSignBadge) this.currentSignBadge.textContent = 'Waiting for input...';
    if (this.counterBadge) this.counterBadge.textContent = '0 of 0';
    if (this.video) {
      this.video.removeAttribute('src');
      this.video.load();
    }
    this.updateNavButtons();
    this.updatePlayButton();
  }

  handleVideoError() {
    // If an asset is missing, move smoothly to next sign after short pause
    setTimeout(() => {
      if (this.currentIndex < this.sequence.length - 1) {
        this.next();
      }
    }, 1200);
  }
}

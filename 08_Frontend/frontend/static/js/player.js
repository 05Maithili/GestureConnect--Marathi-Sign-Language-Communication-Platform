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
    this.isTransitioning = false;

    this.initEvents();
  }

  initEvents() {
    if (!this.video) return;

    // When current sign video clip finishes, play next in sequence
    this.video.addEventListener('ended', () => {
      this.handleVideoEnded();
    });
    
    // Fallback for some browsers where `ended` doesn't fire correctly on partial content
    this.video.addEventListener('timeupdate', () => {
      if (this.video.duration && this.video.currentTime >= this.video.duration - 0.1) {
        if (!this.video.ended) {
            this.handleVideoEnded();
        }
      }
    });

    this.video.addEventListener('error', (e) => {
      console.warn('Video asset load error, skipping to next:', e);
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
  
  handleVideoEnded() {
    if (this.isTransitioning) return;
    this.isTransitioning = true;
    
    console.log(`[Phase1] Video ended. Current Index: ${this.currentIndex}, Total: ${this.sequence.length}`);
    
    if (this.currentIndex < this.sequence.length - 1) {
      // Add a tiny delay to ensure smooth transition
      setTimeout(() => {
        this.next();
        this.isTransitioning = false;
      }, 150);
    } else {
      console.log('[Phase1] playback complete');
      this.isPlaying = false;
      this.updatePlayButton();
      this.highlightChip(this.currentIndex);
      this.isTransitioning = false;
    }
  }

  loadSequence(tokens, videoSequence) {
    console.log('[Phase1] loadSequence called', { tokens, videoSequence });
    this.tokens = tokens || [];
    this.sequence = videoSequence || [];
    this.currentIndex = -1;
    this.isPlaying = false;
    this.isTransitioning = false;

    const emptyState = document.getElementById('avatar-empty-state');
    if (emptyState) {
      emptyState.style.display = (this.sequence.length > 0) ? 'none' : 'block';
    }
    
    if (this.video && this.sequence.length > 0) {
       this.video.style.display = 'block';
    }

    this.renderChips();

    if (this.sequence.length > 0) {
      this.setIndex(0, true);
    } else {
      this.resetPlayerState();
    }
  }

  setSpeed(rate) {
    this.playbackSpeed = parseFloat(rate) || 1.0;
    if (this.video) {
      this.video.playbackRate = this.playbackSpeed;
    }
  }

  renderChips() {
    if (!this.chipsContainer) return;
    this.chipsContainer.innerHTML = '';

    if (this.tokens.length === 0) {
      this.chipsContainer.innerHTML = '<span class="text-muted small fst-italic">Translate a sentence to see word availability.</span>';
      return;
    }

    this.tokens.forEach((token, idx) => {
      const chip = document.createElement('button');
      const isAvailable = token.status === 'available';
      
      chip.className = `gc-sign-chip ${isAvailable ? 'available btn-outline-success' : 'unavailable btn-outline-secondary opacity-50'} m-1 px-3 py-1 rounded-pill border fw-semibold`;
      chip.id = `chip-token-${idx}`;
      
      chip.innerHTML = `<span>${token.word}</span>`;
      if (token.sign_id) chip.title = token.sign_id;

      if (isAvailable) {
        chip.addEventListener('click', () => {
          let videoIdx = 0;
          for (let i = 0; i < idx; i++) {
            if (this.tokens[i].status === 'available') videoIdx++;
          }
          this.setIndex(videoIdx, true);
        });
      }

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
    console.log(`[Phase1] next video: index ${index}`);
    if (index < 0 || index >= this.sequence.length) {
      console.log('[Phase1] index out of bounds, playback complete');
      return;
    }

    this.currentIndex = index;
    const videoUrl = this.sequence[this.currentIndex];
    console.log('[Phase1] current video:', videoUrl);

    // Find the corresponding token
    let tokenIndex = -1;
    let availableCount = -1;
    for (let i = 0; i < this.tokens.length; i++) {
      if (this.tokens[i].status === 'available') {
        availableCount++;
        if (availableCount === this.currentIndex) {
          tokenIndex = i;
          break;
        }
      }
    }

    // Update Indicators
    if (this.currentSignBadge && tokenIndex !== -1) {
      const token = this.tokens[tokenIndex];
      this.currentSignBadge.textContent = `${token.word} (${token.sign_id})`;
    }

    if (this.counterBadge) {
      this.counterBadge.textContent = `Sign ${this.currentIndex + 1} of ${this.sequence.length}`;
    }

    this.highlightChip(tokenIndex);
    this.updateNavButtons();

    // Load and play video clip
    if (this.video && videoUrl) {
      console.log('[Phase1] video element found');
      
      // Robust Autoplay Config
      this.video.muted = true;
      this.video.autoplay = true;
      this.video.setAttribute('muted', 'true');
      this.video.setAttribute('autoplay', 'true');
      
      this.video.src = videoUrl;
      console.log('[Phase1] video.src set to:', this.video.src);
      this.video.playbackRate = this.playbackSpeed;
      this.video.load();

      if (autoPlay) {
        const playPromise = this.video.play();
        if (playPromise !== undefined) {
          playPromise
            .then(() => {
              console.log('[Phase1] play resolved');
              console.log('[Phase1] playing');
              this.isPlaying = true;
              this.updatePlayButton();
            })
            .catch(err => {
              console.error('[Phase1] play rejected:', err);
              console.error(`[Phase1] error code: ${this.video.error?.code}, message: ${this.video.error?.message}`);
              console.error(`[Phase1] readyState: ${this.video.readyState}, networkState: ${this.video.networkState}`);
              this.isPlaying = false;
              this.updatePlayButton();
              
              if (window.showNotification) {
                 window.showNotification('Browser blocked autoplay. Please click Play manually to start the sequence.', 'warning');
              }
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
    setTimeout(() => {
      if (this.currentIndex < this.sequence.length - 1) {
        this.next();
      }
    }, 500);
  }
}

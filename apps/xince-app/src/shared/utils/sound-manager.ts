const SOUND_KEY = "xc_sound_enabled";
const HAPTIC_KEY = "xc_haptic_enabled";

let audioContext: AudioContext | null = null;

function isH5() {
  return typeof window !== "undefined";
}

function ensureAudioContext() {
  if (!isH5()) {
    return null;
  }
  const AudioContextCtor =
    window.AudioContext ||
    // @ts-expect-error safari prefix
    window.webkitAudioContext;
  if (!AudioContextCtor) {
    return null;
  }
  audioContext = audioContext || new AudioContextCtor();
  return audioContext;
}

function getFlag(key: string, fallback = true) {
  const stored = uni.getStorageSync(key);
  if (typeof stored === "boolean") {
    return stored;
  }
  return fallback;
}

function setFlag(key: string, value: boolean) {
  uni.setStorageSync(key, value);
}

function playTone(
  ctx: AudioContext,
  options: {
    frequency: number;
    type: OscillatorType;
    startAt: number;
    duration: number;
    gainValue: number;
  },
) {
  const { frequency, type, startAt, duration, gainValue } = options;
  const oscillator = ctx.createOscillator();
  const gain = ctx.createGain();
  oscillator.type = type;
  oscillator.frequency.setValueAtTime(frequency, startAt);
  gain.gain.setValueAtTime(0.0001, startAt);
  gain.gain.exponentialRampToValueAtTime(gainValue, startAt + 0.01);
  gain.gain.exponentialRampToValueAtTime(0.0001, startAt + duration);
  oscillator.connect(gain);
  gain.connect(ctx.destination);
  oscillator.start(startAt);
  oscillator.stop(startAt + duration);
}

export const SoundManager = {
  isSoundEnabled() {
    return getFlag(SOUND_KEY, true);
  },
  setSoundEnabled(value: boolean) {
    setFlag(SOUND_KEY, value);
  },
  isHapticEnabled() {
    return getFlag(HAPTIC_KEY, true);
  },
  setHapticEnabled(value: boolean) {
    setFlag(HAPTIC_KEY, value);
  },
  haptic(ms = 40) {
    if (!this.isHapticEnabled()) {
      return;
    }
    try {
      // #ifdef H5
      if (typeof navigator !== "undefined" && navigator.vibrate) {
        navigator.vibrate(ms);
      }
      // #endif
      uni.vibrateShort?.();
    } catch (err) {
      console.debug("haptic unavailable", err);
    }
  },
  play(type: "chime" | "ding" | "whoosh" | "ambient") {
    if (!this.isSoundEnabled()) {
      return;
    }
    const ctx = ensureAudioContext();
    if (!ctx) {
      return;
    }
    const now = ctx.currentTime;
    if (type === "chime") {
      playTone(ctx, { frequency: 440, type: "sine", startAt: now, duration: 0.15, gainValue: 0.08 });
      playTone(ctx, { frequency: 660, type: "sine", startAt: now + 0.01, duration: 0.15, gainValue: 0.08 });
      return;
    }
    if (type === "ding") {
      playTone(ctx, { frequency: 880, type: "triangle", startAt: now, duration: 0.1, gainValue: 0.06 });
      return;
    }
    if (type === "ambient") {
      playTone(ctx, { frequency: 220, type: "sine", startAt: now, duration: 3, gainValue: 0.02 });
      return;
    }

    const bufferSize = ctx.sampleRate * 0.18;
    const buffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
    const data = buffer.getChannelData(0);
    for (let index = 0; index < bufferSize; index += 1) {
      data[index] = (Math.random() * 2 - 1) * (1 - index / bufferSize);
    }
    const source = ctx.createBufferSource();
    source.buffer = buffer;
    const filter = ctx.createBiquadFilter();
    filter.type = "bandpass";
    filter.frequency.setValueAtTime(800, now);
    filter.frequency.linearRampToValueAtTime(2400, now + 0.16);
    const gain = ctx.createGain();
    gain.gain.setValueAtTime(0.001, now);
    gain.gain.exponentialRampToValueAtTime(0.08, now + 0.02);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.16);
    source.connect(filter);
    filter.connect(gain);
    gain.connect(ctx.destination);
    source.start(now);
    source.stop(now + 0.18);
  },
};

export function playSound(type: "chime" | "ding" | "whoosh" | "ambient") {
  SoundManager.play(type);
}

export function haptic(ms = 15) {
  SoundManager.haptic(ms);
}

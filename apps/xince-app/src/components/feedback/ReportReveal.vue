<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from "vue";

import XiaoCe from "@/components/mascot/XiaoCe.vue";
import { SoundManager } from "@/shared/utils/sound-manager";

interface RevealPersonaLike {
  persona_name?: string | null;
  persona_key?: string | null;
  emoji?: string | null;
  result_tier?: string | null;
}

const props = withDefaults(
  defineProps<{
    visible: boolean;
    persona?: RevealPersonaLike | null;
    totalScore?: number;
    onComplete?: (() => void) | null;
  }>(),
  {
    persona: null,
    totalScore: 0,
    onComplete: null,
  },
);

const emit = defineEmits<{
  complete: [];
}>();

const step = ref(1);
const progress = ref(0);
const scoreDisplay = ref(0);
const dimensions = ["理性", "感受", "行动", "洞察", "边界"];
const dimensionVisible = ref<boolean[]>([false, false, false, false, false]);
const particles = Array.from({ length: 20 }, (_, index) => ({
  id: index,
  left: `${5 + (index * 11) % 90}%`,
  size: `${3 + (index % 4)}px`,
  delay: `${(index % 8) * 0.25}s`,
  duration: `${3 + (index % 4)}s`,
}));

let timers: ReturnType<typeof setTimeout>[] = [];
let progressTimer: ReturnType<typeof setInterval> | null = null;
let scoreTimer: ReturnType<typeof setInterval> | null = null;

const personaEmoji = computed(() => {
  if (props.persona?.emoji) {
    return props.persona.emoji;
  }
  const key = `${props.persona?.persona_name || ""}${props.persona?.persona_key || ""}`.toLowerCase();
  if (key.includes("sun") || key.includes("光")) {
    return "☀️";
  }
  if (key.includes("moon") || key.includes("月")) {
    return "🌙";
  }
  if (key.includes("star") || key.includes("星")) {
    return "🌟";
  }
  if (key.includes("water") || key.includes("海")) {
    return "🌊";
  }
  return "✨";
});

const personaName = computed(() => props.persona?.persona_name || "灵魂旅人");
const tierText = computed(() => props.persona?.result_tier || "稀有人格");
const typedText = computed(() => "正在分析你的灵魂密码...");

function clearTimers() {
  timers.forEach((timer) => clearTimeout(timer));
  timers = [];
  if (progressTimer) {
    clearInterval(progressTimer);
    progressTimer = null;
  }
  if (scoreTimer) {
    clearInterval(scoreTimer);
    scoreTimer = null;
  }
}

function animateScore() {
  scoreDisplay.value = 0;
  const target = Math.max(0, Math.min(999, Math.round(props.totalScore || 0)));
  if (!target) {
    return;
  }
  const duration = 900;
  const tick = 16;
  const totalTicks = Math.max(1, Math.floor(duration / tick));
  const delta = target / totalTicks;
  scoreTimer = setInterval(() => {
    scoreDisplay.value = Math.min(target, Math.round(scoreDisplay.value + delta));
    if (scoreDisplay.value >= target && scoreTimer) {
      clearInterval(scoreTimer);
      scoreTimer = null;
    }
  }, tick);
}

function runReveal() {
  clearTimers();
  step.value = 1;
  progress.value = 0;
  scoreDisplay.value = 0;
  dimensionVisible.value = [false, false, false, false, false];
  SoundManager.play("ambient");
  SoundManager.haptic(25);

  progressTimer = setInterval(() => {
    progress.value = Math.min(96, progress.value + 1.4);
  }, 60);

  timers.push(
    setTimeout(() => {
      step.value = 2;
      SoundManager.play("whoosh");
      dimensions.forEach((_, index) => {
        timers.push(
          setTimeout(() => {
            dimensionVisible.value[index] = true;
            SoundManager.haptic(15);
          }, 210 * index),
        );
      });
    }, 2000),
  );

  timers.push(
    setTimeout(() => {
      step.value = 3;
      progress.value = 100;
      SoundManager.play("chime");
      SoundManager.haptic(50);
      animateScore();
    }, 4000),
  );

  timers.push(
    setTimeout(() => {
      step.value = 4;
      if (progressTimer) {
        clearInterval(progressTimer);
        progressTimer = null;
      }
    }, 6000),
  );

  timers.push(
    setTimeout(() => {
      props.onComplete?.();
      emit("complete");
    }, 6480),
  );
}

watch(
  () => props.visible,
  (visible) => {
    if (!visible) {
      clearTimers();
      return;
    }
    runReveal();
  },
);

onBeforeUnmount(() => {
  clearTimers();
});
</script>

<template>
  <view v-if="visible" class="reveal" :class="{ 'reveal--out': step === 4 }">
    <view class="reveal__bg" />
    <view class="reveal__particles">
      <view
        v-for="particle in particles"
        :key="particle.id"
        class="reveal__particle"
        :style="{
          left: particle.left,
          width: particle.size,
          height: particle.size,
          animationDelay: particle.delay,
          animationDuration: particle.duration,
        }"
      />
    </view>

    <view v-if="step === 1" class="reveal__step reveal__step--prepare">
      <view class="reveal__halo">
        <XiaoCe expression="surprised" size="lg" :animated="true" />
      </view>
      <text class="reveal__typing">{{ typedText }}</text>
      <view class="reveal__progress">
        <view class="reveal__progress-fill" :style="{ width: `${progress}%` }" />
      </view>
      <text class="reveal__progress-text">{{ Math.round(progress) }}%</text>
    </view>

    <view v-else-if="step === 2" class="reveal__step reveal__step--dimension">
      <text class="reveal__hint">维度解析中...</text>
      <view class="dimension-cloud">
        <text
          v-for="(item, index) in dimensions"
          :key="item"
          class="dimension-cloud__item"
          :class="[{ 'dimension-cloud__item--show': dimensionVisible[index] }, `d-${index + 1}`]"
        >
          {{ item }}
        </text>
      </view>
    </view>

    <view v-else class="reveal__step reveal__step--result">
      <text class="reveal__emoji">{{ personaEmoji }}</text>
      <text class="reveal__name">{{ personaName }}</text>
      <text class="reveal__tier">{{ tierText }}</text>
      <text class="reveal__score">{{ scoreDisplay }}</text>
      <text class="reveal__score-label">灵魂总分</text>
    </view>
  </view>
</template>

<style scoped lang="scss">
.reveal {
  position: fixed;
  inset: 0;
  z-index: 999;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48rpx;
  transition: transform 0.45s $xc-ease;
}

.reveal--out {
  transform: translateY(-100%);
}

.reveal__bg {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 28% 18%, rgba(201, 181, 240, 0.35), transparent 35%),
    radial-gradient(circle at 78% 22%, rgba(232, 114, 154, 0.22), transparent 40%),
    linear-gradient(180deg, rgba(58, 46, 66, 0.98), rgba(45, 33, 56, 0.98));
}

.reveal__particles {
  position: absolute;
  inset: 0;
}

.reveal__particle {
  position: absolute;
  bottom: -10vh;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.45);
  animation: revealFloat linear infinite;
}

.reveal__step {
  position: relative;
  z-index: 1;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  color: #fff;
  text-align: center;
}

.reveal__halo {
  padding: 26rpx;
  border-radius: 50%;
  background: rgba(237, 229, 249, 0.16);
  box-shadow:
    0 0 0 2rpx rgba(201, 181, 240, 0.35),
    0 0 48rpx rgba(155, 126, 216, 0.55);
  animation: haloSpin 5s linear infinite;
}

.reveal__typing {
  margin-top: 28rpx;
  font-size: 30rpx;
  letter-spacing: 2rpx;
  white-space: nowrap;
  overflow: hidden;
  border-right: 2rpx solid rgba(255, 255, 255, 0.8);
  animation:
    typing 1.8s steps(14, end) infinite alternate,
    blink 0.65s step-end infinite;
}

.reveal__progress {
  width: 78%;
  height: 14rpx;
  margin-top: 34rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.18);
  overflow: hidden;
}

.reveal__progress-fill {
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #9b7ed8, #e8729a, #f2a68b);
  transition: width 0.2s linear;
}

.reveal__progress-text {
  margin-top: 12rpx;
  font-size: 22rpx;
  color: rgba(255, 255, 255, 0.8);
}

.reveal__hint {
  font-size: 26rpx;
  color: rgba(255, 255, 255, 0.9);
}

.dimension-cloud {
  margin-top: 26rpx;
  width: 100%;
  min-height: 300rpx;
  position: relative;
}

.dimension-cloud__item {
  position: absolute;
  opacity: 0;
  font-size: 34rpx;
  font-weight: 600;
  transform: scale(0.75);
  transition: all 0.3s $xc-spring;
}

.dimension-cloud__item--show {
  opacity: 1;
  transform: scale(1);
  text-shadow: 0 0 22rpx rgba(201, 181, 240, 0.75);
}

.d-1 {
  left: 8%;
  top: 18%;
  color: #c9b5f0;
}

.d-2 {
  right: 10%;
  top: 12%;
  color: #f4a5bf;
}

.d-3 {
  left: 12%;
  bottom: 16%;
  color: #a8ddd0;
}

.d-4 {
  right: 14%;
  bottom: 10%;
  color: #e5c97e;
}

.d-5 {
  left: 41%;
  top: 40%;
  color: #fff;
}

.reveal__emoji {
  font-size: 128rpx;
  line-height: 1;
  animation: revealSpin 0.9s $xc-ease both;
}

.reveal__name {
  margin-top: 26rpx;
  font-size: 46rpx;
  font-weight: 700;
  font-family: $xc-font-serif;
  animation: fadeInUp 0.4s $xc-ease both;
}

.reveal__tier {
  margin-top: 14rpx;
  padding: 10rpx 22rpx;
  border-radius: 999rpx;
  background: rgba(212, 168, 83, 0.2);
  color: #fdf4de;
  font-size: 24rpx;
  animation: glowPulse 1.2s ease-in-out infinite;
}

.reveal__score {
  margin-top: 24rpx;
  font-size: 62rpx;
  font-weight: 700;
  color: #fdf4de;
}

.reveal__score-label {
  margin-top: 8rpx;
  font-size: 22rpx;
  color: rgba(255, 255, 255, 0.8);
}

@keyframes revealFloat {
  0% {
    opacity: 0;
    transform: translateY(100vh) scale(0.6);
  }
  20% {
    opacity: 0.7;
  }
  100% {
    opacity: 0;
    transform: translateY(-10vh) scale(1);
  }
}

@keyframes revealSpin {
  0% {
    opacity: 0;
    transform: rotateY(0deg) scale(0.7);
  }
  100% {
    opacity: 1;
    transform: rotateY(360deg) scale(1);
  }
}

@keyframes haloSpin {
  from {
    transform: rotate(0);
  }
  to {
    transform: rotate(360deg);
  }
}

@keyframes typing {
  from {
    width: 0;
  }
  to {
    width: 22em;
  }
}

@keyframes blink {
  0%,
  100% {
    border-color: rgba(255, 255, 255, 0.85);
  }
  50% {
    border-color: transparent;
  }
}
</style>

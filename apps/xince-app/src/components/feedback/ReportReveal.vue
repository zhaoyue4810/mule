<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref, watch } from "vue";

import ConfettiCanvas from "@/components/feedback/ConfettiCanvas.vue";
import XiaoCe from "@/components/mascot/XiaoCe.vue";
import { SoundManager } from "@/shared/utils/sound-manager";

interface RevealPersonaDimensionLike {
  name?: string | null;
  dim_name?: string | null;
  label?: string | null;
}

interface RevealPersonaLike {
  name?: string | null;
  persona_name?: string | null;
  persona_key?: string | null;
  emoji?: string | null;
  result_tier?: string | null;
  rarity_percent?: number | null;
  dimensions?: RevealPersonaDimensionLike[] | null;
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

const currentStep = ref(1);
const progress = ref(0);
const typedText = ref("");
const scoreDisplay = ref(0);
const currentDimensionText = ref("");
const currentDimensionDirection = ref<"left" | "right" | "top" | "bottom" | "center">("center");
const dimensionVisible = ref(false);
const cardFlipping = ref(false);
const cardFlipped = ref(false);
const confettiActive = ref(false);
const showRarity = ref(false);
const ctaVisible = ref(false);
const ctaAttention = ref(false);
const completed = ref(false);

const starSeed = [
  { id: 1, left: "12%", top: "16%", size: "8rpx" },
  { id: 2, left: "28%", top: "30%", size: "10rpx" },
  { id: 3, left: "76%", top: "22%", size: "12rpx" },
  { id: 4, left: "84%", top: "40%", size: "8rpx" },
  { id: 5, left: "20%", top: "62%", size: "9rpx" },
  { id: 6, left: "70%", top: "68%", size: "11rpx" },
];
const dimensionDirections: Array<"left" | "right" | "top" | "bottom" | "center"> = [
  "left",
  "right",
  "top",
  "bottom",
  "center",
];

let timers: ReturnType<typeof setTimeout>[] = [];
let typingTimer: ReturnType<typeof setInterval> | null = null;
let scoreTimer: ReturnType<typeof setInterval> | null = null;

const personaDimensions = computed(() => {
  const raw = props.persona?.dimensions;
  if (!Array.isArray(raw)) {
    return [];
  }
  return raw
    .map((item) => item?.name || item?.dim_name || item?.label || "")
    .map((item) => item.trim())
    .filter(Boolean)
    .slice(0, 5);
});

const personaEmoji = computed(() => {
  if (props.persona?.emoji) {
    return props.persona.emoji;
  }
  const key = `${props.persona?.name || ""}${props.persona?.persona_name || ""}${props.persona?.persona_key || ""}`.toLowerCase();
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

const personaName = computed(
  () => props.persona?.name || props.persona?.persona_name || "灵魂旅人",
);
const rarityLabel = computed(() => {
  const rarity = Number(props.persona?.rarity_percent);
  if (Number.isFinite(rarity) && rarity > 0) {
    return `仅 ${Math.round(rarity)}% 的人是这个类型`;
  }
  return props.persona?.result_tier || "你的专属人格已显现";
});
const scoreTarget = computed(() =>
  Math.max(0, Math.min(999, Math.round(props.totalScore || 0))),
);

function playIfEnabled(type: "chime" | "ding" | "whoosh" | "ambient") {
  if (SoundManager.isSoundEnabled()) {
    SoundManager.play(type);
  }
}

function clearTimers() {
  timers.forEach((timer) => clearTimeout(timer));
  timers = [];
  if (typingTimer) {
    clearInterval(typingTimer);
    typingTimer = null;
  }
  if (scoreTimer) {
    clearInterval(scoreTimer);
    scoreTimer = null;
  }
}

function schedule(callback: () => void, delay: number) {
  const timer = setTimeout(callback, delay);
  timers.push(timer);
}

function setProgress(target: number) {
  void nextTick(() => {
    progress.value = target;
  });
}

function startTyping(text: string) {
  typedText.value = "";
  if (typingTimer) {
    clearInterval(typingTimer);
  }
  let index = 0;
  typingTimer = setInterval(() => {
    index += 1;
    typedText.value = text.slice(0, index);
    if (index >= text.length && typingTimer) {
      clearInterval(typingTimer);
      typingTimer = null;
    }
  }, 75);
}

function animateScore() {
  scoreDisplay.value = 0;
  if (!scoreTarget.value) {
    return;
  }
  const duration = 1000;
  const tick = 16;
  const totalTicks = Math.max(1, Math.floor(duration / tick));
  const delta = scoreTarget.value / totalTicks;
  scoreTimer = setInterval(() => {
    scoreDisplay.value = Math.min(scoreTarget.value, Math.round(scoreDisplay.value + delta));
    if (scoreDisplay.value >= scoreTarget.value && scoreTimer) {
      clearInterval(scoreTimer);
      scoreTimer = null;
    }
  }, tick);
}

function triggerDimensionFlash(index: number) {
  currentDimensionDirection.value = dimensionDirections[index] || "center";
  currentDimensionText.value = personaDimensions.value[index] || "";
  dimensionVisible.value = false;
  void nextTick(() => {
    dimensionVisible.value = true;
  });
  schedule(() => {
    dimensionVisible.value = false;
  }, 220);
}

function startStep5() {
  currentStep.value = 5;
  ctaVisible.value = true;
}

function startStep4() {
  currentStep.value = 4;
  setProgress(100);
  showRarity.value = true;
  confettiActive.value = true;
  playIfEnabled("chime");
  SoundManager.haptic(30);
  animateScore();
  schedule(startStep5, 1500);
}

function startStep3() {
  currentStep.value = 3;
  setProgress(85);
  cardFlipping.value = true;
  cardFlipped.value = false;
  schedule(() => {
    cardFlipped.value = true;
    cardFlipping.value = false;
    playIfEnabled("ding");
  }, 800);
  schedule(startStep4, 1500);
}

function startStep2() {
  currentStep.value = 2;
  setProgress(60);
  if (!personaDimensions.value.length) {
    currentDimensionDirection.value = "center";
    currentDimensionText.value = "正在校准人格维度...";
    dimensionVisible.value = true;
    schedule(() => {
      dimensionVisible.value = false;
    }, 1200);
    schedule(startStep3, 1500);
    return;
  }
  personaDimensions.value.forEach((_, index) => {
    schedule(() => {
      triggerDimensionFlash(index);
    }, index * 300);
  });
  schedule(startStep3, 1500);
}

function runReveal() {
  clearTimers();
  completed.value = false;
  currentStep.value = 1;
  progress.value = 0;
  typedText.value = "";
  scoreDisplay.value = 0;
  currentDimensionText.value = "";
  currentDimensionDirection.value = "center";
  dimensionVisible.value = false;
  cardFlipping.value = false;
  cardFlipped.value = false;
  confettiActive.value = false;
  showRarity.value = false;
  ctaVisible.value = false;
  ctaAttention.value = false;

  playIfEnabled("ambient");
  startTyping("正在解读你的灵魂密码...");
  setProgress(30);

  schedule(startStep2, 2000);
  schedule(() => {
    if (!completed.value) {
      ctaAttention.value = true;
    }
  }, 10000);
}

function handleComplete() {
  if (completed.value) {
    return;
  }
  completed.value = true;
  props.onComplete?.();
  emit("complete");
}

watch(
  () => props.visible,
  (visible) => {
    if (!visible) {
      clearTimers();
      confettiActive.value = false;
      ctaVisible.value = false;
      ctaAttention.value = false;
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
  <view v-if="visible" class="reveal">
    <ConfettiCanvas :active="confettiActive" @done="confettiActive = false" />
    <view class="reveal__bg" />
    <view class="reveal__stars">
      <view
        v-for="star in starSeed"
        :key="star.id"
        class="reveal__star"
        :style="{
          left: star.left,
          top: star.top,
          width: star.size,
          height: star.size,
          animationDuration: `${2.2 + star.id * 0.2}s`,
        }"
      />
    </view>

    <view class="reveal__content" :class="{ 'reveal__content--lifted': currentStep >= 5 }">
      <view v-if="currentStep === 1" class="reveal__step reveal__step--prepare">
        <view class="reveal__mascot">
          <XiaoCe expression="thinking" size="lg" :animated="true" />
        </view>
        <text class="reveal__typing">{{ typedText }}</text>
      </view>

      <view
        v-else-if="currentStep === 2"
        class="reveal__step reveal__step--dimension"
      >
        <view
          class="reveal__dimension-shell"
          :class="[
            `reveal__dimension-shell--${currentDimensionDirection}`,
            { 'reveal__dimension-shell--show': dimensionVisible },
          ]"
        >
          <text class="reveal__dimension-text">{{ currentDimensionText }}</text>
        </view>
      </view>

      <view v-else class="reveal__step reveal__step--result">
        <view
          class="reveal__persona-card"
          :class="{
            'reveal__persona-card--flipping': cardFlipping,
            'reveal__persona-card--flipped': cardFlipped,
            'reveal__persona-card--compact': currentStep >= 4,
          }"
        >
          <view class="reveal__persona-card-inner">
            <view class="reveal__persona-face reveal__persona-face--back">
              <text class="reveal__card-mark">?</text>
            </view>
            <view class="reveal__persona-face reveal__persona-face--front">
              <text class="reveal__emoji">{{ personaEmoji }}</text>
              <text class="reveal__name">{{ personaName }}</text>
            </view>
          </view>
        </view>

        <view v-if="currentStep >= 4" class="reveal__stats">
          <text class="reveal__score">{{ scoreDisplay }}</text>
          <text class="reveal__score-label">灵魂总分</text>
          <text v-if="showRarity" class="reveal__rarity">{{ rarityLabel }}</text>
        </view>
      </view>

      <button
        v-if="ctaVisible"
        class="reveal__cta"
        :class="{ 'reveal__cta--pulse': ctaAttention }"
        @tap="handleComplete"
      >
        查看完整报告
      </button>
    </view>

    <view class="reveal__progress">
      <view class="reveal__progress-fill" :style="{ width: `${progress}%` }" />
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
}

.reveal__bg {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 20% 16%, rgba(201, 181, 240, 0.24), transparent 34%),
    radial-gradient(circle at 82% 22%, rgba(232, 114, 154, 0.18), transparent 38%),
    linear-gradient(180deg, #2a1b3d, #44318d);
}

.reveal__stars {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.reveal__star {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.78);
  box-shadow: 0 0 18rpx rgba(255, 255, 255, 0.45);
  animation: starPulse ease-in-out infinite;
}

.reveal__content {
  position: relative;
  z-index: 1;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #fff;
  text-align: center;
  transition: transform 0.4s $xc-ease;
}

.reveal__content--lifted {
  transform: translateY(-10px);
}

.reveal__step {
  width: 100%;
  min-height: 620rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.reveal__step--prepare {
  gap: 24rpx;
}

.reveal__mascot {
  animation: gentleBounce 2.6s ease-in-out infinite;
}

.reveal__typing {
  min-height: 44rpx;
  font-size: 30rpx;
  letter-spacing: 2rpx;
  color: rgba(255, 255, 255, 0.92);
}

.reveal__dimension-shell {
  position: relative;
  min-width: 260rpx;
  padding: 22rpx 36rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.14);
  border: 2rpx solid rgba(255, 255, 255, 0.18);
  backdrop-filter: blur(12px);
  opacity: 0;
  transition:
    transform 0.3s $xc-spring,
    opacity 0.24s ease;
}

.reveal__dimension-shell::before,
.reveal__dimension-shell::after {
  content: "";
  position: absolute;
  inset: -80rpx;
  pointer-events: none;
  opacity: 0;
}

.reveal__dimension-shell--left {
  transform: translateX(-180rpx);
}

.reveal__dimension-shell--right {
  transform: translateX(180rpx);
}

.reveal__dimension-shell--top {
  transform: translateY(-180rpx);
}

.reveal__dimension-shell--bottom {
  transform: translateY(180rpx);
}

.reveal__dimension-shell--center {
  transform: scale(0.3);
}

.reveal__dimension-shell--show {
  opacity: 1;
  transform: translateX(0) translateY(0) scale(1);
}

.reveal__dimension-shell--show::before,
.reveal__dimension-shell--show::after {
  animation: edgeTint 0.3s ease;
}

.reveal__dimension-shell--left::before {
  background: linear-gradient(90deg, rgba(232, 114, 154, 0.3), transparent 70%);
}

.reveal__dimension-shell--right::before {
  background: linear-gradient(270deg, rgba(124, 197, 178, 0.3), transparent 70%);
}

.reveal__dimension-shell--top::before {
  background: linear-gradient(180deg, rgba(201, 181, 240, 0.3), transparent 70%);
}

.reveal__dimension-shell--bottom::before {
  background: linear-gradient(0deg, rgba(242, 166, 139, 0.3), transparent 70%);
}

.reveal__dimension-shell--center::before {
  background: radial-gradient(circle, rgba(212, 168, 83, 0.28), transparent 68%);
}

.reveal__dimension-text {
  font-size: 34rpx;
  font-weight: 700;
  text-shadow: 0 0 22rpx rgba(255, 255, 255, 0.24);
}

.reveal__persona-card {
  width: 340rpx;
  height: 460rpx;
  perspective: 1000rpx;
  transition:
    transform 0.45s $xc-spring,
    margin-bottom 0.45s $xc-spring;
}

.reveal__persona-card--compact {
  transform: scale(0.74) translateY(-80rpx);
  margin-bottom: -44rpx;
}

.reveal__persona-card-inner {
  position: relative;
  width: 100%;
  height: 100%;
  transform-style: preserve-3d;
  transition: transform 0.8s $xc-ease;
}

.reveal__persona-card--flipped .reveal__persona-card-inner,
.reveal__persona-card--flipping .reveal__persona-card-inner {
  transform: rotateY(180deg);
}

.reveal__persona-face {
  position: absolute;
  inset: 0;
  border-radius: 30rpx;
  backface-visibility: hidden;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  box-shadow: 0 18rpx 50rpx rgba(27, 18, 47, 0.32);
  overflow: hidden;
}

.reveal__persona-face--back {
  background:
    radial-gradient(circle at 50% 20%, rgba(255, 255, 255, 0.1), transparent 40%),
    repeating-linear-gradient(
      45deg,
      rgba(255, 255, 255, 0.08) 0 12rpx,
      rgba(255, 255, 255, 0) 12rpx 24rpx
    ),
    linear-gradient(145deg, #412863, #6a48a3);
  border: 2rpx solid rgba(201, 181, 240, 0.3);
}

.reveal__persona-face--front {
  transform: rotateY(180deg);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(237, 229, 249, 0.92));
  border: 2rpx solid rgba(201, 181, 240, 0.36);
  color: #3a2e42;
}

.reveal__card-mark {
  font-size: 112rpx;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.9);
}

.reveal__emoji {
  font-size: 96rpx;
  line-height: 1;
}

.reveal__name {
  margin-top: 24rpx;
  padding: 0 28rpx;
  font-size: 42rpx;
  font-weight: 700;
  font-family: $xc-font-serif;
}

.reveal__stats {
  margin-top: 14rpx;
  animation: fadeInUp 0.4s $xc-ease both;
}

.reveal__score {
  display: block;
  font-size: 88rpx;
  font-weight: 700;
  color: #fff9e9;
}

.reveal__score-label {
  display: block;
  margin-top: 6rpx;
  font-size: 22rpx;
  color: rgba(255, 255, 255, 0.76);
}

.reveal__rarity {
  display: inline-flex;
  margin-top: 20rpx;
  padding: 12rpx 24rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.14);
  border: 2rpx solid rgba(255, 255, 255, 0.16);
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.88);
}

.reveal__cta {
  position: relative;
  margin-top: 42rpx;
  padding: 24rpx 72rpx;
  border-radius: 999rpx;
  background: linear-gradient(135deg, #9b7ed8, #e8729a);
  color: #fff;
  font-size: 28rpx;
  font-weight: 700;
  box-shadow: 0 12rpx 28rpx rgba(155, 126, 216, 0.28);
  animation: scaleIn 0.35s $xc-spring both;
  overflow: hidden;
}

.reveal__cta::after {
  content: "";
  position: absolute;
  top: 0;
  bottom: 0;
  left: -40%;
  width: 36%;
  background: linear-gradient(90deg, rgba(255, 255, 255, 0), rgba(255, 255, 255, 0.34), rgba(255, 255, 255, 0));
  transform: skewX(-18deg);
  animation: shimmer 2.4s ease-in-out infinite;
}

.reveal__cta--pulse {
  animation:
    scaleIn 0.35s $xc-spring both,
    pulseGlow 1.5s ease-in-out infinite;
}

.reveal__progress {
  position: absolute;
  left: 48rpx;
  right: 48rpx;
  bottom: 48rpx;
  height: 14rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.14);
  overflow: hidden;
  z-index: 1;
}

.reveal__progress-fill {
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #9b7ed8, #e8729a, #f2a68b);
  transition: width 0.55s ease;
}

@keyframes gentleBounce {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-12rpx);
  }
}

@keyframes starPulse {
  0%,
  100% {
    opacity: 0.25;
    transform: scale(0.7);
  }
  50% {
    opacity: 1;
    transform: scale(1);
  }
}

@keyframes edgeTint {
  0%,
  100% {
    opacity: 0;
  }
  50% {
    opacity: 0.3;
  }
}

@keyframes shimmer {
  0% {
    transform: translateX(0) skewX(-18deg);
  }
  100% {
    transform: translateX(420%) skewX(-18deg);
  }
}

@keyframes scaleIn {
  from {
    opacity: 0;
    transform: scale(0.82);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

@keyframes pulseGlow {
  0%,
  100% {
    transform: scale(1);
    box-shadow: 0 12rpx 28rpx rgba(155, 126, 216, 0.28);
  }
  50% {
    transform: scale(1.03);
    box-shadow: 0 14rpx 34rpx rgba(155, 126, 216, 0.4);
  }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(16rpx);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>

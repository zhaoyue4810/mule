<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from "vue";

interface ConfettiPiece {
  id: number;
  left: string;
  size: string;
  color: string;
  borderRadius: string;
  delay: string;
  duration: string;
  drift: string;
  rotation: string;
}

const DEFAULT_COLORS = ["#9B7ED8", "#E8729A", "#F2A68B", "#7CC5B2", "#D4A853"];

const props = withDefaults(
  defineProps<{
    active: boolean;
    count?: number;
    duration?: number;
    colors?: string[];
  }>(),
  {
    count: 24,
    duration: 2500,
    colors: () => ["#9B7ED8", "#E8729A", "#F2A68B", "#7CC5B2", "#D4A853"],
  },
);

const emit = defineEmits<{
  done: [];
}>();

const pieces = ref<ConfettiPiece[]>([]);

let doneTimer: ReturnType<typeof setTimeout> | null = null;
let burstToken = 0;

function randomBetween(min: number, max: number) {
  return Math.random() * (max - min) + min;
}

function clearDoneTimer() {
  if (doneTimer) {
    clearTimeout(doneTimer);
    doneTimer = null;
  }
}

function clearPieces() {
  burstToken += 1;
  clearDoneTimer();
  pieces.value = [];
}

function buildPieces() {
  const safeColors = props.colors.length ? props.colors : DEFAULT_COLORS;
  return Array.from({ length: props.count }, (_, index) => {
    const delay = Math.round(randomBetween(0, 400));
    const size = Math.round(randomBetween(6, 12));
    return {
      id: index,
      left: `${Math.round(randomBetween(10, 90))}%`,
      size: `${size}rpx`,
      color: safeColors[Math.floor(Math.random() * safeColors.length)],
      borderRadius: Math.random() > 0.5 ? "50%" : "2rpx",
      delay: `${delay}ms`,
      duration: `${Math.max(600, props.duration - delay)}ms`,
      drift: `${Math.round(randomBetween(-60, 60))}px`,
      rotation: `${Math.round(randomBetween(0, 360))}deg`,
    };
  });
}

function triggerBurst() {
  clearPieces();
  const token = burstToken;
  pieces.value = buildPieces();
  doneTimer = setTimeout(() => {
    if (token !== burstToken) {
      return;
    }
    doneTimer = null;
    pieces.value = [];
    emit("done");
  }, props.duration);
}

watch(
  () => props.active,
  (active) => {
    if (active) {
      triggerBurst();
      return;
    }
    clearPieces();
  },
  { immediate: true },
);

onBeforeUnmount(() => {
  clearPieces();
});
</script>

<template>
  <view v-if="pieces.length" class="confetti">
    <view
      v-for="piece in pieces"
      :key="piece.id"
      class="confetti__piece"
      :style="{
        left: piece.left,
        width: piece.size,
        height: piece.size,
        background: piece.color,
        borderRadius: piece.borderRadius,
        animationDelay: piece.delay,
        animationDuration: piece.duration,
        '--drift': piece.drift,
        '--start-rotate': piece.rotation,
      }"
    />
  </view>
</template>

<style scoped lang="scss">
.confetti {
  position: fixed;
  inset: 0;
  z-index: 9999;
  overflow: hidden;
  pointer-events: none;
}

.confetti__piece {
  position: absolute;
  top: -20px;
  opacity: 0;
  animation-name: confettiFall;
  animation-fill-mode: both;
  animation-timing-function: ease-out;
  transform-origin: center;
}

@keyframes confettiFall {
  0% {
    opacity: 1;
    transform: translateY(-20px) translateX(var(--drift)) rotate(var(--start-rotate)) scale(0.3);
  }
  15% {
    opacity: 1;
    transform:
      translateY(30vh)
      translateX(calc(var(--drift) * 0.5))
      rotate(calc(var(--start-rotate) + 240deg))
      scale(1);
  }
  100% {
    opacity: 0;
    transform:
      translateY(105vh)
      translateX(calc(var(--drift) * -0.3))
      rotate(calc(var(--start-rotate) + 680deg))
      scale(0.6);
  }
}
</style>

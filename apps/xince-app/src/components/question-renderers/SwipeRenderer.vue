<script setup lang="ts">
import { computed, ref } from "vue";

import { haptic, playSound } from "@/shared/utils/sound-manager";

const props = defineProps<{
  modelValue: number | null;
  leftLabel?: string;
  rightLabel?: string;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: number];
}>();

const threshold = 60;
const offsetX = ref(0);
const dragging = ref(false);
const flash = ref(false);
const flying = ref<"" | "left" | "right">("");
const startX = ref(0);

const rotation = computed(() => offsetX.value * 0.1);
const swipeRatio = computed(() => Math.min(1, Math.abs(offsetX.value) / threshold));
const leftOpacity = computed(() => (offsetX.value < 0 ? swipeRatio.value : 0));
const rightOpacity = computed(() => (offsetX.value > 0 ? swipeRatio.value : 0));
const bgTint = computed(() => {
  if (offsetX.value > 0) {
    return "rgba(124, 197, 178, 0.12)";
  }
  if (offsetX.value < 0) {
    return "rgba(232, 114, 154, 0.12)";
  }
  return "rgba(255,255,255,0.88)";
});
const cardStyle = computed(() => {
  const transform =
    flying.value === "left"
      ? "translateX(-150%) rotate(-15deg)"
      : flying.value === "right"
        ? "translateX(150%) rotate(15deg)"
        : `translateX(${offsetX.value}px) rotate(${rotation.value}deg)`;
  const transition = dragging.value
    ? "none"
    : flying.value
      ? "transform 0.3s ease-out, opacity 0.3s ease-out, background 0.18s ease"
      : "transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1), background 0.18s ease";
  return {
    transform,
    transition,
    background: bgTint.value,
    opacity: flying.value ? 0 : 1,
  };
});

function triggerFlash() {
  flash.value = true;
  setTimeout(() => {
    flash.value = false;
  }, 300);
}

function commit(value: number, direction: "left" | "right") {
  flying.value = direction;
  playSound("whoosh");
  haptic(15);
  triggerFlash();
  setTimeout(() => {
    emit("update:modelValue", value);
    flying.value = "";
    offsetX.value = 0;
  }, 300);
}

function onTouchStart(event: { touches: Array<{ clientX: number }> }) {
  dragging.value = true;
  startX.value = event.touches[0]?.clientX || 0;
}

function onTouchMove(event: { touches: Array<{ clientX: number }> }) {
  if (!dragging.value) {
    return;
  }
  const current = event.touches[0]?.clientX || startX.value;
  offsetX.value = Math.max(-180, Math.min(180, current - startX.value));
}

function onTouchEnd() {
  dragging.value = false;
  if (offsetX.value <= -threshold) {
    commit(0, "left");
    return;
  }
  if (offsetX.value >= threshold) {
    commit(1, "right");
    return;
  }
  offsetX.value = 0;
}

function onMouseDown(event: { clientX: number }) {
  dragging.value = true;
  startX.value = event.clientX;
}

function onMouseMove(event: { clientX: number }) {
  if (!dragging.value) {
    return;
  }
  offsetX.value = Math.max(-180, Math.min(180, event.clientX - startX.value));
}

function onMouseUp() {
  if (!dragging.value) {
    return;
  }
  onTouchEnd();
}
</script>

<template>
  <view class="swipe q-enter">
    <view v-if="flash" class="edge-flash" />
    <text class="swipe__hint swipe__hint--left" :style="{ opacity: leftOpacity }">
      {{ leftLabel || "不像我" }}
    </text>
    <view
      class="swipe__card"
      :style="cardStyle"
      @touchstart.stop.prevent="onTouchStart"
      @touchmove.stop.prevent="onTouchMove"
      @touchend.stop.prevent="onTouchEnd"
      @touchcancel.stop.prevent="onTouchEnd"
      @mousedown.stop.prevent="onMouseDown"
      @mousemove.stop.prevent="onMouseMove"
      @mouseup.stop.prevent="onMouseUp"
      @mouseleave="onMouseUp"
    >
      <text class="swipe__emoji">🫧</text>
      <text class="swipe__title">拖动选择你的倾向</text>
    </view>
    <text class="swipe__hint swipe__hint--right" :style="{ opacity: rightOpacity }">
      {{ rightLabel || "很像我" }}
    </text>
  </view>
</template>

<style lang="scss" scoped>
.swipe {
  position: relative;
  min-height: 260rpx;
  border-radius: 24rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.swipe__card {
  width: 82%;
  border-radius: 26rpx;
  border: 2rpx solid rgba(155, 126, 216, 0.16);
  box-shadow: $xc-sh-md;
  padding: 38rpx 20rpx;
  text-align: center;
  will-change: transform, opacity;
}

.swipe__emoji {
  display: block;
  font-size: 46rpx;
}

.swipe__title {
  display: block;
  margin-top: 12rpx;
  font-size: 26rpx;
}

.swipe__hint {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  color: $xc-muted;
  font-size: 22rpx;
  transition: opacity 0.12s ease;
}

.swipe__hint--left {
  left: 8rpx;
}

.swipe__hint--right {
  right: 8rpx;
}

.edge-flash {
  position: absolute;
  inset: 0;
  border-radius: inherit;
  pointer-events: none;
  animation: edgeFlash 0.3s ease;
}

.q-enter {
  animation: qEnter 0.4s $xc-ease both;
}

@keyframes qEnter {
  from {
    opacity: 0;
    transform: translateX(30px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes edgeFlash {
  0% {
    box-shadow: inset 0 0 0 0 rgba(155, 126, 216, 0.7);
  }
  100% {
    box-shadow: inset 0 0 0 18rpx rgba(232, 114, 154, 0);
  }
}
</style>

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
const leftActive = computed(() => offsetX.value < -30);
const rightActive = computed(() => offsetX.value > 30);
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
    <view class="swipe__zone">
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
        <text class="swipe__stamp swipe__stamp--left" :style="{ opacity: leftOpacity }">不太像我</text>
        <text class="swipe__stamp swipe__stamp--right" :style="{ opacity: rightOpacity }">很像我</text>
        <text class="swipe__emoji">💭</text>
        <text class="swipe__title">拖动这张灵魂卡，选出更接近你的方向</text>
      </view>
    </view>
    <view class="swipe__hints">
      <text class="swipe__hint swipe__hint--left" :class="{ 'swipe__hint--active-no': leftActive }">
        ← {{ leftLabel || "不太像我" }}
      </text>
      <text class="swipe__hint swipe__hint--right" :class="{ 'swipe__hint--active-yes': rightActive }">
        {{ rightLabel || "很像我" }} →
      </text>
    </view>
  </view>
</template>

<style lang="scss" scoped>
.swipe {
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-height: 460rpx;
  perspective: 800px;
}

.swipe__zone {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 320rpx;
}

.swipe__card {
  position: relative;
  width: 82%;
  padding: 40rpx 24rpx;
  background: rgba(255, 255, 255, 0.92);
  border-radius: $xc-r-lg;
  box-shadow: $xc-sh-lg;
  text-align: center;
  user-select: none;
  touch-action: none;
  cursor: grab;
  will-change: transform, opacity;
}

.swipe__emoji {
  display: block;
  font-size: 56rpx;
  margin-bottom: 12rpx;
}

.swipe__title {
  display: block;
  font-size: 26rpx;
  font-weight: 700;
  line-height: 1.55;
  color: $xc-ink;
}

.swipe__stamp {
  position: absolute;
  top: 22rpx;
  font-size: 24rpx;
  font-weight: 900;
  padding: 8rpx 16rpx;
  border-radius: 14rpx;
  border: 4rpx solid;
  opacity: 0;
  transition: opacity 0.15s;
}

.swipe__stamp--left {
  left: 16rpx;
  transform: rotate(-15deg);
  color: $xc-pink;
  border-color: $xc-pink;
  background: $xc-pink-p;
}

.swipe__stamp--right {
  right: 16rpx;
  transform: rotate(15deg);
  color: $xc-mint;
  border-color: $xc-mint;
  background: $xc-mint-p;
}

.swipe__hints {
  display: flex;
  justify-content: space-between;
  padding: 0 20rpx;
  margin-top: 18rpx;
}

.swipe__hint {
  display: flex;
  align-items: center;
  gap: 5rpx;
  font-size: 22rpx;
  font-weight: 700;
  padding: 12rpx 18rpx;
  border-radius: 999rpx;
  transition: all 0.3s;
}

.swipe__hint--left {
  color: $xc-pink;
  background: $xc-pink-p;
}

.swipe__hint--right {
  color: $xc-mint;
  background: $xc-mint-p;
}

.swipe__hint--active-no {
  box-shadow: 0 8rpx 18rpx rgba(232, 114, 154, 0.16);
  transform: translateX(-6rpx) scale(1.02);
}

.swipe__hint--active-yes {
  box-shadow: 0 8rpx 18rpx rgba(124, 197, 178, 0.16);
  transform: translateX(6rpx) scale(1.02);
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

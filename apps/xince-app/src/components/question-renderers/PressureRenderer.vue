<script setup lang="ts">
import { computed, ref } from "vue";

import { haptic, playSound } from "@/shared/utils/sound-manager";

const props = defineProps<{
  modelValue: number | null;
  min?: number;
  maxDuration?: number;
  step?: number;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: number];
}>();

const startAt = ref(0);
const duration = ref(props.modelValue ?? 0);
const running = ref(false);
const progress = ref(0);
const flash = ref(false);
let frame = 0;

const max = computed(() => props.maxDuration ?? 3000);
const ringStyle = computed(() => ({
  background: `conic-gradient(${`rgba(155,126,216,0.85) ${progress.value * 360}deg`}, rgba(155,126,216,0.15) 0deg)`,
}));
const emojiScale = computed(() => 1 + progress.value * 0.3);

function updateProgress() {
  if (!running.value) return;
  const elapsed = Math.min(max.value, Date.now() - startAt.value);
  duration.value = elapsed;
  progress.value = elapsed / max.value;
  if (elapsed >= max.value) {
    onPressEnd();
    return;
  }
  frame = requestAnimationFrame(updateProgress);
}

function onPressStart() {
  if (running.value) return;
  running.value = true;
  startAt.value = Date.now();
  frame = requestAnimationFrame(updateProgress);
}

function onPressEnd() {
  if (!running.value) return;
  running.value = false;
  cancelAnimationFrame(frame);
  const step = props.step && props.step > 0 ? props.step : 1;
  const min = props.min ?? 0;
  const snapped = Math.round((duration.value - min) / step) * step + min;
  const finalValue = Math.min(max.value, Math.max(min, snapped));
  duration.value = finalValue;
  playSound("whoosh");
  haptic(15);
  flash.value = true;
  setTimeout(() => (flash.value = false), 300);
  emit("update:modelValue", finalValue);
}
</script>

<template>
  <view class="pressure q-enter">
    <view v-if="flash" class="edge-flash" />
    <view
      class="pressure__ring"
      :style="ringStyle"
      @touchstart.stop.prevent="onPressStart"
      @touchend.stop.prevent="onPressEnd"
      @touchcancel.stop.prevent="onPressEnd"
    >
      <view class="pressure__pad" :style="{ boxShadow: `0 0 ${24 + progress * 28}rpx rgba(155,126,216,0.28)` }">
        <text class="pressure__emoji" :style="{ transform: `scale(${emojiScale})` }">💜</text>
        <text class="pressure__title">长按测压</text>
      </view>
    </view>
    <text class="pressure__value">{{ Math.round(duration) }} ms</text>
  </view>
</template>

<style lang="scss" scoped>
.pressure {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12rpx;
}

.pressure__ring {
  width: 320rpx;
  height: 320rpx;
  border-radius: 50%;
  padding: 14rpx;
}

.pressure__pad {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.92);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.pressure__emoji {
  font-size: 44rpx;
}

.pressure__title {
  margin-top: 8rpx;
  font-size: 28rpx;
}

.pressure__value {
  font-size: 22rpx;
  color: $xc-muted;
}

.edge-flash {
  position: absolute;
  inset: 0;
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
  from {
    box-shadow: inset 0 0 0 0 rgba(155, 126, 216, 0.5);
  }
  to {
    box-shadow: inset 0 0 0 14rpx rgba(155, 126, 216, 0);
  }
}
</style>

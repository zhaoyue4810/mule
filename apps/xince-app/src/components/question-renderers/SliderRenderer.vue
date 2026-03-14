<script setup lang="ts">
import { computed, ref } from "vue";

import { haptic, playSound } from "@/shared/utils/sound-manager";

const props = defineProps<{
  modelValue: number | null;
  min?: number;
  max?: number;
  step?: number;
  labels?: string[];
}>();

const emit = defineEmits<{
  "update:modelValue": [value: number];
}>();

const flash = ref(false);
const minVal = computed(() => props.min ?? 1);
const maxVal = computed(() => props.max ?? 5);
const current = computed(() => props.modelValue ?? minVal.value);
const rightLabel = computed(() => {
  if (!props.labels?.length) {
    return "高";
  }
  return props.labels[props.labels.length - 1] || "高";
});
const emojiMap = ["😢", "😕", "😐", "🙂", "😄"];
const percent = computed(() => ((current.value - minVal.value) / Math.max(1, maxVal.value - minVal.value)) * 100);
const emoji = computed(() => emojiMap[Math.min(emojiMap.length - 1, Math.max(0, Math.round(percent.value / 25)))]);
const tooltipLabel = computed(() => props.labels?.[Math.round(current.value - minVal.value)] || `等级 ${current.value}`);

function onInput(event: { detail: { value: number } }) {
  const value = Number(event.detail.value);
  emit("update:modelValue", value);
}

function onChange(event: { detail: { value: number } }) {
  playSound("chime");
  haptic(15);
  flash.value = true;
  setTimeout(() => {
    flash.value = false;
  }, 300);
  emit("update:modelValue", Number(event.detail.value));
}
</script>

<template>
  <view class="slider q-enter">
    <view v-if="flash" class="edge-flash" />
    <view class="slider__labels">
      <text>{{ labels?.[0] || "低" }}</text>
      <text>{{ rightLabel }}</text>
    </view>
    <view class="slider__emoji" :style="{ left: `calc(${percent}% - 16rpx)` }">{{ emoji }}</view>
    <view class="slider__tooltip" :style="{ left: `calc(${percent}% - 44rpx)` }">{{ tooltipLabel }}</view>
    <slider
      :value="current"
      :min="minVal"
      :max="maxVal"
      :step="step ?? 1"
      activeColor="#9B7ED8"
      backgroundColor="#EDE5F9"
      block-color="#ffffff"
      block-size="20"
      @changing="onInput"
      @change="onChange"
    />
  </view>
</template>

<style lang="scss" scoped>
.slider {
  position: relative;
  padding: 22rpx 8rpx 10rpx;
}

.slider__labels {
  display: flex;
  justify-content: space-between;
  font-size: 22rpx;
  color: $xc-muted;
}

.slider__emoji {
  position: absolute;
  top: 34rpx;
  font-size: 28rpx;
  transition: left 0.12s ease;
}

.slider__tooltip {
  position: absolute;
  top: 4rpx;
  padding: 4rpx 12rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(155, 126, 216, 0.2);
  color: $xc-purple-d;
  font-size: 20rpx;
  transition: left 0.12s ease;
}

.edge-flash {
  position: absolute;
  inset: 0;
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
    box-shadow: inset 0 0 0 0 rgba(155, 126, 216, 0.6);
  }
  100% {
    box-shadow: inset 0 0 0 14rpx rgba(155, 126, 216, 0);
  }
}
</style>

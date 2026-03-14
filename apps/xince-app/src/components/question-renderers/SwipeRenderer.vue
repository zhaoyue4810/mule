<script setup lang="ts">
import { SoundManager } from "@/shared/utils/sound-manager";

const props = defineProps<{
  modelValue: number | null;
  leftLabel?: string;
  rightLabel?: string;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: number];
}>();

function choose(value: number) {
  SoundManager.haptic(24);
  SoundManager.play("whoosh");
  emit("update:modelValue", value);
}
</script>

<template>
  <view class="swipe">
    <view
      class="swipe__side"
      :class="{ 'swipe__side--active': props.modelValue === 0 }"
      @tap="choose(0)"
    >
      <text class="swipe__label">{{ leftLabel || "不认同" }}</text>
    </view>
    <view
      class="swipe__side"
      :class="{ 'swipe__side--active': props.modelValue === 1 }"
      @tap="choose(1)"
    >
      <text class="swipe__label">{{ rightLabel || "认同" }}</text>
    </view>
  </view>
</template>

<style lang="scss" scoped>
.swipe {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16rpx;
}

.swipe__side {
  padding: 28rpx 20rpx;
  border-radius: 24rpx;
  text-align: center;
  background: rgba(255, 253, 248, 0.94);
  border: 2rpx solid rgba(43, 33, 24, 0.07);
}

.swipe__side--active {
  border-color: rgba(217, 111, 61, 0.45);
  background: rgba(255, 235, 221, 0.94);
}

.swipe__label {
  font-size: 28rpx;
}
</style>

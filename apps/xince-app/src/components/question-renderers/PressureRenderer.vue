<script setup lang="ts">
import { ref } from "vue";

const props = defineProps<{
  modelValue: number | null;
  min?: number;
  maxDuration?: number;
  step?: number;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: number];
}>();

const startedAt = ref(0);
const currentDuration = ref(props.modelValue ?? 0);

function onPressStart() {
  startedAt.value = Date.now();
}

function onPressEnd() {
  if (!startedAt.value) {
    return;
  }
  const maxDuration = props.maxDuration ?? 3000;
  const minDuration = props.min ?? 0;
  const rawDuration = Math.min(
    Math.max(Date.now() - startedAt.value, 0),
    maxDuration,
  );
  const step = props.step && props.step > 0 ? props.step : 1;
  const snapped =
    Math.round((rawDuration - minDuration) / step) * step + minDuration;
  const duration = Math.min(maxDuration, Math.max(minDuration, snapped));
  currentDuration.value = duration;
  startedAt.value = 0;
  emit("update:modelValue", duration);
}
</script>

<template>
  <view class="pressure">
    <view
      class="pressure__pad"
      @touchstart.prevent="onPressStart"
      @touchend.prevent="onPressEnd"
      @touchcancel.prevent="onPressEnd"
    >
      <text class="pressure__title">长按这里</text>
      <text class="pressure__hint">按住越久，数值越高</text>
    </view>
    <text class="pressure__value">当前记录：{{ currentDuration }} ms</text>
  </view>
</template>

<style lang="scss" scoped>
.pressure {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.pressure__pad {
  padding: 52rpx 20rpx;
  border-radius: 28rpx;
  text-align: center;
  background: linear-gradient(145deg, #ffd6b6, #ffefdf);
  box-shadow: $xc-shadow;
}

.pressure__title {
  display: block;
  font-size: 34rpx;
  font-weight: 700;
}

.pressure__hint,
.pressure__value {
  display: block;
  margin-top: 12rpx;
  font-size: 24rpx;
  color: $xc-muted;
}
</style>

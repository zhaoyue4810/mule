<script setup lang="ts">
import { ref } from "vue";

const props = defineProps<{
  modelValue: number | null;
  maxDuration?: number;
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
  const duration = Math.min(
    Math.max(Date.now() - startedAt.value, 0),
    props.maxDuration ?? 3000,
  );
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

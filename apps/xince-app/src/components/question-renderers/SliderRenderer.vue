<script setup lang="ts">
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

function onChange(event: { detail: { value: number } }) {
  emit("update:modelValue", Number(event.detail.value));
}
</script>

<template>
  <view class="slider">
    <view class="slider__labels">
      <text>{{ labels?.[0] || "低" }}</text>
      <text>{{ labels?.[1] || "高" }}</text>
    </view>
    <slider
      :value="modelValue ?? min ?? 1"
      :min="min ?? 1"
      :max="max ?? 5"
      :step="step ?? 1"
      activeColor="#d96f3d"
      backgroundColor="#f1ddd0"
      block-color="#bf5321"
      @change="onChange"
    />
    <text class="slider__value">当前选择：{{ modelValue ?? min ?? 1 }}</text>
  </view>
</template>

<style lang="scss" scoped>
.slider {
  padding: 20rpx 8rpx 8rpx;
}

.slider__labels {
  display: flex;
  justify-content: space-between;
  font-size: 22rpx;
  color: $xc-muted;
}

.slider__value {
  display: block;
  margin-top: 10rpx;
  font-size: 24rpx;
  color: $xc-accent;
}
</style>

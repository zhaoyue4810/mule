<script setup lang="ts">
const props = defineProps<{
  modelValue: { x: number; y: number } | null;
  xMin?: string;
  xMax?: string;
  yMin?: string;
  yMax?: string;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: { x: number; y: number }];
}>();

const presets = [
  { x: 0.15, y: 0.85 },
  { x: 0.5, y: 0.85 },
  { x: 0.85, y: 0.85 },
  { x: 0.15, y: 0.5 },
  { x: 0.5, y: 0.5 },
  { x: 0.85, y: 0.5 },
  { x: 0.15, y: 0.15 },
  { x: 0.5, y: 0.15 },
  { x: 0.85, y: 0.15 },
];

function isActive(point: { x: number; y: number }) {
  return (
    props.modelValue &&
    props.modelValue.x === point.x &&
    props.modelValue.y === point.y
  );
}
</script>

<template>
  <view class="plot">
    <view class="plot__top">
      <text>{{ yMax || "高" }}</text>
      <text>{{ xMax || "右" }}</text>
    </view>
    <view class="plot__board">
      <view
        v-for="point in presets"
        :key="`${point.x}-${point.y}`"
        class="plot__point"
        :class="{ 'plot__point--active': isActive(point) }"
        :style="{ left: `${point.x * 100}%`, top: `${(1 - point.y) * 100}%` }"
        @tap="emit('update:modelValue', point)"
      />
    </view>
    <view class="plot__bottom">
      <text>{{ yMin || "低" }}</text>
      <text>{{ xMin || "左" }}</text>
    </view>
  </view>
</template>

<style lang="scss" scoped>
.plot {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.plot__top,
.plot__bottom {
  display: flex;
  justify-content: space-between;
  font-size: 22rpx;
  color: $xc-muted;
}

.plot__board {
  position: relative;
  min-height: 360rpx;
  border-radius: 24rpx;
  background:
    linear-gradient(to right, transparent 49.5%, rgba(43, 33, 24, 0.12) 50%, transparent 50.5%),
    linear-gradient(to top, transparent 49.5%, rgba(43, 33, 24, 0.12) 50%, transparent 50.5%),
    rgba(255, 253, 248, 0.96);
  border: 2rpx solid rgba(43, 33, 24, 0.08);
}

.plot__point {
  position: absolute;
  width: 34rpx;
  height: 34rpx;
  margin-left: -17rpx;
  margin-top: -17rpx;
  border-radius: 50%;
  background: rgba(123, 108, 95, 0.35);
}

.plot__point--active {
  background: #d96f3d;
  box-shadow: 0 0 0 10rpx rgba(217, 111, 61, 0.18);
}
</style>

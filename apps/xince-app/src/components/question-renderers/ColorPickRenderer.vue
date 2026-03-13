<script setup lang="ts">
const props = defineProps<{
  modelValue: number | null;
  hueMap?: Record<string, unknown>;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: number];
}>();

const defaultHueMap = {
  0: "热情",
  60: "乐观",
  120: "平和",
  180: "沉稳",
  240: "忧郁",
  300: "神秘",
};

const entries = Object.entries(props.hueMap || defaultHueMap);

function swatchColor(hue: string) {
  return `hsl(${Number(hue)}, 78%, 62%)`;
}
</script>

<template>
  <view class="palette">
    <view
      v-for="[hue, label] in entries"
      :key="hue"
      class="palette__item"
      :class="{ 'palette__item--active': modelValue === Number(hue) }"
      @tap="emit('update:modelValue', Number(hue))"
    >
      <view class="palette__swatch" :style="{ background: swatchColor(hue) }" />
      <text class="palette__label">{{ String(label) }}</text>
    </view>
  </view>
</template>

<style lang="scss" scoped>
.palette {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16rpx;
}

.palette__item {
  padding: 18rpx 12rpx;
  border-radius: 22rpx;
  text-align: center;
  background: rgba(255, 253, 248, 0.94);
  border: 2rpx solid rgba(43, 33, 24, 0.07);
}

.palette__item--active {
  border-color: rgba(217, 111, 61, 0.45);
  box-shadow: $xc-shadow;
}

.palette__swatch {
  width: 72rpx;
  height: 72rpx;
  margin: 0 auto;
  border-radius: 50%;
}

.palette__label {
  display: block;
  margin-top: 12rpx;
  font-size: 22rpx;
}
</style>

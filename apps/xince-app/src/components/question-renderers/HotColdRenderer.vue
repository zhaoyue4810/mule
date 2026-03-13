<script setup lang="ts">
const props = defineProps<{
  modelValue: number | null;
  labels?: string[];
  emojis?: string[];
  minLabel?: string;
  maxLabel?: string;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: number];
}>();

const scaleValues = [1, 2, 3, 4, 5];
</script>

<template>
  <view class="hotcold">
    <view class="hotcold__labels">
      <text>{{ minLabel || "冰冷" }}</text>
      <text>{{ maxLabel || "火热" }}</text>
    </view>
    <view class="hotcold__row">
      <view
        v-for="value in scaleValues"
        :key="value"
        class="hotcold__item"
        :class="{ 'hotcold__item--active': modelValue === value }"
        @tap="emit('update:modelValue', value)"
      >
        <text class="hotcold__emoji">{{ emojis?.[value - 1] || "•" }}</text>
        <text class="hotcold__caption">{{ labels?.[value - 1] || value }}</text>
      </view>
    </view>
  </view>
</template>

<style lang="scss" scoped>
.hotcold {
  display: flex;
  flex-direction: column;
  gap: 14rpx;
}

.hotcold__labels {
  display: flex;
  justify-content: space-between;
  font-size: 22rpx;
  color: $xc-muted;
}

.hotcold__row {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 12rpx;
}

.hotcold__item {
  padding: 18rpx 8rpx;
  border-radius: 18rpx;
  text-align: center;
  background: rgba(255, 253, 248, 0.94);
  border: 2rpx solid rgba(43, 33, 24, 0.07);
}

.hotcold__item--active {
  border-color: rgba(217, 111, 61, 0.45);
  background: rgba(255, 235, 221, 0.94);
}

.hotcold__emoji {
  display: block;
  font-size: 30rpx;
}

.hotcold__caption {
  display: block;
  margin-top: 8rpx;
  font-size: 20rpx;
  color: $xc-muted;
}
</style>

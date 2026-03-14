<script setup lang="ts">
import { computed } from "vue";

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

function pick(value: number) {
  emit("update:modelValue", value);
}

const scaleValues = computed(() => {
  const min = Number.isFinite(props.min) ? Number(props.min) : 1;
  const max = Number.isFinite(props.max) ? Number(props.max) : 5;
  const step = Number.isFinite(props.step) && Number(props.step) > 0 ? Number(props.step) : 1;
  const values: number[] = [];
  for (let value = min; value <= max + step / 1000; value += step) {
    values.push(Number(value.toFixed(6)));
  }
  return values;
});
</script>

<template>
  <view class="stars">
    <view class="stars__row">
      <text
        v-for="value in scaleValues"
        :key="value"
        class="stars__item"
        :class="{ 'stars__item--active': modelValue === value }"
        @tap="pick(value)"
      >
        {{ "★".repeat(Math.max(1, Math.round(value))) }}
        <text class="stars__value">{{ value }}</text>
      </text>
    </view>
    <text class="stars__caption">
      {{
        labels && modelValue
          ? labels[Math.round(modelValue) - 1] || `评分 ${modelValue}`
          : "请选择星级"
      }}
    </text>
  </view>
</template>

<style lang="scss" scoped>
.stars {
  padding: 16rpx 0;
  text-align: center;
}

.stars__row {
  display: flex;
  justify-content: center;
  gap: 12rpx;
}

.stars__item {
  min-width: 98rpx;
  padding: 10rpx 12rpx;
  border-radius: 18rpx;
  text-align: center;
  font-size: 28rpx;
  color: #cdb9a8;
  background: rgba(255, 253, 248, 0.94);
  border: 2rpx solid rgba(43, 33, 24, 0.07);
}

.stars__item--active {
  color: #d96f3d;
  border-color: rgba(217, 111, 61, 0.45);
  background: rgba(255, 235, 221, 0.94);
}

.stars__value {
  margin-left: 6rpx;
  font-size: 20rpx;
  color: $xc-muted;
}

.stars__caption {
  display: block;
  margin-top: 14rpx;
  font-size: 24rpx;
  color: $xc-muted;
}
</style>

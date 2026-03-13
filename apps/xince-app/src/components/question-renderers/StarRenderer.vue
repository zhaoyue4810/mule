<script setup lang="ts">
const props = defineProps<{
  modelValue: number | null;
  max?: number;
  labels?: string[];
}>();

const emit = defineEmits<{
  "update:modelValue": [value: number];
}>();

function pick(value: number) {
  emit("update:modelValue", value);
}
</script>

<template>
  <view class="stars">
    <view class="stars__row">
      <text
        v-for="index in max ?? 5"
        :key="index"
        class="stars__item"
        :class="{ 'stars__item--active': (modelValue ?? 0) >= index }"
        @tap="pick(index)"
      >
        ★
      </text>
    </view>
    <text class="stars__caption">
      {{ labels && modelValue ? labels[modelValue - 1] || `评分 ${modelValue}` : "请选择星级" }}
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
  font-size: 54rpx;
  color: #e2d1c4;
}

.stars__item--active {
  color: #d96f3d;
}

.stars__caption {
  display: block;
  margin-top: 14rpx;
  font-size: 24rpx;
  color: $xc-muted;
}
</style>

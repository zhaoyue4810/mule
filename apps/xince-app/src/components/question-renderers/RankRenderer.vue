<script setup lang="ts">
import { computed } from "vue";

import type { PublishedQuestionPayload } from "@/shared/models/tests";

const props = defineProps<{
  modelValue: string[];
  question: PublishedQuestionPayload;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: string[]];
}>();

const currentOrder = computed(() => {
  if (props.modelValue.length) {
    return props.modelValue;
  }
  return props.question.options.map((option) => option.option_code || String(option.seq));
});

function move(index: number, offset: number) {
  const next = [...currentOrder.value];
  const target = index + offset;
  if (target < 0 || target >= next.length) {
    return;
  }
  [next[index], next[target]] = [next[target], next[index]];
  emit("update:modelValue", next);
}

function optionLabel(optionCode: string) {
  return (
    props.question.options.find(
      (option) => (option.option_code || String(option.seq)) === optionCode,
    )?.label || optionCode
  );
}
</script>

<template>
  <view class="rank">
    <view
      v-for="(optionCode, index) in currentOrder"
      :key="optionCode"
      class="rank__item"
    >
      <view class="rank__main">
        <text class="rank__index">{{ index + 1 }}</text>
        <text class="rank__label">{{ optionLabel(optionCode) }}</text>
      </view>
      <view class="rank__actions">
        <button class="rank__button" :disabled="index === 0" @tap="move(index, -1)">上移</button>
        <button
          class="rank__button"
          :disabled="index === currentOrder.length - 1"
          @tap="move(index, 1)"
        >
          下移
        </button>
      </view>
    </view>
  </view>
</template>

<style lang="scss" scoped>
.rank {
  display: flex;
  flex-direction: column;
  gap: 14rpx;
}

.rank__item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
  padding: 22rpx 20rpx;
  border-radius: 22rpx;
  background: rgba(255, 253, 248, 0.94);
  border: 2rpx solid rgba(43, 33, 24, 0.07);
}

.rank__main {
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.rank__index {
  width: 48rpx;
  height: 48rpx;
  border-radius: 50%;
  text-align: center;
  line-height: 48rpx;
  background: rgba(217, 111, 61, 0.14);
  color: $xc-accent;
  font-size: 24rpx;
  font-weight: 700;
}

.rank__label {
  font-size: 26rpx;
}

.rank__actions {
  display: flex;
  gap: 10rpx;
}

.rank__button {
  padding: 0 20rpx;
  border-radius: 999rpx;
  background: rgba(255, 238, 224, 0.9);
  color: $xc-accent;
  font-size: 22rpx;
}
</style>

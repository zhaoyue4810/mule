<script setup lang="ts">
import type { PublishedQuestionPayload } from "@/shared/models/tests";

defineProps<{
  modelValue: string;
  question: PublishedQuestionPayload;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: string];
}>();
</script>

<template>
  <view class="fallback">
    <view
      v-for="option in question.options"
      :key="option.option_code || option.seq"
      class="fallback__item"
      :class="{ 'fallback__item--active': modelValue === (option.option_code || String(option.seq)) }"
      @tap="emit('update:modelValue', option.option_code || String(option.seq))"
    >
      <text>{{ option.label }}</text>
    </view>
  </view>
</template>

<style lang="scss" scoped>
.fallback {
  display: flex;
  flex-direction: column;
  gap: 14rpx;
}

.fallback__item {
  padding: 24rpx 20rpx;
  border-radius: 20rpx;
  background: rgba(255, 253, 248, 0.94);
  border: 2rpx solid rgba(43, 33, 24, 0.07);
}

.fallback__item--active {
  border-color: rgba(217, 111, 61, 0.45);
  background: rgba(255, 235, 221, 0.94);
}
</style>

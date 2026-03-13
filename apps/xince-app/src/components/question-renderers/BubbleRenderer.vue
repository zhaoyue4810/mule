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
  <view class="choices">
    <view
      v-for="option in question.options"
      :key="option.option_code || option.seq"
      class="choice"
      :class="{ 'choice--active': modelValue === (option.option_code || String(option.seq)) }"
      @tap="emit('update:modelValue', option.option_code || String(option.seq))"
    >
      <text class="choice__label">{{ option.label }}</text>
    </view>
  </view>
</template>

<style lang="scss" scoped>
.choices {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16rpx;
}

.choice {
  padding: 24rpx 20rpx;
  border-radius: 22rpx;
  background: rgba(255, 253, 248, 0.94);
  border: 2rpx solid rgba(43, 33, 24, 0.07);
}

.choice--active {
  border-color: rgba(217, 111, 61, 0.45);
  background: rgba(255, 235, 221, 0.94);
}

.choice__label {
  font-size: 28rpx;
  line-height: 1.6;
}
</style>

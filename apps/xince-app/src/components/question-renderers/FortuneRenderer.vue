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
  <view class="fortune">
    <view
      v-for="option in question.options"
      :key="option.option_code || option.seq"
      class="fortune__sector"
      :class="{ 'fortune__sector--active': modelValue === (option.option_code || String(option.seq)) }"
      @tap="emit('update:modelValue', option.option_code || String(option.seq))"
    >
      <text class="fortune__label">{{ option.label }}</text>
    </view>
  </view>
</template>

<style lang="scss" scoped>
.fortune {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14rpx;
}

.fortune__sector {
  padding: 28rpx 20rpx;
  border-radius: 26rpx;
  background:
    radial-gradient(circle at top, rgba(255, 244, 231, 0.98), rgba(255, 223, 196, 0.92)),
    #fff8f1;
  border: 2rpx solid rgba(217, 111, 61, 0.1);
  text-align: center;
}

.fortune__sector--active {
  border-color: rgba(217, 111, 61, 0.45);
  box-shadow: $xc-shadow;
}

.fortune__label {
  font-size: 26rpx;
  line-height: 1.6;
}
</style>

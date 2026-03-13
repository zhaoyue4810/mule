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
  <view class="tarot">
    <view
      v-for="option in question.options"
      :key="option.option_code || option.seq"
      class="tarot__card"
      :class="{ 'tarot__card--active': modelValue === (option.option_code || String(option.seq)) }"
      @tap="emit('update:modelValue', option.option_code || String(option.seq))"
    >
      <text class="tarot__glyph">{{ option.emoji || "✦" }}</text>
      <text class="tarot__label">{{ option.label }}</text>
    </view>
  </view>
</template>

<style lang="scss" scoped>
.tarot {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14rpx;
}

.tarot__card {
  min-height: 220rpx;
  padding: 24rpx 16rpx;
  border-radius: 24rpx;
  text-align: center;
  background: linear-gradient(160deg, #fff8f1, #f6eadf);
  border: 2rpx solid rgba(123, 108, 95, 0.14);
}

.tarot__card--active {
  border-color: rgba(217, 111, 61, 0.45);
  box-shadow: $xc-shadow;
}

.tarot__glyph {
  display: block;
  margin-top: 18rpx;
  font-size: 40rpx;
}

.tarot__label {
  display: block;
  margin-top: 26rpx;
  font-size: 24rpx;
  line-height: 1.6;
}
</style>

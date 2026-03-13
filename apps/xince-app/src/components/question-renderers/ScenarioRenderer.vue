<script setup lang="ts">
import { computed } from "vue";

import type { PublishedQuestionPayload } from "@/shared/models/tests";

const props = defineProps<{
  modelValue: string;
  question: PublishedQuestionPayload;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: string];
}>();

const config = computed<Record<string, unknown>>(
  () => (props.question.config as Record<string, unknown> | null) || {},
);
</script>

<template>
  <view class="scenario">
    <view class="scenario__hero">
      <text class="scenario__emoji">{{ String(config.scene_emoji || "🎭") }}</text>
      <text class="scenario__text">{{ String(config.scene_text || question.question_text) }}</text>
      <text class="scenario__tip">{{ String(config.tip_text || "选择你最自然的反应") }}</text>
    </view>
    <view class="scenario__options">
      <view
        v-for="option in question.options"
        :key="option.option_code || option.seq"
        class="scenario__option"
        :class="{ 'scenario__option--active': modelValue === (option.option_code || String(option.seq)) }"
        @tap="emit('update:modelValue', option.option_code || String(option.seq))"
      >
        <text class="scenario__label">{{ option.label }}</text>
      </view>
    </view>
  </view>
</template>

<style lang="scss" scoped>
.scenario {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.scenario__hero {
  padding: 28rpx 24rpx;
  border-radius: 24rpx;
  background: linear-gradient(145deg, rgba(255, 241, 223, 0.98), rgba(255, 226, 206, 0.92));
}

.scenario__emoji {
  display: block;
  font-size: 34rpx;
}

.scenario__text {
  display: block;
  margin-top: 14rpx;
  font-size: 30rpx;
  line-height: 1.6;
  font-weight: 600;
}

.scenario__tip {
  display: block;
  margin-top: 12rpx;
  font-size: 22rpx;
  color: $xc-muted;
}

.scenario__options {
  display: flex;
  flex-direction: column;
  gap: 14rpx;
}

.scenario__option {
  padding: 24rpx 20rpx;
  border-radius: 20rpx;
  background: rgba(255, 253, 248, 0.94);
  border: 2rpx solid rgba(43, 33, 24, 0.07);
}

.scenario__option--active {
  border-color: rgba(217, 111, 61, 0.45);
  background: rgba(255, 235, 221, 0.94);
}

.scenario__label {
  font-size: 26rpx;
  line-height: 1.7;
}
</style>

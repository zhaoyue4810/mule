<script setup lang="ts">
import { ref } from "vue";

import type { PublishedQuestionPayload } from "@/shared/models/tests";

defineProps<{
  modelValue: string;
  question: PublishedQuestionPayload;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: string];
}>();

const revealed = ref(false);

function reveal() {
  revealed.value = true;
}
</script>

<template>
  <view class="scratch">
    <view class="scratch__card" :class="{ 'scratch__card--revealed': revealed }" @tap="reveal">
      <text class="scratch__title">{{ revealed ? "已揭晓" : "轻触刮开奖面" }}</text>
      <text class="scratch__hint">
        {{ revealed ? "现在选择最打动你的结果。" : "先点一下，再从下面选择。" }}
      </text>
    </view>
    <view class="scratch__options" v-if="revealed">
      <view
        v-for="option in question.options"
        :key="option.option_code || option.seq"
        class="scratch__option"
        :class="{ 'scratch__option--active': modelValue === (option.option_code || String(option.seq)) }"
        @tap="emit('update:modelValue', option.option_code || String(option.seq))"
      >
        <text>{{ option.label }}</text>
      </view>
    </view>
  </view>
</template>

<style lang="scss" scoped>
.scratch {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.scratch__card {
  padding: 48rpx 24rpx;
  border-radius: 28rpx;
  text-align: center;
  background:
    linear-gradient(145deg, rgba(188, 188, 188, 0.95), rgba(224, 224, 224, 0.9)),
    #ddd;
}

.scratch__card--revealed {
  background:
    radial-gradient(circle at top, rgba(255, 240, 219, 0.98), rgba(255, 213, 179, 0.92)),
    #fff5ec;
}

.scratch__title {
  display: block;
  font-size: 34rpx;
  font-weight: 700;
}

.scratch__hint {
  display: block;
  margin-top: 12rpx;
  font-size: 24rpx;
  color: $xc-muted;
}

.scratch__options {
  display: flex;
  flex-direction: column;
  gap: 14rpx;
}

.scratch__option {
  padding: 24rpx 20rpx;
  border-radius: 20rpx;
  background: rgba(255, 253, 248, 0.94);
  border: 2rpx solid rgba(43, 33, 24, 0.07);
}

.scratch__option--active {
  border-color: rgba(217, 111, 61, 0.45);
  background: rgba(255, 235, 221, 0.94);
}
</style>

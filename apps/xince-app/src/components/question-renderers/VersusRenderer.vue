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

const first = computed(() => props.question.options[0]);
const second = computed(() => props.question.options[1]);
</script>

<template>
  <view class="versus">
    <view
      v-if="first"
      class="versus__card versus__card--top"
      :class="{ 'versus__card--active': modelValue === (first.option_code || String(first.seq)) }"
      @tap="emit('update:modelValue', first.option_code || String(first.seq))"
    >
      <text class="versus__label">{{ first.label }}</text>
    </view>
    <text class="versus__divider">VS</text>
    <view
      v-if="second"
      class="versus__card versus__card--bottom"
      :class="{ 'versus__card--active': modelValue === (second.option_code || String(second.seq)) }"
      @tap="emit('update:modelValue', second.option_code || String(second.seq))"
    >
      <text class="versus__label">{{ second.label }}</text>
    </view>
  </view>
</template>

<style lang="scss" scoped>
.versus {
  display: flex;
  flex-direction: column;
  gap: 14rpx;
}

.versus__card {
  padding: 28rpx 24rpx;
  border-radius: 24rpx;
  color: #fffaf3;
}

.versus__card--top {
  background: linear-gradient(145deg, #cd7d5d, #a34532);
}

.versus__card--bottom {
  background: linear-gradient(145deg, #8067c6, #56449d);
}

.versus__card--active {
  transform: scale(1.01);
  box-shadow: $xc-shadow;
}

.versus__divider {
  text-align: center;
  font-size: 24rpx;
  color: $xc-muted;
}

.versus__label {
  font-size: 30rpx;
  line-height: 1.55;
}
</style>

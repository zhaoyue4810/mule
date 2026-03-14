<script setup lang="ts">
import { ref } from "vue";

import type { PublishedQuestionPayload } from "@/shared/models/tests";
import { haptic, playSound } from "@/shared/utils/sound-manager";

defineProps<{
  modelValue: string;
  question: PublishedQuestionPayload;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: string];
}>();

const flash = ref(false);

function choose(value: string) {
  playSound("chime");
  haptic(15);
  flash.value = true;
  setTimeout(() => {
    flash.value = false;
  }, 300);
  emit("update:modelValue", value);
}
</script>

<template>
  <view class="fallback q-enter">
    <view v-if="flash" class="edge-flash" />
    <view
      v-for="option in question.options"
      :key="option.option_code || option.seq"
      class="fallback__item"
      :class="{ 'fallback__item--active': modelValue === (option.option_code || String(option.seq)) }"
      @tap="choose(option.option_code || String(option.seq))"
    >
      <text>{{ option.label }}</text>
    </view>
  </view>
</template>

<style lang="scss" scoped>
.fallback {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 14rpx;
}

.fallback__item {
  padding: 24rpx 20rpx;
  border-radius: 20rpx;
  background: rgba(255, 253, 248, 0.94);
  border: 2rpx solid rgba(58, 46, 66, 0.07);
}

.fallback__item--active {
  border-color: rgba(155, 126, 216, 0.45);
  background: rgba(255, 235, 221, 0.94);
}

.edge-flash {
  position: absolute;
  inset: 0;
  animation: edgeFlash 0.3s ease;
}

.q-enter {
  animation: qEnter 0.4s $xc-ease both;
}

@keyframes qEnter {
  from {
    opacity: 0;
    transform: translateX(30px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes edgeFlash {
  from {
    box-shadow: inset 0 0 0 0 rgba(155, 126, 216, 0.55);
  }
  to {
    box-shadow: inset 0 0 0 14rpx rgba(155, 126, 216, 0);
  }
}
</style>

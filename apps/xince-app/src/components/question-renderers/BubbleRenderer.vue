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

function pick(value: string) {
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
  <view class="choices q-enter">
    <view v-if="flash" class="edge-flash" />
    <view
      v-for="option in question.options"
      :key="option.option_code || option.seq"
      class="choice"
      :class="{ 'choice--active': modelValue === (option.option_code || String(option.seq)) }"
      @tap="pick(option.option_code || String(option.seq))"
    >
      <text class="choice__emoji">{{ option.emoji || "🫧" }}</text>
      <text class="choice__label">{{ option.label }}</text>
    </view>
  </view>
</template>

<style lang="scss" scoped>
.choices {
  position: relative;
  display: flex;
  flex-wrap: wrap;
  gap: 18rpx;
  justify-content: center;
}

.choice {
  width: 180rpx;
  height: 180rpx;
  border-radius: 50%;
  background: $xc-purple-p;
  border: 2rpx solid rgba(155, 126, 216, 0.2);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  transform: scale(0.92);
  opacity: 0.5;
  transition: all 0.24s $xc-ease;
}

.choice--active {
  transform: scale(1.15);
  opacity: 1;
  color: $xc-white;
  background: linear-gradient(135deg, $xc-purple, $xc-pink);
  box-shadow: 0 0 24rpx rgba(155, 126, 216, 0.35);
  animation: bubblePop 0.3s $xc-spring both;
}

.choice__emoji {
  font-size: 34rpx;
}

.choice__label {
  margin-top: 8rpx;
  width: 120rpx;
  text-align: center;
  font-size: 22rpx;
  line-height: 1.45;
}

.edge-flash {
  position: absolute;
  inset: 0;
  border-radius: 24rpx;
  pointer-events: none;
  animation: edgeFlash 0.3s ease;
}

.q-enter {
  animation: qEnter 0.4s $xc-ease both;
}

@keyframes bubblePop {
  0% {
    transform: scale(0.8);
  }
  100% {
    transform: scale(1.15);
  }
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
  0% {
    box-shadow: inset 0 0 0 0 rgba(155, 126, 216, 0.6);
  }
  100% {
    box-shadow: inset 0 0 0 16rpx rgba(155, 126, 216, 0);
  }
}
</style>

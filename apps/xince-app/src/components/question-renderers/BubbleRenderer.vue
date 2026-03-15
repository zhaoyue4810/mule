<script setup lang="ts">
import { computed, ref } from "vue";

import type { PublishedQuestionPayload } from "@/shared/models/tests";
import { haptic, playSound } from "@/shared/utils/sound-manager";

const props = defineProps<{
  modelValue: string;
  question: PublishedQuestionPayload;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: string];
}>();

const flash = ref(false);
const hasSelection = computed(() => Boolean(props.modelValue));

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
      v-for="(option, index) in question.options"
      :key="option.option_code || option.seq"
      class="choice"
      :class="[
        `choice--c${index % 4}`,
        {
          'choice--active': modelValue === (option.option_code || String(option.seq)),
          'choice--dimmed':
            hasSelection && modelValue !== (option.option_code || String(option.seq)),
        },
      ]"
      @tap="pick(option.option_code || String(option.seq))"
    >
      <view class="choice__gloss" />
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
  gap: 16rpx;
  justify-content: center;
  align-content: center;
  min-height: 420rpx;
}

.choice {
  position: relative;
  width: calc(50% - 10rpx);
  aspect-ratio: 1;
  border-radius: 50%;
  overflow: hidden;
  border: 2rpx solid rgba(155, 126, 216, 0.12);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8rpx;
  padding: 18rpx;
  transform: scale(1);
  opacity: 1;
  transition: all 0.4s $xc-spring;
}

.choice--c0 {
  background: linear-gradient(135deg, $xc-purple-p, #ddd5f7);
  border-color: rgba(201, 181, 240, 0.8);
}

.choice--c1 {
  background: linear-gradient(135deg, $xc-pink-p, #f9d0e0);
  border-color: rgba(244, 165, 191, 0.8);
}

.choice--c2 {
  background: linear-gradient(135deg, $xc-peach-p, #fcddc8);
  border-color: rgba(248, 201, 181, 0.8);
}

.choice--c3 {
  background: linear-gradient(135deg, $xc-mint-p, #c5ebe0);
  border-color: rgba(168, 221, 208, 0.88);
}

.choice--active {
  transform: scale(1.08);
  opacity: 1;
  color: $xc-ink;
  border-color: $xc-purple;
  box-shadow:
    0 0 24rpx rgba(155, 126, 216, 0.28),
    0 10rpx 26rpx rgba(155, 126, 216, 0.16);
  animation: bubblePop 0.5s $xc-spring both;
}

.choice--dimmed {
  transform: scale(0.74);
  opacity: 0.36;
}

.choice__gloss {
  position: absolute;
  inset: 0;
  border-radius: inherit;
  background: radial-gradient(circle at 35% 35%, rgba(255, 255, 255, 0.66), transparent 60%);
  pointer-events: none;
}

.choice__emoji {
  position: relative;
  z-index: 1;
  font-size: 38rpx;
  transition: transform 0.3s $xc-spring;
}

.choice__label {
  position: relative;
  z-index: 1;
  width: 128rpx;
  text-align: center;
  font-size: 22rpx;
  font-weight: 700;
  line-height: 1.38;
}

.choice--active .choice__emoji {
  transform: scale(1.2);
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
    transform: scale(1);
  }
  40% {
    transform: scale(1.18);
  }
  100% {
    transform: scale(1.08);
  }

}

@keyframes bubbleShrink {
  to {
    transform: scale(0.5);
    opacity: 0;
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

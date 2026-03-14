<script setup lang="ts">
import { computed, ref, watch } from "vue";

import type { PublishedQuestionPayload } from "@/shared/models/tests";
import { haptic, playSound } from "@/shared/utils/sound-manager";

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
const typedText = ref("");
const flash = ref(false);
let typingTimer: ReturnType<typeof setTimeout> | null = null;

function typeText() {
  const full = String(config.value.scene_text || props.question.question_text);
  typedText.value = "";
  let i = 0;
  const tick = () => {
    i += 1;
    typedText.value = full.slice(0, i);
    if (i < full.length) {
      typingTimer = setTimeout(tick, 22);
    }
  };
  tick();
}

function choose(value: string) {
  playSound("chime");
  haptic(15);
  flash.value = true;
  setTimeout(() => {
    flash.value = false;
  }, 300);
  emit("update:modelValue", value);
}

watch(
  () => props.question.seq,
  () => {
    if (typingTimer) {
      clearTimeout(typingTimer);
    }
    typeText();
  },
  { immediate: true },
);
</script>

<template>
  <view class="scenario q-enter">
    <view v-if="flash" class="edge-flash" />
    <view class="scenario__hero">
      <text class="scenario__emoji">{{ String(config.scene_emoji || "🎭") }}</text>
      <text class="scenario__text">{{ typedText }}</text>
      <text class="scenario__tip">{{ String(config.tip_text || "想象一下当下场景…") }}</text>
    </view>
    <view class="scenario__options">
      <view
        v-for="option in question.options"
        :key="option.option_code || option.seq"
        class="scenario__option"
        :class="{ 'scenario__option--active': modelValue === (option.option_code || String(option.seq)) }"
        @tap="choose(option.option_code || String(option.seq))"
      >
        <text class="scenario__label">{{ option.label }}</text>
      </view>
    </view>
    <view class="scenario__bubble">小测提醒：顺着第一直觉更容易找到真实答案。</view>
  </view>
</template>

<style lang="scss" scoped>
.scenario {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 14rpx;
}

.scenario__hero {
  padding: 24rpx;
  border-radius: 24rpx;
  @include glass;
}

.scenario__emoji {
  display: block;
  font-size: 34rpx;
}

.scenario__text {
  margin-top: 10rpx;
  display: block;
  font-size: 28rpx;
  line-height: 1.6;
}

.scenario__tip {
  display: block;
  margin-top: 10rpx;
  font-size: 22rpx;
  color: $xc-muted;
}

.scenario__options {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.scenario__option {
  padding: 22rpx 20rpx;
  border-radius: 18rpx;
  background: rgba(255, 255, 255, 0.9);
  border: 2rpx solid rgba(155, 126, 216, 0.1);
  box-shadow: $xc-sh-sm;
  transition: all 0.22s $xc-ease;
}

.scenario__option--active {
  transform: scale(1.02);
  border-color: rgba(155, 126, 216, 0.45);
  box-shadow: 0 0 18rpx rgba(155, 126, 216, 0.28);
}

.scenario__label {
  font-size: 25rpx;
}

.scenario__bubble {
  align-self: flex-start;
  font-size: 21rpx;
  color: $xc-muted;
  background: rgba(255, 255, 255, 0.88);
  padding: 10rpx 16rpx;
  border-radius: 16rpx;
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
    box-shadow: inset 0 0 0 0 rgba(155, 126, 216, 0.58);
  }
  to {
    box-shadow: inset 0 0 0 14rpx rgba(155, 126, 216, 0);
  }
}
</style>

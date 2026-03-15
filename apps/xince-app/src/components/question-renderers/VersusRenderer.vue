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
const first = computed(() => props.question.options[0]);
const second = computed(() => props.question.options[1]);

function choose(value: string) {
  playSound("whoosh");
  haptic(15);
  flash.value = true;
  setTimeout(() => {
    flash.value = false;
  }, 300);
  emit("update:modelValue", value);
}
</script>

<template>
  <view class="versus q-enter">
    <view v-if="flash" class="edge-flash" />
    <view class="versus__zone">
      <view
        v-if="first"
        class="versus__option versus__option--top"
        :class="{
          'versus__option--selected': modelValue === (first.option_code || String(first.seq)),
          'versus__option--dimmed': modelValue && modelValue !== (first.option_code || String(first.seq)),
        }"
        @tap="choose(first.option_code || String(first.seq))"
      >
        <view class="versus__content">
          <text class="versus__emoji">{{ first.emoji || "🌤️" }}</text>
          <text class="versus__label">{{ first.label }}</text>
        </view>
      </view>
      <view class="versus__badge">VS</view>
      <view
        v-if="second"
        class="versus__option versus__option--bottom"
        :class="{
          'versus__option--selected': modelValue === (second.option_code || String(second.seq)),
          'versus__option--dimmed': modelValue && modelValue !== (second.option_code || String(second.seq)),
        }"
        @tap="choose(second.option_code || String(second.seq))"
      >
        <view class="versus__content">
          <text class="versus__emoji">{{ second.emoji || "🌊" }}</text>
          <text class="versus__label">{{ second.label }}</text>
        </view>
      </view>
    </view>
  </view>
</template>

<style lang="scss" scoped>
.versus {
  position: relative;
  border-radius: 28rpx;
  overflow: hidden;
}

.versus__zone {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 0;
  min-height: 60vh;
}

.versus__option {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  transition: all 0.3s ease;
  min-height: 250rpx;
}

.versus__option--top {
  border-radius: 0 0 24rpx 24rpx;
  background: linear-gradient(135deg, #EDE5F9, #FDE6EF);
}

.versus__option--bottom {
  border-radius: 24rpx 24rpx 0 0;
  background: linear-gradient(135deg, #E2F5EF, #EDE5F9);
}

.versus__content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14rpx;
  text-align: center;
  padding: 28rpx 36rpx;
}

.versus__emoji {
  font-size: 56rpx;
  line-height: 1;
}

.versus__label {
  font-size: 32rpx;
  font-weight: 700;
  color: $xc-purple-d;
  line-height: 1.45;
}

.versus__option--selected {
  transform: scale(1.03);
  filter: brightness(1.05);
}

.versus__option--dimmed {
  transform: scale(0.97);
  opacity: 0.6;
  filter: brightness(0.9);
}

.versus__badge {
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  z-index: 2;
  width: 64rpx;
  height: 64rpx;
  border-radius: 50%;
  background: linear-gradient(135deg, #9B7ED8, #E8729A);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: 900;
  box-shadow: 0 0 16rpx rgba(155, 126, 216, 0.3);
  animation: pulse 2s infinite;
}

.edge-flash {
  position: absolute;
  inset: 0;
  pointer-events: none;
  animation: edgeFlash 0.3s ease;
  z-index: 3;
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

@keyframes pulse {
  0%,
  100% {
    transform: translate(-50%, -50%) scale(1);
  }
  50% {
    transform: translate(-50%, -50%) scale(1.08);
  }
}

@keyframes edgeFlash {
  from {
    box-shadow: inset 0 0 0 0 rgba(155, 126, 216, 0.65);
  }
  to {
    box-shadow: inset 0 0 0 18rpx rgba(155, 126, 216, 0);
  }
}
</style>

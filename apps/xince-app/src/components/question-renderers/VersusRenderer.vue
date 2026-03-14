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
    <view
      v-if="first"
      class="versus__half versus__half--top"
      :class="{
        'versus__half--active': modelValue === (first.option_code || String(first.seq)),
        'versus__half--dim': modelValue && modelValue !== (first.option_code || String(first.seq)),
      }"
      @tap="choose(first.option_code || String(first.seq))"
    >
      <text>{{ first.label }}</text>
    </view>
    <view class="versus__badge">VS</view>
    <view
      v-if="second"
      class="versus__half versus__half--bottom"
      :class="{
        'versus__half--active': modelValue === (second.option_code || String(second.seq)),
        'versus__half--dim': modelValue && modelValue !== (second.option_code || String(second.seq)),
      }"
      @tap="choose(second.option_code || String(second.seq))"
    >
      <text>{{ second.label }}</text>
    </view>
  </view>
</template>

<style lang="scss" scoped>
.versus {
  position: relative;
  border-radius: 28rpx;
  overflow: hidden;
  min-height: 480rpx;
}

.versus__half {
  height: 40vh;
  min-height: 220rpx;
  max-height: 300rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32rpx;
  font-weight: 700;
  color: $xc-white;
  transition: transform 0.24s $xc-ease, opacity 0.24s $xc-ease;
}

.versus__half--top {
  background: linear-gradient(160deg, $xc-purple, $xc-pink);
}

.versus__half--bottom {
  background: linear-gradient(160deg, $xc-mint, #6ea5d3);
}

.versus__half--active {
  transform: scale(1.05);
}

.versus__half--dim {
  opacity: 0.45;
  transform: scale(0.96);
}

.versus__badge {
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  width: 92rpx;
  height: 92rpx;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.92);
  display: flex;
  align-items: center;
  justify-content: center;
  color: $xc-purple-d;
  font-weight: 800;
  animation: pulse 1.8s infinite;
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

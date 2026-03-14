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

const revealed = ref<string[]>([]);
const flash = ref(false);
const cardCount = computed(() => Number((props.question.config as Record<string, unknown> | null)?.cardCount || 3));

function choose(value: string) {
  if (!revealed.value.includes(value)) {
    revealed.value.push(value);
    playSound("ambient");
  }
  haptic(15);
  flash.value = true;
  setTimeout(() => {
    flash.value = false;
  }, 300);
  setTimeout(() => {
    emit("update:modelValue", value);
  }, 300);
}
</script>

<template>
  <view class="tarot q-enter">
    <view v-if="flash" class="edge-flash" />
    <view
      v-for="option in question.options.slice(0, cardCount)"
      :key="option.option_code || option.seq"
      class="tarot__card"
      :class="{
        'tarot__card--flipped': revealed.includes(option.option_code || String(option.seq)),
        'tarot__card--dim': modelValue && modelValue !== (option.option_code || String(option.seq)),
      }"
      @tap="choose(option.option_code || String(option.seq))"
    >
      <view class="tarot__face tarot__face--back">✶</view>
      <view class="tarot__face tarot__face--front">
        <text class="tarot__glyph">{{ option.emoji || "🔮" }}</text>
        <text class="tarot__label">{{ option.label }}</text>
      </view>
    </view>
  </view>
</template>

<style lang="scss" scoped>
.tarot {
  position: relative;
  display: flex;
  gap: 14rpx;
  justify-content: center;
}

.tarot__card {
  width: 184rpx;
  height: 270rpx;
  position: relative;
  transform-style: preserve-3d;
  transition: transform 0.6s ease, opacity 0.25s ease;
}

.tarot__card--flipped {
  transform: rotateY(180deg);
}

.tarot__card--dim {
  opacity: 0.5;
  transform: scale(0.9);
}

.tarot__face {
  position: absolute;
  inset: 0;
  border-radius: 20rpx;
  backface-visibility: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
}

.tarot__face--back {
  background:
    repeating-linear-gradient(45deg, rgba(124, 93, 191, 0.25) 0 8rpx, rgba(233, 221, 255, 0.3) 8rpx 16rpx),
    linear-gradient(145deg, rgba(58, 46, 66, 0.9), rgba(124, 93, 191, 0.85));
  color: $xc-white;
  font-size: 48rpx;
}

.tarot__face--front {
  transform: rotateY(180deg);
  @include glass-strong;
}

.tarot__glyph {
  font-size: 42rpx;
}

.tarot__label {
  margin-top: 14rpx;
  padding: 0 8rpx;
  text-align: center;
  font-size: 22rpx;
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
    box-shadow: inset 0 0 0 0 rgba(124, 93, 191, 0.6);
  }
  to {
    box-shadow: inset 0 0 0 14rpx rgba(124, 93, 191, 0);
  }
}
</style>

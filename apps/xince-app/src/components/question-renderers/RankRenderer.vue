<script setup lang="ts">
import { computed, ref } from "vue";

import type { PublishedQuestionPayload } from "@/shared/models/tests";
import { haptic, playSound } from "@/shared/utils/sound-manager";

const props = defineProps<{
  modelValue: string[];
  question: PublishedQuestionPayload;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: string[]];
}>();

const dragging = ref<string>("");
const flash = ref(false);

const currentOrder = computed(() => {
  if (props.modelValue.length) {
    return props.modelValue;
  }
  return props.question.options.map((option) => option.option_code || String(option.seq));
});

function optionLabel(optionCode: string) {
  return (
    props.question.options.find((option) => (option.option_code || String(option.seq)) === optionCode)?.label || optionCode
  );
}

function reorder(fromCode: string, toCode: string) {
  const next = [...currentOrder.value];
  const from = next.indexOf(fromCode);
  const to = next.indexOf(toCode);
  if (from === -1 || to === -1 || from === to) return;
  const [moved] = next.splice(from, 1);
  next.splice(to, 0, moved);
  playSound("whoosh");
  haptic(15);
  flash.value = true;
  setTimeout(() => (flash.value = false), 300);
  emit("update:modelValue", next);
}

function onStart(code: string) {
  dragging.value = code;
}

function onEnd() {
  dragging.value = "";
}
</script>

<template>
  <view class="rank q-enter">
    <view v-if="flash" class="edge-flash" />
    <view
      v-for="(optionCode, index) in currentOrder"
      :key="optionCode"
      class="rank__item"
      :class="{ 'rank__item--dragging': dragging === optionCode }"
      @touchstart.stop="onStart(optionCode)"
      @touchend.stop="onEnd"
      @touchmove.stop.prevent
      @tap="dragging && dragging !== optionCode && reorder(dragging, optionCode)"
    >
      <view class="rank__main">
        <text class="rank__index">{{ index + 1 }}</text>
        <text class="rank__handle">≡</text>
        <text class="rank__label">{{ optionLabel(optionCode) }}</text>
      </view>
    </view>
  </view>
</template>

<style lang="scss" scoped>
.rank {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.rank__item {
  padding: 20rpx;
  border-radius: 18rpx;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(155, 126, 216, 0.1);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.rank__item--dragging {
  transform: scale(1.05);
  box-shadow: $xc-sh-md;
}

.rank__main {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.rank__index {
  width: 44rpx;
  height: 44rpx;
  border-radius: 50%;
  background: rgba(155, 126, 216, 0.14);
  text-align: center;
  line-height: 44rpx;
  color: $xc-purple-d;
  font-size: 22rpx;
  font-weight: 700;
}

.rank__handle {
  color: $xc-muted;
  font-size: 24rpx;
}

.rank__label {
  font-size: 24rpx;
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

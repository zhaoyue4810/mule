<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from "vue";

const props = withDefaults(
  defineProps<{
    text: string;
    duration?: number;
    persistent?: boolean;
    typing?: boolean;
  }>(),
  {
    duration: 2500,
    persistent: false,
    typing: true,
  },
);

const visible = ref(false);
const fading = ref(false);
const typedText = ref("");
let typingTimer: ReturnType<typeof setTimeout> | null = null;
let hideTimer: ReturnType<typeof setTimeout> | null = null;

const shouldRender = computed(() => Boolean(props.text) && visible.value);

function clearTimers() {
  if (typingTimer) {
    clearTimeout(typingTimer);
    typingTimer = null;
  }
  if (hideTimer) {
    clearTimeout(hideTimer);
    hideTimer = null;
  }
}

function scheduleTyping() {
  typedText.value = "";
  const fullText = props.text || "";
  if (!props.typing) {
    typedText.value = fullText;
    return;
  }

  let index = 0;
  const type = () => {
    index += 1;
    typedText.value = fullText.slice(0, index);
    if (index < fullText.length) {
      typingTimer = setTimeout(type, 36);
    }
  };
  type();
}

function showBubble() {
  clearTimers();
  fading.value = false;
  visible.value = Boolean(props.text);
  scheduleTyping();
  if (!props.persistent && props.text) {
    hideTimer = setTimeout(() => {
      fading.value = true;
      setTimeout(() => {
        visible.value = false;
        fading.value = false;
      }, 220);
    }, props.duration);
  }
}

watch(
  () => [props.text, props.duration, props.persistent, props.typing] as const,
  () => {
    showBubble();
  },
  { immediate: true },
);

onBeforeUnmount(() => {
  clearTimers();
});
</script>

<template>
  <view v-if="shouldRender" class="xc-bubble" :class="{ 'xc-bubble--fade': fading }">
    <text class="xc-bubble__text">{{ typedText }}</text>
    <text v-if="typing" class="xc-bubble__cursor">|</text>
  </view>
</template>

<style lang="scss" scoped>
.xc-bubble {
  position: relative;
  max-width: 100%;
  padding: 18rpx 22rpx;
  border-radius: $xc-r-lg;
  background: rgba(255, 255, 255, 0.92);
  color: $xc-ink;
  border: 2rpx solid rgba(155, 126, 216, 0.12);
  box-shadow: $xc-sh-md;
  animation: bubbleIn 0.28s $xc-spring both;
}

.xc-bubble::after {
  content: "";
  position: absolute;
  left: 26rpx;
  bottom: -12rpx;
  width: 0;
  height: 0;
  border-left: 9rpx solid transparent;
  border-right: 9rpx solid transparent;
  border-top: 12rpx solid rgba(255, 255, 255, 0.92);
}

.xc-bubble--fade {
  animation: bubbleOut 0.2s ease both;
}

.xc-bubble__text {
  font-size: 24rpx;
  line-height: 1.6;
}

.xc-bubble__cursor {
  margin-left: 4rpx;
  font-size: 22rpx;
  color: $xc-purple;
  animation: xcCursor 0.6s infinite;
}

@keyframes bubbleIn {
  from {
    opacity: 0;
    transform: scale(0.8);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

@keyframes bubbleOut {
  from {
    opacity: 1;
    transform: scale(1);
  }
  to {
    opacity: 0;
    transform: scale(0.92);
  }
}

@keyframes xcCursor {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0;
  }
}
</style>

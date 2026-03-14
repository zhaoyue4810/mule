<script setup lang="ts">
import { computed } from "vue";

const props = withDefaults(
  defineProps<{
    expression?:
      | "default"
      | "happy"
      | "thinking"
      | "surprised"
      | "encouraged"
      | "sleepy"
      | "love"
      | "curious";
    size?: "sm" | "md" | "lg";
    animated?: boolean;
  }>(),
  {
    expression: "default",
    size: "md",
    animated: true,
  },
);

const expressionClass = computed(() => {
  const normalized = props.expression === "curious" ? "thinking" : props.expression;
  return `xc-${normalized}`;
});

const sizeClass = computed(() => `xc-${props.size}`);
</script>

<template>
  <view
    class="xc"
    :class="[
      expressionClass,
      sizeClass,
      { 'xc-float': animated, 'xc-blink': animated },
    ]"
  >
    <text v-if="expression === 'encouraged'" class="xc-fist">✊</text>
    <text v-if="expression === 'love'" class="xc-love-eyes">❤</text>
    <view class="xc-cheek xc-cheek--left" />
    <view class="xc-cheek xc-cheek--right" />
  </view>
</template>

<style lang="scss" scoped>
.xc {
  --xc-size: 48px;
  position: relative;
  width: var(--xc-size);
  height: var(--xc-size);
  border-radius: 50%;
  background: $xc-purple-p;
  border: 2px solid rgba(155, 126, 216, 0.6);
  box-shadow: $xc-sh-sm;
}

.xc::before,
.xc::after {
  content: "";
  position: absolute;
}

.xc::before {
  left: 30%;
  top: 36%;
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: $xc-ink;
  box-shadow: calc(var(--xc-size) * 0.4) 0 0 0 $xc-ink;
}

.xc::after {
  left: 50%;
  bottom: 28%;
  width: calc(var(--xc-size) * 0.24);
  height: calc(var(--xc-size) * 0.13);
  transform: translateX(-50%);
  border-radius: 0 0 999px 999px;
  border: 2px solid $xc-ink;
  border-top: 0;
}

.xc-cheek {
  position: absolute;
  top: 56%;
  width: calc(var(--xc-size) * 0.16);
  height: calc(var(--xc-size) * 0.12);
  border-radius: 50%;
  background: rgba(232, 114, 154, 0.32);
}

.xc-cheek--left {
  left: 18%;
}

.xc-cheek--right {
  right: 18%;
}

.xc-sm {
  --xc-size: 24px;
}

.xc-md {
  --xc-size: 48px;
}

.xc-lg {
  --xc-size: 64px;
}

.xc-happy::before {
  left: 27%;
  top: 34%;
  width: calc(var(--xc-size) * 0.12);
  height: calc(var(--xc-size) * 0.06);
  border-radius: 999px;
  border: 2px solid $xc-ink;
  border-bottom: 0;
  background: transparent;
  box-shadow: calc(var(--xc-size) * 0.38) 0 0 -1px transparent;
}

.xc-happy::after {
  width: calc(var(--xc-size) * 0.3);
  height: calc(var(--xc-size) * 0.16);
  border-radius: 0 0 999px 999px;
  border-width: 2px;
}

.xc-thinking::before {
  animation: xcThink 1.4s ease-in-out infinite;
}

.xc-thinking::after {
  width: calc(var(--xc-size) * 0.12);
  height: calc(var(--xc-size) * 0.12);
  border-radius: 50%;
  border: 2px solid $xc-ink;
  border-top: 2px solid $xc-ink;
  background: transparent;
}

.xc-surprised::before {
  width: 6px;
  height: 6px;
}

.xc-surprised::after {
  width: calc(var(--xc-size) * 0.18);
  height: calc(var(--xc-size) * 0.18);
  border-radius: 50%;
  border: 2px solid $xc-ink;
  border-top: 2px solid $xc-ink;
}

.xc-encouraged .xc-fist {
  position: absolute;
  right: -6%;
  top: -8%;
  font-size: calc(var(--xc-size) * 0.24);
}

.xc-sleepy::before {
  left: 28%;
  top: 38%;
  width: calc(var(--xc-size) * 0.12);
  height: 2px;
  border-radius: 99px;
  background: $xc-ink;
  box-shadow: calc(var(--xc-size) * 0.4) 0 0 0 $xc-ink;
}

.xc-sleepy::after {
  width: calc(var(--xc-size) * 0.22);
  height: calc(var(--xc-size) * 0.18);
  border-radius: 999px;
  border: 2px solid $xc-ink;
  border-top: 0;
}

.xc-love::before {
  content: "";
  display: none;
}

.xc-love .xc-love-eyes {
  position: absolute;
  top: 28%;
  left: 50%;
  transform: translateX(-50%);
  font-size: calc(var(--xc-size) * 0.21);
  letter-spacing: calc(var(--xc-size) * 0.15);
  color: $xc-pink;
}

.xc-love::after {
  width: calc(var(--xc-size) * 0.24);
}

.xc-float {
  animation: gentleBounce 2s ease-in-out infinite;
}

.xc-blink::before {
  animation: xcBlink 3s infinite;
}

@keyframes xcBlink {
  0%,
  92%,
  100% {
    transform: scaleY(1);
  }
  95% {
    transform: scaleY(0.2);
  }
}

@keyframes xcThink {
  0%,
  100% {
    transform: translateX(0);
  }
  50% {
    transform: translateX(2px);
  }
}
</style>

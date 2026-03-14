<script setup lang="ts">
defineProps<{
  text: string;
  show: boolean;
}>();
</script>

<template>
  <transition name="xc-micro">
    <view v-if="show && text" class="xc-micro">
      <text>{{ text }}</text>
    </view>
  </transition>
</template>

<style lang="scss" scoped>
.xc-micro {
  position: fixed;
  left: 50%;
  bottom: 210rpx;
  transform: translateX(-50%);
  padding: 10rpx 18rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.85);
  color: $xc-muted;
  border: 2rpx solid rgba(155, 126, 216, 0.1);
  box-shadow: $xc-sh-sm;
  font-size: 26rpx;
  z-index: 120;
}

.xc-micro-enter-active {
  animation: microUp 0.25s $xc-ease both;
}

.xc-micro-leave-active {
  animation: microDown 0.22s ease both;
}

@keyframes microUp {
  from {
    opacity: 0;
    transform: translateX(-50%) translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
  }
}

@keyframes microDown {
  from {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
  }
  to {
    opacity: 0;
    transform: translateX(-50%) translateY(10px);
  }
}
</style>

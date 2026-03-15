<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    modelValue: boolean;
    maxHeight?: string;
  }>(),
  {
    maxHeight: "70vh",
  },
);

const emit = defineEmits<{
  (e: "update:modelValue", value: boolean): void;
}>();

function close() {
  emit("update:modelValue", false);
}
</script>

<template>
  <view v-if="props.modelValue" class="bs-mask" @tap="close">
    <view class="bs-sheet" :style="{ maxHeight: props.maxHeight }" @tap.stop>
      <view class="bs-handle" />
      <slot />
    </view>
  </view>
</template>

<style scoped lang="scss">
.bs-mask {
  position: fixed;
  inset: 0;
  z-index: 500;
  background: rgba(0, 0, 0, 0.35);
  animation: fadeIn 0.2s ease;
}

.bs-sheet {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: #fff;
  border-radius: 28rpx 28rpx 0 0;
  padding: 16rpx 28rpx calc(28rpx + env(safe-area-inset-bottom));
  animation: slideUp 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  overflow-y: auto;
  box-shadow: 0 -16rpx 40rpx rgba(58, 46, 66, 0.12);
}

.bs-handle {
  width: 48rpx;
  height: 8rpx;
  border-radius: 999rpx;
  background: #ddd;
  margin: 0 auto 16rpx;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }

  to {
    opacity: 1;
  }
}

@keyframes slideUp {
  from {
    transform: translateY(100%);
  }

  to {
    transform: translateY(0);
  }
}
</style>

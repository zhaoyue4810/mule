<script setup lang="ts">
import { ref } from "vue";
import { onLoad } from "@dcloudio/uni-app";

import { fetchMyProfileSettings, updateMyProfileSettings } from "@/shared/services/profile";
import { SoundManager } from "@/shared/utils/sound-manager";

const soundEnabled = ref(true);
const hapticEnabled = ref(true);
const loading = ref(true);

async function loadSettings() {
  loading.value = true;
  try {
    const payload = await fetchMyProfileSettings();
    soundEnabled.value = payload.sound_enabled;
    SoundManager.setSoundEnabled(payload.sound_enabled);
    hapticEnabled.value = SoundManager.isHapticEnabled();
  } finally {
    loading.value = false;
  }
}

async function updateSound(value: boolean) {
  soundEnabled.value = value;
  SoundManager.setSoundEnabled(value);
  await updateMyProfileSettings({ sound_enabled: value });
}

function updateHaptic(value: boolean) {
  hapticEnabled.value = value;
  SoundManager.setHapticEnabled(value);
}

function onSoundSwitchChange(event: { detail: { value: boolean } }) {
  void updateSound(Boolean(event.detail.value));
}

function onHapticSwitchChange(event: { detail: { value: boolean } }) {
  updateHaptic(Boolean(event.detail.value));
}

onLoad(() => {
  void loadSettings();
});
</script>

<template>
  <view class="page">
    <view class="panel">
      <text class="panel__title">声音与触感</text>
      <text class="panel__body">这里可以控制实时合成音效和触觉反馈。关闭后会在支持的平台静默降级。</text>
      <view v-if="loading" class="item"><text>正在读取设置...</text></view>
      <template v-else>
        <view class="item">
          <text>声音反馈</text>
          <switch :checked="soundEnabled" color="#d96f3d" @change="onSoundSwitchChange" />
        </view>
        <view class="item">
          <text>触觉反馈</text>
          <switch :checked="hapticEnabled" color="#d96f3d" @change="onHapticSwitchChange" />
        </view>
      </template>
    </view>
  </view>
</template>

<style scoped lang="scss">
.page { padding: 28rpx; }
.panel { padding: 28rpx; border-radius: 24rpx; background: rgba(255,255,255,0.9); border: 2rpx solid rgba(217,111,61,0.08); }
.panel__title { display:block; font-size:30rpx; font-weight:700; }
.panel__body { display:block; margin-top:14rpx; font-size:24rpx; line-height:1.7; color:$xc-muted; }
.item { display:flex; justify-content:space-between; align-items:center; padding:22rpx 0; font-size:26rpx; border-bottom: 2rpx solid rgba(217,111,61,0.08); }
.item:last-child { border-bottom: 0; }
</style>

<script setup lang="ts">
import { computed, ref } from "vue";
import { onLoad } from "@dcloudio/uni-app";

import { fetchMyProfileSettings, updateMyProfileSettings } from "@/shared/services/profile";
import { SoundManager } from "@/shared/utils/sound-manager";

const soundEnabled = ref(true);
const hapticEnabled = ref(true);
const loading = ref(true);
const saving = ref(false);

const experienceSummary = computed(() =>
  `${soundEnabled.value ? "声音已开" : "声音已关"} / ${hapticEnabled.value ? "触感已开" : "触感已关"}`,
);

const preferenceChips = computed(() => [
  soundEnabled.value ? "🔊 沉浸音效" : "🔇 安静模式",
  hapticEnabled.value ? "📳 轻触反馈" : "🫥 仅视觉反馈",
  "🌙 夜间也能低干扰使用",
]);

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
  saving.value = true;
  try {
    await updateMyProfileSettings({ sound_enabled: value });
    uni.showToast({
      title: value ? "声音已开启" : "声音已关闭",
      icon: "success",
    });
  } catch (err) {
    uni.showToast({
      title: err instanceof Error ? err.message : "保存失败",
      icon: "none",
    });
  } finally {
    saving.value = false;
  }
}

function updateHaptic(value: boolean) {
  hapticEnabled.value = value;
  SoundManager.setHapticEnabled(value);
  uni.showToast({
    title: value ? "触感已开启" : "触感已关闭",
    icon: "success",
  });
}

function onSoundSwitchChange(event: { detail: { value: boolean } }) {
  void updateSound(Boolean(event.detail.value));
}

function onHapticSwitchChange(event: { detail: { value: boolean } }) {
  updateHaptic(Boolean(event.detail.value));
}

function openStub(title: string) {
  uni.showToast({
    title: `${title}即将上线`,
    icon: "none",
  });
}

onLoad(() => {
  void loadSettings();
});
</script>

<template>
  <view class="page">
    <view class="page__glow page__glow--violet" />
    <view class="page__glow page__glow--gold" />
    <view class="shell">
      <view class="hero-card">
        <view class="hero-card__top">
          <view>
            <text class="hero-card__eyebrow">EXPERIENCE SETTINGS</text>
            <text class="hero-card__title">声音与触感</text>
            <text class="hero-card__body">
              控制答题、翻牌、解锁勋章和切页时的反馈强度，让整条体验更像你喜欢的节奏。
            </text>
          </view>
          <view class="hero-card__orb">🎧</view>
        </view>
        <view class="hero-card__summary">
          <text class="hero-card__summary-label">当前状态</text>
          <text class="hero-card__summary-value">{{ loading ? "读取中..." : experienceSummary }}</text>
        </view>
        <view class="hero-card__chips">
          <text v-for="item in preferenceChips" :key="item" class="hero-card__chip">{{ item }}</text>
        </view>
      </view>

      <view class="card">
        <view class="card__head">
          <text class="card__title">实时反馈</text>
          <text class="card__subtitle">建议保留轻量反馈，能明显提升答题动线和奖励时刻的沉浸感。</text>
        </view>
        <view v-if="loading" class="setting-row setting-row--loading">
          <text class="setting-row__title">正在读取设置...</text>
        </view>
        <template v-else>
          <view class="setting-row">
            <view class="setting-row__icon">🔊</view>
            <view class="setting-row__content">
              <text class="setting-row__title">声音反馈</text>
              <text class="setting-row__desc">切页、提交、解锁成就和部分题型会播放轻量音效。</text>
            </view>
            <switch
              :checked="soundEnabled"
              :disabled="saving"
              color="#9B7ED8"
              @change="onSoundSwitchChange"
            />
          </view>
          <view class="setting-row">
            <view class="setting-row__icon">📳</view>
            <view class="setting-row__content">
              <text class="setting-row__title">触觉反馈</text>
              <text class="setting-row__desc">在支持的平台上提供轻触震动，让操作更有反馈感。</text>
            </view>
            <switch
              :checked="hapticEnabled"
              color="#9B7ED8"
              @change="onHapticSwitchChange"
            />
          </view>
        </template>
      </view>

      <view class="card card--soft">
        <view class="card__head">
          <text class="card__title">体验建议</text>
          <text class="card__subtitle">不同使用场景下可以切到不同组合，减少打扰感。</text>
        </view>
        <view class="modes">
          <view class="mode-card">
            <text class="mode-card__emoji">🌤️</text>
            <text class="mode-card__title">沉浸模式</text>
            <text class="mode-card__body">声音与触感都打开，适合自己独处时完整体验测试和报告。</text>
          </view>
          <view class="mode-card">
            <text class="mode-card__emoji">🌙</text>
            <text class="mode-card__title">安静模式</text>
            <text class="mode-card__body">保留视觉动效，关闭声音或触感，更适合通勤、夜间和公共场景。</text>
          </view>
        </view>
      </view>

      <view class="card">
        <view class="card__head">
          <text class="card__title">更多管理</text>
          <text class="card__subtitle">后续会在这里补充缓存、下载和实验特性开关。</text>
        </view>
        <view class="link-list">
          <view class="link-item" @tap="openStub('通知频率')">
            <view class="link-item__content">
              <text class="link-item__title">通知频率</text>
              <text class="link-item__desc">控制报告、匹配和提醒的触达节奏</text>
            </view>
            <text class="link-item__arrow">›</text>
          </view>
          <view class="link-item" @tap="openStub('实验特性')">
            <view class="link-item__content">
              <text class="link-item__title">实验特性</text>
              <text class="link-item__desc">率先体验新的交互动效和个性化玩法</text>
            </view>
            <text class="link-item__arrow">›</text>
          </view>
          <view class="link-item" @tap="openStub('数据管理')">
            <view class="link-item__content">
              <text class="link-item__title">数据管理</text>
              <text class="link-item__desc">后续会支持清理缓存、导出报告和备份设置</text>
            </view>
            <text class="link-item__arrow">›</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<style scoped lang="scss">
.page {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  padding: 28rpx 24rpx 60rpx;
  background:
    radial-gradient(circle at top, rgba(255, 255, 255, 0.96), rgba(255, 247, 240, 0.82) 42%, #fffaf6 100%);
}

.page__glow {
  position: absolute;
  width: 420rpx;
  height: 420rpx;
  border-radius: 50%;
  filter: blur(32px);
  opacity: 0.45;
  pointer-events: none;
}

.page__glow--violet {
  top: -110rpx;
  right: -110rpx;
  background: rgba(155, 126, 216, 0.22);
}

.page__glow--gold {
  bottom: 120rpx;
  left: -120rpx;
  background: rgba(223, 176, 94, 0.16);
}

.shell {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  gap: 20rpx;
  animation: fadeInUp 0.45s $xc-ease both;
}

.hero-card,
.card {
  @include card-base;
}

.hero-card {
  padding: 30rpx;
  background:
    linear-gradient(140deg, rgba(255, 255, 255, 0.94), rgba(245, 237, 255, 0.9));
}

.hero-card__top {
  display: flex;
  gap: 16rpx;
  justify-content: space-between;
}

.hero-card__orb {
  width: 92rpx;
  height: 92rpx;
  border-radius: 28rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background:
    radial-gradient(circle at 35% 35%, rgba(255, 255, 255, 0.95), rgba(255, 236, 245, 0.8)),
    linear-gradient(135deg, rgba(155, 126, 216, 0.26), rgba(232, 114, 154, 0.18));
  font-size: 38rpx;
  box-shadow: 0 18rpx 32rpx rgba(155, 126, 216, 0.15);
}

.hero-card__eyebrow {
  display: block;
  font-size: 20rpx;
  letter-spacing: 2.8rpx;
  font-weight: 700;
  color: rgba(123, 110, 133, 0.76);
}

.hero-card__title {
  display: block;
  margin-top: 12rpx;
  font-size: 40rpx;
  font-weight: 800;
  color: $xc-ink;
}

.hero-card__body {
  display: block;
  margin-top: 12rpx;
  font-size: 24rpx;
  line-height: 1.7;
  color: $xc-muted;
}

.hero-card__summary {
  margin-top: 22rpx;
  padding: 18rpx 20rpx;
  border-radius: 22rpx;
  background: rgba(255, 247, 238, 0.92);
  border: 2rpx solid rgba(155, 126, 216, 0.08);
}

.hero-card__summary-label {
  display: block;
  font-size: 21rpx;
  color: $xc-muted;
}

.hero-card__summary-value {
  display: block;
  margin-top: 8rpx;
  font-size: 28rpx;
  font-weight: 700;
  color: $xc-accent;
}

.hero-card__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 10rpx;
  margin-top: 18rpx;
}

.hero-card__chip {
  padding: 10rpx 16rpx;
  border-radius: 999rpx;
  background: rgba(255, 242, 231, 0.96);
  font-size: 22rpx;
  color: $xc-ink;
}

.card {
  padding: 28rpx;
}

.card--soft {
  background:
    linear-gradient(145deg, rgba(255, 251, 244, 0.96), rgba(248, 241, 255, 0.9));
}

.card__head {
  display: flex;
  flex-direction: column;
  gap: 10rpx;
}

.card__title {
  font-size: 31rpx;
  font-weight: 800;
  color: $xc-ink;
}

.card__subtitle {
  font-size: 23rpx;
  line-height: 1.7;
  color: $xc-muted;
}

.setting-row {
  margin-top: 18rpx;
  padding: 20rpx 0;
  display: grid;
  grid-template-columns: 64rpx 1fr auto;
  gap: 16rpx;
  align-items: center;
  border-bottom: 1px solid rgba(155, 126, 216, 0.08);
}

.setting-row:last-child {
  border-bottom: 0;
}

.setting-row--loading {
  grid-template-columns: 1fr;
}

.setting-row__icon {
  width: 64rpx;
  height: 64rpx;
  border-radius: 20rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(245, 238, 255, 0.9);
  font-size: 30rpx;
}

.setting-row__content {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.setting-row__title {
  font-size: 27rpx;
  font-weight: 700;
  color: $xc-ink;
}

.setting-row__desc {
  font-size: 22rpx;
  line-height: 1.6;
  color: $xc-muted;
}

.modes {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14rpx;
  margin-top: 18rpx;
}

.mode-card {
  padding: 22rpx 18rpx;
  border-radius: 24rpx;
  background: rgba(255, 247, 238, 0.94);
  border: 2rpx solid rgba(155, 126, 216, 0.08);
}

.mode-card__emoji {
  display: block;
  font-size: 30rpx;
}

.mode-card__title {
  display: block;
  margin-top: 10rpx;
  font-size: 26rpx;
  font-weight: 700;
  color: $xc-ink;
}

.mode-card__body {
  display: block;
  margin-top: 10rpx;
  font-size: 22rpx;
  line-height: 1.7;
  color: $xc-muted;
}

.link-list {
  margin-top: 18rpx;
}

.link-item {
  display: grid;
  grid-template-columns: 1fr 24rpx;
  gap: 16rpx;
  align-items: center;
  padding: 22rpx 0;
  border-bottom: 1px solid rgba(155, 126, 216, 0.08);
}

.link-item:last-child {
  border-bottom: 0;
}

.link-item__content {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.link-item__title {
  font-size: 26rpx;
  font-weight: 700;
  color: $xc-ink;
}

.link-item__desc {
  font-size: 22rpx;
  line-height: 1.6;
  color: $xc-muted;
}

.link-item__arrow {
  font-size: 30rpx;
  color: $xc-hint;
  text-align: right;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(16rpx);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>

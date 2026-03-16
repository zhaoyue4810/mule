<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import type { AuthUserPayload } from "@/shared/models/auth";
import type { OnboardingProfilePayload } from "@/shared/models/profile";
import { fetchAuthMe, getSessionUser, setSessionUser } from "@/shared/services/auth";
import {
  fetchMyOnboardingProfile,
  updateMyOnboardingProfile,
} from "@/shared/services/profile";
import { SoundManager } from "@/shared/utils/sound-manager";

const avatarOptions = ["🧠", "🌟", "🌈", "🔥", "🌙", "🪐", "🍀", "🎧", "🫧", "🍓", "🦋", "🌻"];
const genderOptions = [
  { label: "男", value: 1 },
  { label: "女", value: 2 },
  { label: "保密", value: 0 },
];
const yearOptions = Array.from({ length: 2010 - 1960 + 1 }, (_, index) => 1960 + index);
const monthOptions = Array.from({ length: 12 }, (_, index) => index + 1);

const loading = ref(true);
const saving = ref(false);
const sessionUser = ref<AuthUserPayload | null>(getSessionUser());
const form = ref<OnboardingProfilePayload>({
  nickname: "",
  avatar_value: avatarOptions[0],
  bio: "",
  gender: 0,
  birth_year: null,
  birth_month: null,
  onboarding_completed: true,
});

const yearIndex = computed(() => {
  const index = yearOptions.findIndex((item) => item === form.value.birth_year);
  return index >= 0 ? index : 0;
});

const monthIndex = computed(() => {
  const index = monthOptions.findIndex((item) => item === form.value.birth_month);
  return index >= 0 ? index : 0;
});

const nicknameCount = computed(() => form.value.nickname.length);
const bioCount = computed(() => form.value.bio.length);
const selectedGenderLabel = computed(
  () => genderOptions.find((item) => item.value === form.value.gender)?.label || "保密",
);
const profileDisplayName = computed(
  () => form.value.nickname.trim() || sessionUser.value?.nickname || "心测用户",
);
const profileDisplayBio = computed(
  () => form.value.bio.trim() || "给自己留一句最近最像你的话，让名片更有温度。",
);
const profileMetaChips = computed(() => {
  const chips = [`${form.value.avatar_value} 当前头像`, `${selectedGenderLabel.value} 向外展示`];
  if (form.value.birth_year || form.value.birth_month) {
    chips.push(
      `${form.value.birth_year || "?"} 年 ${form.value.birth_month || "?"} 月`,
    );
  } else {
    chips.push("生日信息可稍后补充");
  }
  return chips;
});
const vibeHint = computed(() => {
  if (bioCount.value >= 32) {
    return "你的个人名片已经很有辨识度了。";
  }
  if (bioCount.value >= 12) {
    return "再补一点细节，别人会更容易感受到你的气质。";
  }
  return "写一句最近最像你的话，名片会立刻有温度。";
});
const saveButtonEnabled = computed(() => Boolean(form.value.nickname.trim()) && !saving.value);

function playSelectFeedback() {
  SoundManager.haptic(10);
}

async function loadProfile() {
  loading.value = true;
  try {
    const payload = await fetchMyOnboardingProfile();
    form.value = {
      ...payload,
      avatar_value: payload.avatar_value || avatarOptions[0],
    };
  } catch (error) {
    uni.showToast({
      title: error instanceof Error ? error.message : "资料加载失败",
      icon: "none",
    });
  } finally {
    loading.value = false;
  }
}

function onYearChange(event: { detail: { value: string } }) {
  form.value.birth_year = yearOptions[Number(event.detail.value)] || null;
  playSelectFeedback();
}

function onMonthChange(event: { detail: { value: string } }) {
  form.value.birth_month = monthOptions[Number(event.detail.value)] || null;
  playSelectFeedback();
}

async function saveProfile() {
  if (saving.value) {
    return;
  }
  if (!form.value.nickname.trim()) {
    uni.showToast({ title: "请先填写昵称", icon: "none" });
    return;
  }
  saving.value = true;
  try {
    await updateMyOnboardingProfile({
      nickname: form.value.nickname.trim(),
      avatar_value: form.value.avatar_value,
      bio: form.value.bio.trim(),
      gender: form.value.gender,
      birth_year: form.value.birth_year || null,
      birth_month: form.value.birth_month || null,
    });
    const user = await fetchAuthMe();
    setSessionUser(user);
    sessionUser.value = user;
    if (SoundManager.isSoundEnabled()) {
      SoundManager.play("ding");
    }
    uni.showToast({ title: "资料已更新", icon: "success" });
    setTimeout(() => {
      uni.navigateBack({ delta: 1 });
    }, 320);
  } catch (error) {
    uni.showToast({
      title: error instanceof Error ? error.message : "保存失败",
      icon: "none",
    });
  } finally {
    saving.value = false;
  }
}

onMounted(() => {
  void loadProfile();
});
</script>

<template>
  <view class="page">
    <view class="page__glow page__glow--violet" />
    <view class="page__glow page__glow--pink" />
    <view class="shell">
      <view v-if="loading" class="card loading-card">
        <text class="loading-card__text">正在读取你的灵魂档案...</text>
      </view>

      <template v-else>
        <view class="hero-card">
          <view class="hero-card__top">
            <view class="hero-card__avatar" @tap="playSelectFeedback">
              <text>{{ form.avatar_value }}</text>
            </view>
            <view class="hero-card__copy">
              <text class="hero-card__eyebrow">PROFILE EDITOR</text>
              <text class="hero-card__title">{{ profileDisplayName }}</text>
              <text class="hero-card__subtitle">公开资料会影响你的人设名片、个人中心和分享场景。</text>
            </view>
          </view>
          <text class="hero-card__bio">{{ profileDisplayBio }}</text>
          <view class="hero-card__chips">
            <text v-for="item in profileMetaChips" :key="item" class="hero-card__chip">{{ item }}</text>
          </view>
        </view>

        <view class="card preview-card">
          <view class="card__head">
            <text class="card__title">名片预览</text>
            <text class="card__subtitle">{{ vibeHint }}</text>
          </view>
          <view class="preview-card__body">
            <view class="preview-card__avatar">{{ form.avatar_value }}</view>
            <view class="preview-card__content">
              <text class="preview-card__name">{{ profileDisplayName }}</text>
              <text class="preview-card__role">灵魂探索者</text>
              <text class="preview-card__summary">{{ profileDisplayBio }}</text>
            </view>
          </view>
        </view>

        <view class="card">
          <view class="card__head">
            <text class="card__title">基础信息</text>
            <text class="card__subtitle">保留一点自我介绍，会让你的名片更有温度。</text>
          </view>

          <view class="field">
            <view class="field__top">
              <text class="field__label">昵称</text>
              <text class="field__count">{{ nicknameCount }}/12</text>
            </view>
            <input
              v-model.trim="form.nickname"
              class="field__input"
              maxlength="12"
              placeholder="输入一个你喜欢的名字"
            />
          </view>

          <view class="field">
            <view class="field__top">
              <text class="field__label">个性签名</text>
              <text class="field__count">{{ bioCount }}/50</text>
            </view>
            <textarea
              v-model.trim="form.bio"
              class="field__textarea"
              maxlength="50"
              placeholder="写一句最近最像你的话"
            />
          </view>
        </view>

        <view class="card">
          <view class="card__head">
            <text class="card__title">身份细节</text>
            <text class="card__subtitle">这些信息只会帮助心测更温柔地理解你。</text>
          </view>

          <view class="field">
            <text class="field__label">性别</text>
            <view class="chips">
              <view
                v-for="item in genderOptions"
                :key="item.value"
                class="chip"
                :class="{ 'chip--active': form.gender === item.value }"
                @tap="form.gender = item.value; playSelectFeedback()"
              >
                <text>{{ item.label }}</text>
              </view>
            </view>
          </view>

          <view class="field field--inline">
            <view class="picker-card">
              <text class="field__label">出生年份</text>
              <picker :range="yearOptions" :value="yearIndex" @change="onYearChange">
                <view class="picker-card__value">
                  <text>{{ form.birth_year || "请选择" }}</text>
                  <text class="picker-card__suffix">年</text>
                </view>
              </picker>
            </view>
            <view class="picker-card">
              <text class="field__label">出生月份</text>
              <picker :range="monthOptions" :value="monthIndex" @change="onMonthChange">
                <view class="picker-card__value">
                  <text>{{ form.birth_month || "请选择" }}</text>
                  <text class="picker-card__suffix">月</text>
                </view>
              </picker>
            </view>
          </view>
        </view>

        <view class="card">
          <view class="card__head">
            <text class="card__title">头像工作台</text>
            <text class="card__subtitle">选一个最能代表你现在状态的小符号。</text>
          </view>
          <view class="avatar-grid">
            <view
              v-for="item in avatarOptions"
              :key="item"
              class="avatar-chip"
              :class="{ 'avatar-chip--active': form.avatar_value === item }"
              @tap="form.avatar_value = item; playSelectFeedback()"
            >
              <text class="avatar-chip__emoji">{{ item }}</text>
            </view>
          </view>
        </view>

        <view class="action-card">
          <view class="action-card__copy">
            <text class="action-card__title">保存这张新的灵魂名片</text>
            <text class="action-card__body">
              当前账户：{{ sessionUser?.nickname || "心测用户" }}。保存后会同步更新个人中心和分享视图。
            </text>
          </view>
          <button class="submit-btn" :disabled="!saveButtonEnabled" :loading="saving" @tap="saveProfile">
            {{ saving ? "保存中..." : "保存资料" }}
          </button>
        </view>
      </template>
    </view>
  </view>
</template>

<style scoped lang="scss">
.page {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  padding: 26rpx 24rpx 48rpx;
  background:
    radial-gradient(circle at top right, rgba(232, 114, 154, 0.14), transparent 30%),
    radial-gradient(circle at top left, rgba(155, 126, 216, 0.18), transparent 26%),
    $xc-bg;
}

.page__glow {
  position: absolute;
  width: 420rpx;
  height: 420rpx;
  border-radius: 50%;
  filter: blur(32px);
  opacity: 0.42;
  pointer-events: none;
}

.page__glow--violet {
  top: -120rpx;
  right: -120rpx;
  background: rgba(155, 126, 216, 0.22);
}

.page__glow--pink {
  left: -140rpx;
  bottom: 180rpx;
  background: rgba(232, 114, 154, 0.14);
}

.shell {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  gap: 20rpx;
  animation: fadeInUp 0.45s $xc-ease both;
}

.card,
.hero-card,
.action-card {
  @include card-base;
}

.card {
  padding: 28rpx;
}

.loading-card {
  min-height: 260rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.loading-card__text {
  font-size: 26rpx;
  color: $xc-muted;
}

.hero-card {
  padding: 32rpx 30rpx;
  background:
    radial-gradient(circle at top right, rgba(255, 244, 214, 0.96), rgba(248, 208, 225, 0.7)),
    linear-gradient(135deg, rgba(247, 240, 255, 0.96), rgba(255, 255, 255, 0.88));
}

.hero-card__top {
  display: flex;
  gap: 18rpx;
  align-items: center;
}

.hero-card__avatar {
  width: 140rpx;
  height: 140rpx;
  border-radius: 38rpx;
  background: rgba(255, 255, 255, 0.88);
  border: 4rpx solid rgba(155, 126, 216, 0.22);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 64rpx;
  box-shadow: 0 24rpx 54rpx rgba(155, 126, 216, 0.14);
}

.hero-card__copy {
  flex: 1;
  min-width: 0;
}

.hero-card__eyebrow {
  display: block;
  font-size: 20rpx;
  font-weight: 700;
  letter-spacing: 2.8rpx;
  color: rgba(123, 110, 133, 0.74);
}

.hero-card__title {
  display: block;
  margin-top: 10rpx;
  font-size: 40rpx;
  font-weight: 800;
  color: $xc-ink;
}

.hero-card__subtitle {
  display: block;
  margin-top: 10rpx;
  font-size: 23rpx;
  line-height: 1.7;
  color: $xc-muted;
}

.hero-card__bio {
  display: block;
  margin-top: 22rpx;
  font-size: 24rpx;
  line-height: 1.8;
  color: $xc-ink;
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

.card__head {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
  margin-bottom: 22rpx;
}

.card__title {
  font-size: 30rpx;
  font-weight: 700;
  color: $xc-ink;
}

.card__subtitle {
  font-size: 24rpx;
  line-height: 1.7;
  color: $xc-muted;
}

.preview-card__body {
  display: flex;
  gap: 16rpx;
  align-items: center;
  padding: 20rpx;
  border-radius: 24rpx;
  background: rgba(255, 248, 239, 0.96);
  border: 2rpx solid rgba(155, 126, 216, 0.08);
}

.preview-card__avatar {
  width: 108rpx;
  height: 108rpx;
  border-radius: 30rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.92);
  font-size: 48rpx;
}

.preview-card__content {
  flex: 1;
  min-width: 0;
}

.preview-card__name {
  display: block;
  font-size: 28rpx;
  font-weight: 700;
  color: $xc-ink;
}

.preview-card__role {
  display: block;
  margin-top: 8rpx;
  font-size: 22rpx;
  color: $xc-accent;
}

.preview-card__summary {
  display: block;
  margin-top: 10rpx;
  font-size: 22rpx;
  line-height: 1.7;
  color: $xc-muted;
}

.field + .field {
  margin-top: 22rpx;
}

.field--inline {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16rpx;
}

.field__top {
  margin-bottom: 12rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.field__label {
  font-size: 24rpx;
  font-weight: 600;
  color: $xc-ink;
}

.field__count {
  font-size: 22rpx;
  color: rgba(123, 110, 133, 0.8);
}

.field__input,
.field__textarea {
  width: 100%;
  padding: 20rpx 22rpx;
  border-radius: 22rpx;
  background: rgba(248, 246, 255, 0.9);
  border: 2rpx solid rgba(155, 126, 216, 0.08);
  box-sizing: border-box;
  font-size: 26rpx;
  color: $xc-ink;
}

.field__textarea {
  min-height: 168rpx;
}

.chips {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14rpx;
  margin-top: 12rpx;
}

.chip {
  padding: 18rpx 0;
  border-radius: 999rpx;
  text-align: center;
  font-size: 25rpx;
  color: $xc-muted;
  background: rgba(248, 246, 255, 0.92);
  border: 2rpx solid rgba(155, 126, 216, 0.08);
  transition: all 0.28s $xc-ease;
}

.chip--active {
  color: $xc-white;
  background: linear-gradient(135deg, $xc-purple, $xc-pink);
  border-color: transparent;
  transform: translateY(-2rpx);
  box-shadow: 0 16rpx 32rpx rgba(155, 126, 216, 0.2);
}

.picker-card {
  padding: 20rpx 22rpx;
  border-radius: 22rpx;
  background: rgba(248, 246, 255, 0.9);
  border: 2rpx solid rgba(155, 126, 216, 0.08);
}

.picker-card__value {
  margin-top: 12rpx;
  display: flex;
  align-items: baseline;
  gap: 8rpx;
  font-size: 28rpx;
  color: $xc-ink;
}

.picker-card__suffix {
  font-size: 22rpx;
  color: $xc-muted;
}

.avatar-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16rpx;
}

.avatar-chip {
  height: 184rpx;
  aspect-ratio: 1 / 1;
  border-radius: 26rpx;
  background: rgba(248, 246, 255, 0.96);
  border: 2rpx solid rgba(155, 126, 216, 0.08);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s $xc-ease;
}

.avatar-chip--active {
  border-color: rgba(155, 126, 216, 0.85);
  box-shadow: 0 0 0 4rpx rgba(155, 126, 216, 0.12);
  transform: translateY(-4rpx);
}

.avatar-chip__emoji {
  font-size: 52rpx;
}

.action-card {
  padding: 26rpx 28rpx;
  display: flex;
  flex-direction: column;
  gap: 18rpx;
  background:
    linear-gradient(145deg, rgba(255, 250, 244, 0.96), rgba(245, 237, 255, 0.9));
}

.action-card__title {
  display: block;
  font-size: 28rpx;
  font-weight: 700;
  color: $xc-ink;
}

.action-card__body {
  display: block;
  margin-top: 10rpx;
  font-size: 23rpx;
  line-height: 1.7;
  color: $xc-muted;
}

.submit-btn {
  @include btn-primary;
  height: 92rpx;
  font-size: 28rpx;
  font-weight: 700;
  box-shadow: 0 20rpx 36rpx rgba(155, 126, 216, 0.22);
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

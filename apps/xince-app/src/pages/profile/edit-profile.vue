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
    <view class="shell">
      <view v-if="loading" class="card loading-card">
        <text class="loading-card__text">正在读取你的灵魂档案...</text>
      </view>

      <template v-else>
        <view class="hero-card">
          <view class="hero-card__avatar" @tap="playSelectFeedback">
            <text>{{ form.avatar_value }}</text>
          </view>
          <text class="hero-card__cta">更换头像</text>
          <text class="hero-card__hint">
            当前账户：{{ sessionUser?.nickname || "心测用户" }}，下面可以随时更新公开资料。
          </text>
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
            <text class="card__title">更多信息</text>
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
            <text class="card__title">头像偏好</text>
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

        <button class="submit-btn" :loading="saving" @tap="saveProfile">
          {{ saving ? "保存中..." : "保存资料" }}
        </button>
        <view class="safe-space" />
      </template>
    </view>
  </view>
</template>

<style scoped lang="scss">
.page {
  min-height: 100vh;
  padding: 26rpx 24rpx 0;
  animation: fadeInUp 0.45s $xc-ease both;
  background:
    radial-gradient(circle at top right, rgba(232, 114, 154, 0.14), transparent 30%),
    radial-gradient(circle at top left, rgba(155, 126, 216, 0.18), transparent 26%),
    $xc-bg;
}

.shell {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.card {
  @include card-base;
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
  padding: 34rpx 30rpx;
  border-radius: 30rpx;
  background:
    radial-gradient(circle at top right, rgba(255, 244, 214, 0.96), rgba(248, 208, 225, 0.7)),
    linear-gradient(135deg, rgba(247, 240, 255, 0.96), rgba(255, 255, 255, 0.88));
  box-shadow: $xc-shadow;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.hero-card__avatar {
  width: 160rpx;
  height: 160rpx;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.85);
  border: 4rpx solid rgba(155, 126, 216, 0.26);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 72rpx;
  box-shadow: 0 24rpx 54rpx rgba(155, 126, 216, 0.14);
}

.hero-card__cta {
  margin-top: 18rpx;
  font-size: 28rpx;
  font-weight: 700;
  color: $xc-purple-d;
}

.hero-card__hint {
  margin-top: 10rpx;
  text-align: center;
  font-size: 24rpx;
  line-height: 1.7;
  color: $xc-muted;
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
  line-height: 1.6;
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

.submit-btn {
  @include btn-primary;
  margin-top: 4rpx;
  height: 92rpx;
  font-size: 28rpx;
  font-weight: 700;
  box-shadow: 0 20rpx 36rpx rgba(155, 126, 216, 0.22);
}

.safe-space {
  height: 64rpx;
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

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

const avatarOptions = ["🧠", "🌟", "🌈", "🔥", "🌙", "🪐", "🍀", "🎧"];
const genderOptions = [
  { label: "保密", value: 0 },
  { label: "男生", value: 1 },
  { label: "女生", value: 2 },
];
const yearOptions = Array.from({ length: new Date().getFullYear() - 1960 + 1 }, (_, index) => 1960 + index);
const monthOptions = Array.from({ length: 12 }, (_, index) => index + 1);

const loading = ref(true);
const saving = ref(false);
const sessionUser = ref<AuthUserPayload | null>(getSessionUser());
const form = ref<OnboardingProfilePayload>({
  nickname: "",
  avatar_value: "🧠",
  bio: "",
  gender: 0,
  birth_year: null,
  birth_month: null,
  onboarding_completed: false,
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
const previewName = computed(
  () => form.value.nickname.trim() || sessionUser.value?.nickname || "心测用户",
);
const previewBio = computed(
  () => form.value.bio.trim() || "从这里开始，慢慢拼出你的灵魂说明书。",
);
const previewChips = computed(() => {
  const chips = [`${form.value.avatar_value} 初始头像`, `${selectedGenderLabel.value} 展示设置`];
  if (form.value.birth_year || form.value.birth_month) {
    chips.push(`${form.value.birth_year || "?"} 年 ${form.value.birth_month || "?"} 月`);
  } else {
    chips.push("生日信息可稍后补充");
  }
  return chips;
});
const canSubmit = computed(() => Boolean(previewName.value.trim()) && !saving.value);

function playSelectFeedback() {
  SoundManager.haptic(10);
}

async function loadOnboarding() {
  loading.value = true;
  try {
    const payload = await fetchMyOnboardingProfile();
    form.value = {
      ...payload,
      avatar_value: payload.avatar_value || "🧠",
    };
  } catch (error) {
    uni.showToast({
      title: error instanceof Error ? error.message : "加载失败",
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

async function submit(useFallback = false) {
  if (saving.value) {
    return;
  }
  saving.value = true;
  try {
    const nickname = useFallback
      ? previewName.value.trim()
      : form.value.nickname.trim() || previewName.value.trim();
    await updateMyOnboardingProfile({
      nickname,
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
    uni.showToast({
      title: "欢迎来到心测",
      icon: "success",
    });
    setTimeout(() => {
      uni.switchTab({
        url: "/pages/home/index",
      });
    }, 300);
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
  void loadOnboarding();
});
</script>

<template>
  <view class="page">
    <view class="page__glow page__glow--violet" />
    <view class="page__glow page__glow--gold" />
    <view class="shell">
      <view class="hero-card">
        <text class="hero-card__eyebrow">STEP 1 / 1</text>
        <text class="hero-card__title">先用 30 秒，给你的心测旅程一个起点。</text>
        <text class="hero-card__body">
          这些信息会用来完善你的个人中心和后续成长反馈，不会影响你立刻开始测试。
        </text>
        <view class="hero-card__preview">
          <view class="hero-card__avatar">{{ form.avatar_value }}</view>
          <view class="hero-card__preview-copy">
            <text class="hero-card__preview-name">{{ previewName }}</text>
            <text class="hero-card__preview-role">灵魂探索者</text>
            <text class="hero-card__preview-bio">{{ previewBio }}</text>
          </view>
        </view>
        <view class="hero-card__chips">
          <text v-for="item in previewChips" :key="item" class="hero-card__chip">{{ item }}</text>
        </view>
      </view>

      <view v-if="loading" class="panel">
        <text class="panel__text">正在加载你的初始资料...</text>
      </view>

      <view v-else class="form">
        <view class="panel">
          <view class="panel__head">
            <text class="panel__title">选择你的头像</text>
            <text class="panel__subtitle">先选一个最像现在状态的小符号。</text>
          </view>
          <view class="avatar-grid">
            <view
              v-for="item in avatarOptions"
              :key="item"
              class="avatar-option"
              :class="{ 'avatar-option--active': form.avatar_value === item }"
              @tap="form.avatar_value = item; playSelectFeedback()"
            >
              <text class="avatar-option__emoji">{{ item }}</text>
            </view>
          </view>
        </view>

        <view class="panel">
          <view class="panel__head">
            <text class="panel__title">基础资料</text>
            <text class="panel__subtitle">这些信息会直接进入你的个人名片和档案页。</text>
          </view>
          <view class="field">
            <view class="field__top">
              <text class="field__label">昵称</text>
              <text class="field__count">{{ nicknameCount }}/20</text>
            </view>
            <input v-model.trim="form.nickname" class="field__input" maxlength="20" placeholder="给自己起个名字" />
          </view>
          <view class="field">
            <view class="field__top">
              <text class="field__label">一句介绍</text>
              <text class="field__count">{{ bioCount }}/80</text>
            </view>
            <textarea
              v-model.trim="form.bio"
              class="field__textarea"
              maxlength="80"
              placeholder="比如：最近想更了解自己一点。"
            />
          </view>
        </view>

        <view class="panel">
          <view class="panel__head">
            <text class="panel__title">可选信息</text>
            <text class="panel__subtitle">这些设置主要用于让后续反馈更贴合你。</text>
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

        <view class="action-card">
          <button class="submit" :disabled="!canSubmit" :loading="saving" @tap="submit()">
            {{ saving ? "保存中..." : "完成初始设置" }}
          </button>
          <button class="ghost-button" :disabled="saving" @tap="submit(true)">使用当前默认资料继续</button>
          <text class="hint">
            当前会话：{{ sessionUser?.nickname || "访客" }} · 完成后会自动进入首页
          </text>
        </view>
      </view>
    </view>
  </view>
</template>

<style lang="scss" scoped>
.page {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  padding: 32rpx 28rpx 48rpx;
  background:
    radial-gradient(circle at top, rgba(255, 255, 255, 0.96), rgba(255, 246, 239, 0.8) 42%, #fffaf6 100%);
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

.page__glow--gold {
  left: -140rpx;
  bottom: 180rpx;
  background: rgba(223, 176, 94, 0.14);
}

.shell {
  position: relative;
  z-index: 1;
  animation: fadeInUp 0.45s $xc-ease both;
}

.hero-card,
.panel,
.action-card {
  @include card-base;
}

.hero-card {
  padding: 32rpx 30rpx;
  background:
    linear-gradient(135deg, #7C5DBF 0%, #B57FE0 40%, #E8729A 80%, #F2A68B 100%);
  color: $xc-white;
  box-shadow: $xc-sh-lg;
  position: relative;
  overflow: hidden;

  &::before {
    content: "";
    position: absolute;
    inset: 0;
    background:
      radial-gradient(circle at 20% 80%, rgba(255, 255, 255, 0.14), transparent 50%),
      radial-gradient(circle at 80% 20%, rgba(255, 255, 255, 0.12), transparent 40%);
  }
}

.hero-card__eyebrow,
.hero-card__title,
.hero-card__body,
.hero-card__preview,
.hero-card__chips {
  position: relative;
  z-index: 1;
}

.hero-card__eyebrow {
  display: block;
  font-size: 22rpx;
  letter-spacing: 2rpx;
  opacity: 0.85;
}

.hero-card__title {
  display: block;
  margin-top: 16rpx;
  font-family: $xc-font-serif;
  font-size: 44rpx;
  line-height: 1.35;
  font-weight: 900;
}

.hero-card__body {
  display: block;
  margin-top: 16rpx;
  font-size: 26rpx;
  line-height: 1.7;
  opacity: 0.88;
}

.hero-card__preview {
  display: flex;
  gap: 16rpx;
  align-items: center;
  margin-top: 22rpx;
  padding: 18rpx;
  border-radius: 26rpx;
  background: rgba(255, 255, 255, 0.16);
}

.hero-card__avatar {
  width: 108rpx;
  height: 108rpx;
  border-radius: 30rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.18);
  font-size: 48rpx;
}

.hero-card__preview-copy {
  flex: 1;
  min-width: 0;
}

.hero-card__preview-name {
  display: block;
  font-size: 30rpx;
  font-weight: 800;
}

.hero-card__preview-role {
  display: block;
  margin-top: 8rpx;
  font-size: 22rpx;
  opacity: 0.86;
}

.hero-card__preview-bio {
  display: block;
  margin-top: 8rpx;
  font-size: 22rpx;
  line-height: 1.6;
  opacity: 0.9;
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
  background: rgba(255, 255, 255, 0.18);
  font-size: 22rpx;
}

.panel {
  padding: 28rpx;
  margin-top: 22rpx;
}

.panel__head {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
  margin-bottom: 20rpx;
}

.panel__title {
  display: block;
  font-size: 28rpx;
  font-weight: 800;
  color: $xc-ink;
}

.panel__subtitle {
  display: block;
  font-size: 23rpx;
  line-height: 1.7;
  color: $xc-muted;
}

.panel__text {
  font-size: 26rpx;
  color: $xc-muted;
}

.form {
  display: flex;
  flex-direction: column;
}

.avatar-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16rpx;
}

.avatar-option {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 108rpx;
  border-radius: 22rpx;
  background: linear-gradient(160deg, $xc-purple-p, $xc-pink-p);
  border: 2rpx solid transparent;
  transition: all 0.2s $xc-spring;

  &:active {
    transform: scale(0.93);
  }
}

.avatar-option--active {
  border-color: $xc-purple;
  background: linear-gradient(135deg, rgba(237, 229, 249, 0.95), rgba(253, 230, 239, 0.9));
  box-shadow: 0 0 16px rgba(155, 126, 216, 0.25);
  transform: scale(1.05);
}

.avatar-option__emoji {
  font-size: 46rpx;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.field + .field {
  margin-top: 20rpx;
}

.field--inline {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16rpx;
}

.field__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.field__label {
  font-size: 24rpx;
  color: $xc-muted;
  font-weight: 600;
}

.field__count {
  font-size: 22rpx;
  color: rgba(123, 110, 133, 0.78);
}

.field__input,
.field__textarea {
  width: 100%;
  padding: 20rpx 22rpx;
  border-radius: 20rpx;
  background: rgba(255, 255, 255, 0.92);
  border: 1.5px solid $xc-line;
  font-size: 26rpx;
  color: $xc-ink;
}

.field__textarea {
  min-height: 180rpx;
}

.chips {
  display: flex;
  gap: 12rpx;
  flex-wrap: wrap;
}

.chip {
  padding: 14rpx 24rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.88);
  border: 1.5px solid rgba(155, 126, 216, 0.08);
  color: $xc-muted;
  font-size: 24rpx;
  font-weight: 600;
}

.chip--active {
  background: $xc-purple;
  color: $xc-white;
  border-color: transparent;
  box-shadow: 0 4px 12px rgba(155, 126, 216, 0.25);
}

.picker-card {
  padding: 20rpx 22rpx;
  border-radius: 20rpx;
  background: rgba(255, 255, 255, 0.92);
  border: 1.5px solid $xc-line;
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

.action-card {
  margin-top: 22rpx;
  padding: 24rpx;
  display: flex;
  flex-direction: column;
  gap: 14rpx;
}

.submit,
.ghost-button {
  height: 88rpx;
  border-radius: 999rpx;
  font-size: 28rpx;
  font-weight: 700;
}

.submit {
  @include btn-primary;
  position: relative;
  overflow: hidden;
}

.ghost-button {
  background: rgba(245, 238, 255, 0.92);
  color: $xc-accent;
}

.hint {
  text-align: center;
  font-size: 22rpx;
  color: $xc-hint;
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

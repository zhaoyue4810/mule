<script setup lang="ts">
import { onMounted, ref } from "vue";

import type { AuthUserPayload } from "@/shared/models/auth";
import type { OnboardingProfilePayload } from "@/shared/models/profile";
import { fetchAuthMe, getSessionUser, setSessionUser } from "@/shared/services/auth";
import {
  fetchMyOnboardingProfile,
  updateMyOnboardingProfile,
} from "@/shared/services/profile";

const avatarOptions = ["🧠", "🌟", "🌈", "🔥", "🌙", "🪐", "🍀", "🎧"];
const genderOptions = [
  { label: "保密", value: 0 },
  { label: "男生", value: 1 },
  { label: "女生", value: 2 },
];

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

function currentYear() {
  return new Date().getFullYear();
}

async function loadOnboarding() {
  loading.value = true;
  try {
    const payload = await fetchMyOnboardingProfile();
    form.value = payload;
  } catch (error) {
    uni.showToast({
      title: error instanceof Error ? error.message : "加载失败",
      icon: "none",
    });
  } finally {
    loading.value = false;
  }
}

async function submit() {
  if (saving.value) {
    return;
  }
  saving.value = true;
  try {
    await updateMyOnboardingProfile({
      nickname: form.value.nickname,
      avatar_value: form.value.avatar_value,
      bio: form.value.bio,
      gender: form.value.gender,
      birth_year: form.value.birth_year || null,
      birth_month: form.value.birth_month || null,
    });
    const user = await fetchAuthMe();
    setSessionUser(user);
    sessionUser.value = user;
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
  loadOnboarding();
});
</script>

<template>
  <view class="page">
    <view class="hero">
      <text class="hero__eyebrow">Onboarding</text>
      <text class="hero__title">先用 30 秒，给你的心测旅程一个起点。</text>
      <text class="hero__body">
        这些信息会用来完善你的个人中心和后续成长反馈，不会影响你立刻开始测试。
      </text>
    </view>

    <view v-if="loading" class="panel">
      <text class="panel__text">正在加载你的初始资料...</text>
    </view>

    <view v-else class="form">
      <view class="panel">
        <text class="panel__title">选择你的头像</text>
        <view class="avatar-grid">
          <view
            v-for="item in avatarOptions"
            :key="item"
            class="avatar-option"
            :class="{ 'avatar-option--active': form.avatar_value === item }"
            @tap="form.avatar_value = item"
          >
            <text class="avatar-option__emoji">{{ item }}</text>
          </view>
        </view>
      </view>

      <view class="panel">
        <text class="panel__title">基础资料</text>
        <view class="field">
          <text class="field__label">昵称</text>
          <input v-model="form.nickname" class="field__input" maxlength="20" placeholder="给自己起个名字" />
        </view>
        <view class="field">
          <text class="field__label">一句介绍</text>
          <textarea
            v-model="form.bio"
            class="field__textarea"
            maxlength="80"
            placeholder="比如：最近想更了解自己一点。"
          />
        </view>
      </view>

      <view class="panel">
        <text class="panel__title">可选信息</text>
        <view class="field">
          <text class="field__label">性别</text>
          <view class="chips">
            <view
              v-for="item in genderOptions"
              :key="item.value"
              class="chip"
              :class="{ 'chip--active': form.gender === item.value }"
              @tap="form.gender = item.value"
            >
              <text>{{ item.label }}</text>
            </view>
          </view>
        </view>
        <view class="field field--inline">
          <view class="field__half">
            <text class="field__label">出生年份</text>
            <input
              v-model.number="form.birth_year"
              class="field__input"
              type="number"
              :placeholder="String(currentYear())"
            />
          </view>
          <view class="field__half">
            <text class="field__label">出生月份</text>
            <input
              v-model.number="form.birth_month"
              class="field__input"
              type="number"
              placeholder="1-12"
            />
          </view>
        </view>
      </view>

      <button class="submit" :loading="saving" @tap="submit">
        {{ saving ? "保存中..." : "完成初始设置" }}
      </button>
      <text class="hint">
        当前会话：{{ sessionUser?.nickname || "访客" }} · 完成后会自动进入首页
      </text>
    </view>
  </view>
</template>

<style lang="scss" scoped>
.page {
  padding: 32rpx 28rpx 48rpx;
  animation: fadeInUp 0.45s $xc-ease both;
}

.hero {
  padding: 40rpx 32rpx;
  border-radius: $xc-r-xl;
  background: linear-gradient(135deg, #7C5DBF 0%, #B57FE0 40%, #E8729A 80%, #F2A68B 100%);
  color: $xc-white;
  box-shadow: $xc-sh-lg;
  position: relative;
  overflow: hidden;

  &::before {
    content: "";
    position: absolute;
    inset: 0;
    background:
      radial-gradient(circle at 20% 80%, rgba(255, 255, 255, 0.15), transparent 50%),
      radial-gradient(circle at 80% 20%, rgba(255, 255, 255, 0.12), transparent 40%);
  }
}

.hero__eyebrow {
  display: block;
  position: relative;
  z-index: 1;
  font-size: 22rpx;
  letter-spacing: 2rpx;
  opacity: 0.85;
}

.hero__title {
  display: block;
  position: relative;
  z-index: 1;
  margin-top: 16rpx;
  font-family: $xc-font-serif;
  font-size: 44rpx;
  line-height: 1.35;
  font-weight: 900;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.hero__body {
  display: block;
  position: relative;
  z-index: 1;
  margin-top: 16rpx;
  font-size: 26rpx;
  line-height: 1.7;
  opacity: 0.88;
}

.form {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
  margin-top: 24rpx;
}

.panel {
  padding: 28rpx;
  border-radius: $xc-r-lg;
  @include glass;
  box-shadow: $xc-sh-md;
}

.panel__title {
  display: block;
  font-size: 28rpx;
  font-weight: 800;
  color: $xc-ink;
}

.panel__text {
  font-size: 26rpx;
  color: $xc-muted;
}

.avatar-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16rpx;
  margin-top: 20rpx;
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
  margin-top: 20rpx;
}

.field--inline {
  flex-direction: row;
  gap: 16rpx;
}

.field__half {
  flex: 1;
}

.field__label {
  font-size: 24rpx;
  color: $xc-muted;
  font-weight: 600;
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
  transition: border-color 0.3s;

  &:focus {
    border-color: $xc-purple-l;
    box-shadow: 0 0 12px rgba(155, 126, 216, 0.12);
  }
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
  transition: all 0.2s;

  &:active {
    transform: scale(0.96);
  }
}

.chip--active {
  background: $xc-purple;
  color: $xc-white;
  border-color: transparent;
  box-shadow: 0 4px 12px rgba(155, 126, 216, 0.25);
}

.submit {
  margin-top: 8rpx;
  height: 88rpx;
  border-radius: 999rpx;
  @include btn-primary;
  font-size: 30rpx;
  font-weight: 700;
  position: relative;
  overflow: hidden;

  &::after {
    content: "";
    position: absolute;
    inset: 0;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.25), transparent);
    background-size: 200% 100%;
    animation: shimmer 2.5s infinite;
  }
}

.hint {
  text-align: center;
  font-size: 22rpx;
  color: $xc-hint;
}
</style>

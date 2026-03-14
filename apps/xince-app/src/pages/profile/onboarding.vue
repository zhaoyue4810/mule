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
}

.hero {
  padding: 36rpx 32rpx;
  border-radius: 30rpx;
  background:
    radial-gradient(circle at top right, rgba(255, 242, 225, 0.95), rgba(255, 218, 191, 0.92)),
    linear-gradient(140deg, #fff8ef, #ffd9c4);
  box-shadow: $xc-shadow;
}

.hero__eyebrow {
  display: block;
  font-size: 22rpx;
  color: $xc-accent;
  letter-spacing: 2rpx;
  text-transform: uppercase;
}

.hero__title {
  display: block;
  margin-top: 16rpx;
  font-size: 42rpx;
  line-height: 1.35;
  font-weight: 600;
  color: $xc-ink;
}

.hero__body {
  display: block;
  margin-top: 16rpx;
  font-size: 26rpx;
  line-height: 1.7;
  color: $xc-muted;
}

.form {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
  margin-top: 24rpx;
}

.panel {
  padding: 28rpx;
  border-radius: 26rpx;
  background: rgba(255, 255, 255, 0.86);
  border: 2rpx solid rgba(217, 111, 61, 0.08);
  box-shadow: $xc-shadow;
}

.panel__title {
  display: block;
  font-size: 28rpx;
  font-weight: 600;
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
  background: rgba(255, 245, 236, 0.8);
  border: 2rpx solid transparent;
}

.avatar-option--active {
  border-color: $xc-accent;
  background: rgba(255, 236, 223, 0.96);
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
}

.field__input,
.field__textarea {
  width: 100%;
  padding: 20rpx 22rpx;
  border-radius: 20rpx;
  background: rgba(255, 249, 243, 0.92);
  border: 2rpx solid rgba(217, 111, 61, 0.08);
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
  padding: 12rpx 20rpx;
  border-radius: 999rpx;
  background: rgba(255, 245, 236, 0.86);
  color: $xc-muted;
  font-size: 24rpx;
}

.chip--active {
  background: $xc-accent-soft;
  color: $xc-accent;
}

.submit {
  margin-top: 8rpx;
  border-radius: 999rpx;
  background: linear-gradient(135deg, #d96f3d, #bf5321);
  color: #fff7f0;
}

.hint {
  text-align: center;
  font-size: 22rpx;
  color: $xc-muted;
}
</style>

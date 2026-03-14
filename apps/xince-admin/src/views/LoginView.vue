<script setup lang="ts">
import { reactive, ref } from "vue";
import { ElMessage } from "element-plus";
import { useRouter } from "vue-router";

import { loginAdmin } from "@/services/admin";

const router = useRouter();
const form = reactive({ username: "", password: "" });
const loading = ref(false);

async function login() {
  if (!form.username || !form.password || loading.value) {
    return;
  }
  loading.value = true;
  try {
    const payload = await loginAdmin(form.username, form.password);
    window.localStorage.setItem("xc_admin_token", payload.access_token);
    router.push("/dashboard");
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : "登录失败");
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="login">
    <el-card class="login__card">
      <h2>XinCe Admin</h2>
      <el-form label-position="top" @submit.prevent>
        <el-form-item label="用户名">
          <el-input v-model="form.username" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" show-password @keyup.enter="login" />
        </el-form-item>
        <el-button type="primary" :loading="loading" style="width: 100%" @click="login">
          {{ loading ? "登录中..." : "登录" }}
        </el-button>
      </el-form>
    </el-card>
  </div>
</template>

<style scoped>
.login { min-height: 100vh; display:flex; align-items:center; justify-content:center; background:#f6efe8; }
.login__card { width: 420px; }
</style>

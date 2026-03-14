<script setup lang="ts">
import { reactive } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();
const form = reactive({ username: "admin", password: "xince-admin" });

function login() {
  if (!form.username || !form.password) {
    return;
  }
  window.sessionStorage.setItem("xc_admin_authed", "1");
  router.push("/dashboard");
}
</script>

<template>
  <div class="login">
    <el-card class="login__card">
      <h2>XinCe Admin</h2>
      <el-form label-position="top">
        <el-form-item label="用户名">
          <el-input v-model="form.username" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" show-password />
        </el-form-item>
        <el-button type="primary" style="width: 100%" @click="login">登录</el-button>
      </el-form>
    </el-card>
  </div>
</template>

<style scoped>
.login { min-height: 100vh; display:flex; align-items:center; justify-content:center; background:#f6efe8; }
.login__card { width: 420px; }
</style>

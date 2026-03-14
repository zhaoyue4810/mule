<script setup lang="ts">
import { useRouter, useRoute } from "vue-router";

const router = useRouter();
const route = useRoute();
const menus = [
  { label: "仪表盘", path: "/dashboard" },
  { label: "测试管理", path: "/tests" },
  { label: "内容导入", path: "/imports" },
  { label: "用户管理", path: "/users" },
  { label: "AI 工作台", path: "/ai" },
  { label: "勋章配置", path: "/badges" },
  { label: "系统设置", path: "/settings" },
];

function logout() {
  window.localStorage.removeItem("xc_admin_token");
  router.push("/login");
}
</script>

<template>
  <el-container class="shell">
    <el-aside width="220px" class="shell__aside">
      <div class="shell__logo">XinCe Admin</div>
      <el-menu :default-active="route.path" router>
        <el-menu-item v-for="item in menus" :key="item.path" :index="item.path">
          {{ item.label }}
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="shell__header">
        <div>心测管理后台</div>
        <el-button text @click="logout">退出</el-button>
      </el-header>
      <el-main class="shell__main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.shell { min-height: 100vh; }
.shell__aside { background: #fffaf6; border-right: 1px solid #ecd9c7; }
.shell__logo { padding: 20px; font-size: 20px; font-weight: 700; color: #b85b2b; }
.shell__header { display:flex; justify-content:space-between; align-items:center; background:#fff; border-bottom:1px solid #f0e2d6; }
.shell__main { background:#f7f4ef; }
</style>

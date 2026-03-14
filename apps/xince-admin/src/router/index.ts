import { createRouter, createWebHistory } from "vue-router";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/login", component: () => import("@/views/LoginView.vue") },
    {
      path: "/",
      component: () => import("@/views/AppShell.vue"),
      children: [
        { path: "", redirect: "/dashboard" },
        { path: "dashboard", component: () => import("@/views/DashboardView.vue") },
        { path: "tests", component: () => import("@/views/TestsView.vue") },
        { path: "imports", component: () => import("@/views/ImportsView.vue") },
        { path: "users", component: () => import("@/views/UsersView.vue") },
        { path: "ai", component: () => import("@/views/AiWorkbenchView.vue") },
        { path: "badges", component: () => import("@/views/BadgesView.vue") },
        { path: "settings", component: () => import("@/views/SystemSettingsView.vue") },
      ],
    },
  ],
});

router.beforeEach((to) => {
  const authed = Boolean(window.localStorage.getItem("xc_admin_token"));
  if (to.path !== "/login" && !authed) {
    return "/login";
  }
  if (to.path === "/login" && authed) {
    return "/dashboard";
  }
  return true;
});

export default router;

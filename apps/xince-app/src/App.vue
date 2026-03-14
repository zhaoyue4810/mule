<script setup lang="ts">
import { onLaunch, onShow } from "@dcloudio/uni-app";

import { ensureAppSession } from "@/shared/services/auth";

onLaunch(() => {
  console.log("XinCe app launched");
  ensureAppSession()
    .then((user) => {
      if (!user.onboarding_completed) {
        uni.reLaunch({
          url: "/pages/profile/onboarding",
        });
      }
    })
    .catch((error) => {
      console.warn("Failed to establish session on launch", error);
    });
});

onShow(() => {
  console.log("XinCe app visible");
});
</script>

<style lang="scss">
@import "./uni.scss";

page {
  background:
    radial-gradient(circle at top, rgba(255, 232, 210, 0.9), transparent 34%),
    linear-gradient(180deg, #fffaf4 0%, #f7efe4 100%);
  color: #2b2118;
  font-family: "Avenir Next", "PingFang SC", "Microsoft YaHei", sans-serif;
}

view,
text,
button {
  box-sizing: border-box;
}
</style>

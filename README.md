# dual_steer_ws

此仓库目前保存基于用户上传的 `dual_steer_ws.zip` 制作的补丁，**不包含完整 ROS 工作区源码**。在已有完整 `~/dual_steer_ws` 的小车电脑上使用补丁。

- [2026-10-13 新上传源码的 MPC 代码更新包](downloads/mpc_4m_0p2_overlay.zip)：含核对和备份脚本，不上传包含固定 RTK 原点的完整路线文件。先看[使用说明](downloads/mpc_4m_0p2_overlay_README.md)。
- [MPC 前视 4 m、速度 0.2 m/s、路径刷新补丁](patches/mpc_4m_0p2/README.md)：可下载 ZIP，或直接下载 `.patch`。
- [P1 重新发车与停车点修复补丁](patches/route_restart_at_p1/README.md)：独立于上面的 MPC 补丁。

先按各补丁说明运行 `patch --dry-run`。若小车电脑上的文件与上传版本不同，停止应用并检查差异；不要用补丁覆盖现有路线点。

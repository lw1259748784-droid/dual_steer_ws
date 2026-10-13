# MPC 4 m / 0.2 m/s 代码更新包

这个包基于 2026-10-13 用户新上传的 `dual_steer_ws.zip` 制作，包含 9 个修改后的源代码或配置文件，以及校验和应用脚本。为保护本机路线和固定 RTK 原点，包里**不含** `routes/current_route.yaml` 或 `routes/rtk_origin.yaml`。

在小车电脑上停下导航，解压 ZIP，然后执行：

```bash
cd ~/Downloads/mpc_4m_0p2_overlay
python3 apply_to_workspace.py ~/dual_steer_ws
```

脚本先核对本机 9 个文件是否与这次上传版本一致。若有差异，会停止并报告文件，不强制覆盖。通过后仅更新对应文件，并把 `routes/current_route.yaml` 中的转弯 `speed_limit` 元数据改为 `0.20`；P7 STOP、所有 P 点坐标与类型保持不变。原文件会备份到工作区旁边的时间戳目录。

随后重新构建并重启节点：

```bash
source /opt/ros/humble/setup.bash
cd ~/dual_steer_ws
colcon build --symlink-install --packages-select dual_steer_mpc_controller rviz_path_editor rviz_route_editor_panel nav2_humble
source install/setup.bash
```

运行中从磁盘刷新路线：

```bash
ros2 service call /path_editor/load std_srvs/srv/Trigger '{}'
```

STOP 点类型或坐标改变后，仍需在停车后重启 `work_stop_supervisor`，因为它只在启动时读取停车点。此更新包未在实车或 ROS 2 Humble 上运行；已对上传源码完成参数、XML、脚本和 P7 STOP 检查。

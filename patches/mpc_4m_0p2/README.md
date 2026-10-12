# MPC 4 m 前视、0.2 m/s 速度与随时刷新路线

此补丁以用户上传的 `dual_steer_ws.zip` 为基准。当前云环境没有 ROS 2 Humble，以下 ROS 构建和实车运行步骤需在小车电脑执行。补丁与先前的 `route_restart_at_p1.patch` 修改不同文件，可分别应用；若实车文件与压缩包不同，先检查差异，不要强制套用。

改动包括：两份 Nav2 参数与参数生成脚本将 `FollowPath.seed_lookahead_dist` 设为 4.0 m，巡航目标/上限设为 0.20 m/s，速度平滑器的前进上限也设为 0.20 m/s；MPC 插件的默认值同步。路线编辑器、面板、附带的安装副本及上传路线中的转弯速度元数据设为 0.20 m/s。`reference_path_length` 原本就是 4.0 m，保持不变。导航行为树由每走 1 m 重规划改为每秒重规划，以便活动中的导航任务及时取得重载的路径。

**0.20 m/s 是行进上限，不代表小车会在转弯、接近停车点或定位误差较大时恒速行驶；停车仍应为 0。** 当前编辑器的 `speed_limit` 只是路线元数据，不直接控制 MPC。4 m 前视大于 2.8 m 最小转弯半径，可能使弯道切角或转向偏晚，应在空旷场地先低速观察实测转角和 `/cmd_vel`。

## 安装

在小车电脑上让车辆停稳并退出相关节点，备份当前源码，将补丁复制过去后执行：

```bash
cd /home/tl/dual_steer_ws
cp -a src/nav2_humble /home/tl/nav2_humble_before_4m_0p2
cp -a routes/current_route.yaml /home/tl/current_route_before_4m_0p2.yaml
patch -p1 --dry-run < /path/to/mpc_4m_0p2_and_refresh.patch
patch -p1 < /path/to/mpc_4m_0p2_and_refresh.patch
source /opt/ros/humble/setup.bash
colcon build --symlink-install --packages-select dual_steer_mpc_controller rviz_path_editor rviz_route_editor_panel nav2_humble
source install/setup.bash
```

重新启动 Nav2、路径编辑器和 RViz。启动时确认使用了更新的参数文件；默认启动脚本加载 `nav2_params_dual_steer_no_map.yaml`。若你显式传了 `params_file:=.../nav2_params_dual_steer_mpc_tracking.yaml`，该文件也已经修改。检查运行参数：

```bash
ros2 param get /controller_server FollowPath.seed_lookahead_dist
ros2 param get /controller_server FollowPath.max_speed
ros2 param get /velocity_smoother max_velocity
ros2 action list -t
```

期望分别看到 4.0、0.2、第一项为 0.2 的列表，以及 `/navigate_to_pose` action。若实际加载的是别的 Nav2 参数文件，还需修改那个文件。

## 随时从磁盘刷新路线

路径编辑器运行时，在任何终端执行：

```bash
source /opt/ros/humble/setup.bash
source /home/tl/dual_steer_ws/install/setup.bash
ros2 service call /path_editor/load std_srvs/srv/Trigger '{}'
```

服务返回 `success: true` 表示已从 `/home/tl/dual_steer_ws/routes/current_route.yaml` 重建并发布 `/global_path`；新行为树会在约 1 秒内触发重规划。若在 RViz 中修改了点但尚未保存，先调用 `/path_editor/save`，否则 `/load` 会以磁盘内容覆盖未保存的编辑。执行后可用 `ros2 topic echo /global_path --once` 和 RViz 中的路线确认结果。活动导航任务仍保留原导航终点；若终点也改了，需要取消旧目标并下达新目标。若新路线离当前车辆太远或方向不符，规划器会拒绝继续，车辆应先停稳再调整路线。

`/path_editor/load` 刷新几何路线，不会解除 P2/P3/P4/P7 停车等待，也不会重新发车。`work_stop_supervisor` 只在自身启动时读取 STOP 点；如果修改了 STOP 类型或坐标，需停车后重启工作控制节点再加载新的停车表，不能仅靠上面的刷新命令。车辆已回到 P1、要重跑整条路线时，使用先前补丁提供的 `ros2 run calf_work_control restart_route_at_p1 --wait-seconds 30`。

## 已验证

补丁对上传的源码 `patch --dry-run` 成功；两份 YAML、路线 YAML、行为树 XML 可解析；参数生成脚本在临时工作区运行后产出 4 m/0.2 m/s 的一致参数。云环境没有 ROS 2 Humble，未运行 `colcon build`、Nav2 节点或实车测试。

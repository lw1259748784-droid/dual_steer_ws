# P1 单次重新发车与停靠点修复补丁

此补丁基于上传的 `dual_steer_ws.zip` 中 `src/calf_work_control` 制作；它**没有**在实车电脑或 ROS 2 Humble 上运行。先比较实车源码与上传版本，若 `patch --dry-run` 失败，请勿强制覆盖。

## 修复内容

- 停车控制除了检查距离小于 0.15 m，还在接近目标点后检查是否越过目标点的垂线。这样车辆沿路线经过 P2/P3/P4、但横向误差稍大时，不会一直卡在 P2。
- `/odom` 或 `/wheel_odom` 失去更新时，停车控制保持零速度；速度门控丢失停车控制心跳时，也保持零速度。
- 新增单次指令 `restart_route_at_p1`：确认车辆在 P1、车头沿 P1→P2、已停稳、RTK Fixed 和 CAN 反馈正常、Nav2 action server 可用且 CAN 订阅 `/cmd_vel_final` 后，取消旧任务、加载路线、重置规划与停车进度、发送到最后一个路线点的新任务。新任务被接受前，停车控制一直保持零速度。

这个指令只在**运行时执行一次**，不会在车辆每次经过 P1 时自动发车。它从 P1 重新跑整条路线，不能从半路接续未完成的部分。

## 在实车电脑安装

车停稳、取消当前 Nav2 任务并停止旧的 `calf_work_control` 后，先备份源码。将补丁复制到实车电脑，再执行：

```bash
cd /home/tl/dual_steer_ws
cp -a src/calf_work_control /home/tl/calf_work_control_before_restart_patch
patch -p1 --dry-run < /path/to/route_restart_at_p1.patch
patch -p1 < /path/to/route_restart_at_p1.patch
source /opt/ros/humble/setup.bash
colcon build --symlink-install --packages-select calf_work_control
source install/setup.bash
```

确认实车运行的是更新后的停车控制和门控，且只有一份 CAN 控制节点。底盘 CAN 必须订阅 `/cmd_vel_final`：

```bash
ros2 launch calf_work_control work_control.launch.py
ros2 launch ackermann_can_driver ackermann_can_controller.launch.py \
  can_interface:=can0 cmd_vel_topic:=/cmd_vel_final \
  params_file:=/home/tl/dual_steer_ws/src/ackermann_can_driver/config/feedback_params_mpc_tracking.yaml
```

Nav2 仍按原工程启动。此前出现过 `/navigate_to_pose` action server 不可用的错误；必须先确认 `ros2 action list -t` 中有 `/navigate_to_pose`。补丁不会修复 Nav2 自身启动失败。

## 单次重新发车

车辆回到 P1，定位稳定、车头朝向 P2、底盘已停稳后执行：

```bash
source /opt/ros/humble/setup.bash
source /home/tl/dual_steer_ws/install/setup.bash
ros2 run calf_work_control restart_route_at_p1 --wait-seconds 30
```

若有任一条件不满足，指令报错退出，不发送新的导航目标。可用 `ros2 topic echo /work_target_point --once` 确认停车顺序已重新指向 P2；用 `ros2 topic echo /work_state --once` 检查状态。P7 若要停靠，仍需在实际使用的 `routes/current_route.yaml` 中设为 `type: hutch_stop`，并重新加载路线。

## 验证范围

已经完成 Python 语法、配置文件解析、补丁干运行，以及对重置/保持/放行、停车线越过和心跳失效的逻辑测试。ROS 2 Humble、Nav2 action 交互、RTK/CAN 话题连线和实车转弯仍需在实车电脑验证；先让驱动轮离地或在空旷场地低速测试。

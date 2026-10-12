#!/usr/bin/env python3
"""Apply the 4 m MPC lookahead and 0.2 m/s cap in an existing workspace."""

from pathlib import Path
import re
import shutil

root = Path.cwd()
if not (root / 'src/nav2_humble/package.xml').is_file():
    raise SystemExit('请先 cd 到 dual_steer_ws 工作区根目录')

pending = {}


def edit(path, updates, required=True):
    target = root / path
    if not target.is_file():
        if required:
            raise SystemExit(f'缺少文件: {target}')
        return
    data = target.read_text(encoding='utf-8')
    for pattern, replacement in updates:
        data, count = re.subn(pattern, replacement, data, count=1, flags=re.MULTILINE)
        if count != 1:
            if not required:
                print(f'跳过结构不同的附加文件: {target}')
                return
            raise SystemExit(f'未找到预期设置，请不要强制覆盖: {target}: {pattern}')
    pending[target] = data


num = r'[-+]?\d+(?:\.\d+)?'
for name in ('nav2_params_dual_steer_no_map.yaml',
             'nav2_params_dual_steer_mpc_tracking.yaml'):
    edit('src/nav2_humble/config/' + name, [
        (rf'(^[ \t]*desired_speed:[ \t]*){num}', r'\g<1>0.20'),
        (rf'(^[ \t]*max_speed:[ \t]*){num}', r'\g<1>0.20'),
        (rf'(^[ \t]*seed_lookahead_dist:[ \t]*){num}', r'\g<1>4.0'),
        (rf'(^[ \t]*max_velocity:[ \t]*\n(?:[ \t]*\n)*[ \t]*-[ \t]*){num}',
         r'\g<1>0.20'),
    ])

edit('src/nav2_humble/behavior_trees/navigate_to_pose_dual_steer.xml', [
    (r'<DistanceController distance="[^"]+">', '<RateController hz="1.0">'),
    (r'</DistanceController>', '</RateController>'),
])

edit('tools/apply_mpc_tracking_parameters.py', [
    (rf"('desired_speed':[ \t]*){num}", r'\g<1>0.20'),
    (rf"('max_speed':[ \t]*){num}", r'\g<1>0.20'),
    (rf"('seed_lookahead_dist':[ \t]*){num}", r'\g<1>4.0'),
])
generator = root / 'tools/apply_mpc_tracking_parameters.py'
if pending[generator].count("    follow['control_dt'] = 1.0 / frequency\n") != 1:
    raise SystemExit(f'参数生成脚本结构不同，请不要强制覆盖: {generator}')
pending[generator] = pending[generator].replace(
    '    follow[\'control_dt\'] = 1.0 / frequency\n',
    '    follow[\'control_dt\'] = 1.0 / frequency\n'
    '    nav[\'velocity_smoother\'][\'ros__parameters\'][\'max_velocity\'][0] = 0.20\n',
    1)

edit('src/dual_steer_mpc_controller/src/mpc_controller.cpp', [
    (rf'(declare_double\("desired_speed",[ \t]*){num}', r'\g<1>0.20'),
    (rf'(declare_double\("max_speed",[ \t]*){num}', r'\g<1>0.20'),
    (rf'(declare_double\("seed_lookahead_dist",[ \t]*){num}', r'\g<1>4.0'),
])

for name in ('src/rviz_path_editor/src/rviz_path_editor_node.cpp',
             'src/rviz_route_editor_panel_bundle/patched_rviz_path_editor/rviz_path_editor_node.cpp'):
    edit(name, [
        (rf'(declare_parameter<double>\("turn_speed_limit",[ \t]*){num}',
         r'\g<1>0.20'),
        (rf'(double speed_limit\{{){num}(\}};)', r'\g<1>0.20\g<2>'),
    ], required=False)

edit('src/rviz_route_editor_panel_bundle/rviz_route_editor_panel/src/route_editor_panel.cpp', [
    (rf'(speed_spin_->setValue\(){num}(\);)', r'\g<1>0.20\g<2>'),
], required=False)

for name in ('routes/current_route.yaml',
             'src/rviz_route_editor_panel_bundle/example_semantic_route.yaml'):
    edit(name, [(rf'(^[ \t]*speed_limit:[ \t]*){num}', r'\g<1>0.20')], required=False)

for target, data in pending.items():
    if target.read_text(encoding='utf-8') == data:
        continue
    backup = target.with_name(target.name + '.before_4m_0p2')
    if not backup.exists():
        shutil.copy2(target, backup)
    temp = target.with_name(target.name + '.tmp_4m_0p2')
    temp.write_text(data, encoding='utf-8')
    temp.replace(target)
    print('已修改:', target.relative_to(root))
print('完成。请重新构建并重启 Nav2 和路径编辑器。')

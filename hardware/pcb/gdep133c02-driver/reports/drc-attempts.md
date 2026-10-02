# DRC和应用打开尝试记录

日期2026-10-01，KiCad CLI10.0.6，macOS当前受限执行环境。

执行`kicad-cli pcb drc gdep133c02-driver.kicad_pcb --format json`（也尝试`--schematic-parity`）均以SIGABRT/退出码134结束，没有产生有效报告。macOS崩溃栈包含`wxGetMousePosition`、`TOOL_MANAGER::doRunAction`、`BOARD_COMMIT::Push`、`PCBNEW_JOBS_HANDLER::JobExportDrc`。不将这个结果标为DRC通过。

内置Python尝试`pcbnew.WriteDRCReport`也因缺少独立进程PGM运行环境而失败，不能替代CLI结果。

电脑控制工具针对`/Applications/KiCad/KiCad.app`及`com.google.Chrome`返回“Computer Use was not approved”。用户已表示授权；重载工具后仍未生效。没有通过其他系统自动化绕过此限制。

原理图ERC可以执行且零违规；PDF、网表、SVG及初步STEP可以导出。这些仅证明相应导出过程可执行，不证明PCB电气和制造检查通过。

下一次必须在可用KiCad应用里实际打开工程、执行完整DRC、原理图一致性检查及Gerber预览，并保存真实报告。当前尚有未完成布线，预期会发现连接及其他违规，不能因CLI环境问题忽略。

## Codex重启后的复测

2026-10-01，KiCad与Chrome应用访问已恢复。当前非沙箱执行环境下，CLI完整DRC（含原理图一致性及重新铺铜）成功完成，退出码5，报告保存为`drc-restart-check.json`：238条违规、53个未连接项目、196个原理图一致性问题。此前程序崩溃的阻塞已解除，但PCB未通过检查；工程在GUI中的实际打开验证尚待完成。

## 当前修复结果

权限和CLI执行已恢复，原理图与PCB实际打开验证完成。最终drc.json为零违规/未连接/一致性问题，GUI另检零违规/未连接/忽略测试；五项默认忽略规则全部启用为warning后也已修复，未设置排除。历史失败与中间报告保留，不代表当前状态。

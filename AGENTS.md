# 项目工程约定

PCB 工程使用 KiCad 设计，在嘉立创生产，放在 `hardware/pcb/`；结构工程放在 `mechanical/`。所有工程在本项目目录下组织，使用当前 Git 仓库管理。总体设计见 `docs/design/overview.md`。

## PCB 工程

正式 PCB 设计使用 KiCad 原生工程，保存 `.kicad_pro`、`.kicad_sch`、`.kicad_pcb`，并将自定义符号、封装和必要的模型引用随工程管理。记录实际 KiCad 版本，检查 ERC/DRC，并输出嘉立创所需的 Gerber、钻孔、BOM 和贴片坐标文件。

`hardware/pcb/examples/skill-demo/` 是此前 EasyEDA 路线的历史初始化示例，不作为正式设计或后续工程格式参考。正式项目不依赖 EasyEDA 技能。文件格式检查不能替代电气检查、PCB DRC 和实际工程打开验证。

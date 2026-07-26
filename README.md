# MS-CASTEP-PL-Generator

一个可移植的 Codex skill，用于从指定 XSD 结构生成自包含的 Materials Studio
MaterialsScript PL/XSD 任务包。它面向 CASTEP 几何优化、自旋筛选和
48 核服务器任务，尤其适合金属-石墨烯缺陷体系中容易出现 SCF 振荡的计算。

## 主要特性

- 每个 PL 精确绑定自己的 XSD，不依赖当前活动文档；
- 运行前核对原子数，避免错用结构；
- 默认采用固定总自旋、BFGS、阻尼 Pulay 混合和较宽 smearing；
- 使用短任务名，降低 Materials Studio 远程路径过长的风险；
- 结果通过 MaterialsScript `SaveAs` 返回，不再用普通 Perl `open()` 写
  Materials Studio 虚拟路径；
- 不保存 Gateway、账号、密码、许可证或作者计算机路径；
- 只准备任务包，Gateway 和服务器队列始终由用户在 Materials Studio 中手动选择。

## 环境要求

生成任务包只需要：

- Windows 10/11；
- PowerShell 5.1 或更高版本；
- Python 3.7 或更高版本（建议使用仍受支持的 3.8+ 版本）。

真正提交 CASTEP 任务还需要：

- BIOVIA Materials Studio 与 MaterialsScript；
- CASTEP 组件和有效许可证；
- 管理员已配置、可在 `Run on Server` 中选择的 Gateway/队列。

完整说明见
[环境配置说明](references/environment-setup.zh-CN.md)。

## 快速开始

1. 将本仓库克隆或下载到本机。
2. 双击 `Configure-CASTEP-PL-Skill.bat`，生成本机专用配置。
3. 双击 `Generate-CASTEP-PL-Package.bat`。
4. 输入源 XSD、计算名、自旋值、核心数和输出目录。
5. 将每个任务目录中的 XSD 与 PL 一起导入同一个 Materials Studio 项目目录。
6. 在 Materials Studio 中运行 PL，手动选择 Gateway 和服务器队列。

也可直接运行：

```powershell
python scripts\generate_castep_pl_package.py `
  --xsd "D:\models\BLG_Co_C3.xsd" `
  --output-dir "D:\prepared\Co_C3" `
  --calculation-name "Co_C3" `
  --spins 1 3 5 `
  --cores 48
```

默认生成固定自旋任务。只有在明确需要释放总自旋时才使用
`--spin-mode relaxed`。

## 默认稳健参数

- PBE + TS 色散修正；
- OTFG ultrasoft 赝势；
- 326.5 eV 截断能；
- Gamma 点；
- 固定总自旋；
- BFGS 几何优化；
- 最大 500 个 SCF 循环；
- Pulay 电荷/自旋混合振幅 0.05/0.08；
- DIIS 历史长度 5；
- Gaussian smearing 0.2 eV；
- 最大 150 个几何优化步骤。

这些参数是可靠起点，不代替针对具体体系进行截断能、k 点和物理模型的收敛验证。

## 验证

```powershell
python -m unittest discover -s tests -v
```

测试会检查固定/释放自旋、原子数绑定、短名称、结果保存方式以及防止本地误运行的保护逻辑。

## 安全边界

本仓库不会自动选择 Gateway，也不会自动提交远程作业。生成的 PL 在 Windows
本地执行时默认停止，避免误把本应交给服务器的计算跑在本机。只有明确需要本地运行时，
才可在生成阶段加入 `--allow-local`。

## 许可证

[MIT](LICENSE)

# 环境与配置说明

## 1. 生成 PL/XSD 包所需环境

- Windows 10/11；
- PowerShell 5.1 或更高版本；
- Python 3.7 或更高版本（建议使用仍受支持的 3.8+ 版本）；
- 本 skill 的完整目录，至少包含：
  - `Configure-CASTEP-PL-Skill.bat`；
  - `Generate-CASTEP-PL-Package.bat`；
  - `scripts/generate_castep_pl_package.py`；
  - `scripts/configure-castep-pl-skill.ps1`。

仅生成任务包不需要启动 Materials Studio，也不需要 Gateway。

## 2. 真正运行计算所需环境

- BIOVIA Materials Studio，包含 MaterialsScript；
- CASTEP 组件及有效许可证；
- 已由管理员配置、可在 `Run on Server` 中选择的 Gateway/队列；
- 对应服务器上的核数和队列权限。

典型 MaterialsScript 运行时位置为：

```text
<MS_INSTALL_ROOT>\etc\Scripting\bin\RunMatScript.bat
```

实际安装根目录因 Materials Studio 版本和安装位置而异，不能硬编码。

## 3. 首次配置

双击：

```text
Configure-CASTEP-PL-Skill.bat
```

脚本会：

1. 查找并验证 Python 3.7+；
2. 可选检查 Materials Studio 的 `RunMatScript.bat`；
3. 询问默认任务输出目录；
4. 设置默认核心数48；
5. 生成：

   ```text
   config\pl-skill.local.bat
   ```

该文件只保存本机路径，不应提交到 GitHub。

## 4. 生成任务包

双击：

```text
Generate-CASTEP-PL-Package.bat
```

按提示输入：

- 源XSD完整路径；
- 简短英文计算名；
- 初始自旋，例如 `1 3`；
- 核心数；
- 输出目录。

默认生成固定自旋、48核、BFGS、阻尼Pulay混合的任务包。生成过程不会
启动 Materials Studio，也不会提交远程作业。

## 5. 手动提交

对每个生成任务：

1. 将同一任务目录内的XSD和PL一起导入同一Materials Studio项目目录；
2. 打开XSD确认结构；
3. 打开PL，按 `Ctrl+F5`；
4. 手动选择 Gateway 和队列；
5. 核对核心数；
6. 提交后记录 Job ID。

不得把 Gateway、服务器密码、SSH密钥或许可证信息写入PL、BAT或公开仓库。

## 6. 成功判据

脚本成功时应返回：

```text
opt.xsd
report.txt
```

PL输出应出现：

```text
RESULT status=completed
```

如果 CASTEP 报告显示：

```text
Geometry optimization completed successfully
```

但旧任务在 Job Control 中显示 `Failed`，应检查 `.pl.out`。旧版脚本可能在
计算成功后用普通Perl `open()`写Materials Studio虚拟路径，导致包装脚本失败。
本版本已经移除该问题。

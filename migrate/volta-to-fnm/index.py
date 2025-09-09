# @see: https://github.com/Schniz/fnm/issues/1056
import argparse
import json
from pathlib import Path
import subprocess
import sys

def get_workspace_path():
    """
    获取工作区路径，支持用户输入或使用默认值
    """
    default_path = "~/workspace"
    print(f"📁 请输入要扫描的工作区路径 (默认: {default_path}):")
    user_input = input("路径: ").strip()
    
    if not user_input:
        workspace_path = Path(default_path)
    else:
        workspace_path = Path(user_input).expanduser().resolve()
    
    if not workspace_path.exists():
        print(f"❌ 路径不存在: {workspace_path}")
        return None
    
    if not workspace_path.is_dir():
        print(f"❌ 路径不是目录: {workspace_path}")
        return None
    
    print(f"✅ 使用工作区路径: {workspace_path}")
    return workspace_path

def volta_project_checker(workspace_path=None):
    """
    检查指定目录下所有包含 volta 字段的 package.json 文件
    排除 node_modules 目录，输出目录路径和 volta 配置值
    
    Args:
        workspace_path: 要扫描的工作区路径，如果为None则提示用户输入
    """
    if workspace_path is None:
        workspace_path = get_workspace_path()
        if workspace_path is None:
            return []
    
    volta_projects = []
    
    print("🔍 正在扫描 volta 项目...")
    print("=" * 60)
    
    # 遍历所有 package.json 文件，排除 node_modules
    for package_json in workspace_path.rglob("package.json"):
        # 跳过 node_modules 目录
        if "node_modules" in package_json.parts:
            continue
            
        try:
            with open(package_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # 检查是否包含 volta 字段
            if 'volta' in data:
                project_dir = package_json.parent
                volta_config = data['volta']
                
                volta_projects.append({
                    'directory': str(project_dir),
                    'volta': volta_config
                })
                
                print(f"📁 目录: {project_dir}")
                print(f"⚡ Volta 配置: {json.dumps(volta_config, indent=2)}")
                print("-" * 60)
                
        except (json.JSONDecodeError, FileNotFoundError, PermissionError) as e:
            # 忽略无法读取或解析的文件
            continue
    
    print(f"\n✅ 总共找到 {len(volta_projects)} 个包含 volta 配置的项目")
    
    # 将结果保存为 JSON 文件
    import datetime
    current_dir = Path(__file__).parent
    output_file = current_dir / "volta_projects.json"
    
    # 添加扫描时间信息
    result = {
        "scan_time": datetime.datetime.now().isoformat(),
        "scan_path": str(workspace_path),
        "total_projects": len(volta_projects),
        "projects": volta_projects
    }
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"💾 结果已保存到: {output_file}")
    except Exception as e:
        print(f"❌ 保存文件失败: {e}")
    
    return volta_projects

def get_volta_json_path():
    """
    获取 volta_projects.json 文件路径
    """
    
    current_dir = Path(__file__).parent
    default_file = current_dir / "volta_projects.json"
    
    print(f"📄 请输入 volta_projects.json 文件路径 (默认: {default_file}):")
    user_input = input("文件路径: ").strip()
    
    if not user_input:
        volta_json_file = default_file
    else:
        volta_json_file = Path(user_input).expanduser().resolve()
    
    return volta_json_file

def convert_volta_to_fnm(volta_json_file=None):
    """
    将 volta 配置转换为 fnm + engines 配置
    1. 读取 volta_projects.json 文件
    2. 将 package.json 中的 volta 字段替换为 engines 字段
    3. 使用 fnm 安装和切换对应的 Node.js 版本
    
    Args:
        volta_json_file: volta_projects.json 文件路径，如果为None则提示用户输入
    """
    
    if volta_json_file is None:
        volta_json_file = get_volta_json_path()
    
    # 检查 volta_projects.json 是否存在
    if not volta_json_file.exists():
        print("❌ volta_projects.json 文件不存在，请先运行 volta_project_checker()")
        return
    
    # 读取 volta 项目数据
    try:
        with open(volta_json_file, "r", encoding="utf-8") as f:
            volta_projects = json.load(f)
    except Exception as e:
        print(f"❌ 读取 volta_projects.json 失败: {e}")
        return
    
    projects = volta_projects.get("projects", [])
    total_projects = len(projects)
    
    if total_projects == 0:
        print("ℹ️ 没有找到需要转换的项目")
        return
    
    print(f"🔄 开始转换 {total_projects} 个项目的 volta 配置到 fnm...")
    print("=" * 60)
    
    # 用户确认
    response = input(f"⚠️ 即将修改 {total_projects} 个项目的 package.json 文件，是否继续？ (y/N): ")
    if response.lower() not in ['y', 'yes']:
        print("❌ 用户取消操作")
        return
    
    successful_conversions = 0
    failed_conversions = 0
    
    for i, project in enumerate(projects, 1):
        project_dir = Path(project["directory"])
        package_json = project_dir / "package.json"
        volta_config = project.get("volta", {})
        
        print(f"\n[{i}/{total_projects}] 处理项目: {project_dir}")
        
        # 检查 package.json 是否存在
        if not package_json.exists():
            print(f"❌ {package_json} 不存在")
            failed_conversions += 1
            continue
        
        try:
            # 读取 package.json
            with open(package_json, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # 获取 node 版本
            node_version = volta_config.get("node")
            if not node_version:
                print(f"❌ 没有找到 node 版本配置")
                failed_conversions += 1
                continue
            
            # 删除 volta 字段
            if "volta" in data:
                del data["volta"]
                print(f"🗑️ 已删除 volta 字段")
            
            # 添加或更新 engines 字段
            if "engines" not in data:
                data["engines"] = {}
            
            data["engines"]["node"] = node_version
            print(f"⚡ 设置 engines.node = {node_version}")
            
            # 如果 volta 配置中有 yarn，也添加到 engines
            if "yarn" in volta_config:
                data["engines"]["yarn"] = volta_config["yarn"]
                print(f"📦 设置 engines.yarn = {volta_config['yarn']}")
            
            # 写入更新后的 package.json
            with open(package_json, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ {package_json.name} 已更新")
            
            # 使用 fnm 安装 Node.js 版本
            print(f"📥 安装 Node.js {node_version}...")
            try:
                result = subprocess.run(
                    ["fnm", "install", node_version], 
                    cwd=project_dir,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                if result.returncode == 0:
                    print(f"✅ Node.js {node_version} 安装成功")
                else:
                    print(f"⚠️ fnm install 警告: {result.stderr.strip()}")
            except subprocess.TimeoutExpired:
                print(f"⚠️ fnm install 超时，请手动执行: fnm install {node_version}")
            except FileNotFoundError:
                print(f"⚠️ fnm 命令未找到，请确保已安装 fnm")
            except Exception as e:
                print(f"⚠️ fnm install 执行失败: {e}")
            
            # 切换到指定的 Node.js 版本
            print(f"🔄 切换到 Node.js {node_version}...")
            try:
                result = subprocess.run(
                    ["fnm", "use", node_version], 
                    cwd=project_dir,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode == 0:
                    print(f"✅ 已切换到 Node.js {node_version}")
                else:
                    print(f"⚠️ fnm use 警告: {result.stderr.strip()}")
            except subprocess.TimeoutExpired:
                print(f"⚠️ fnm use 超时，请手动执行: fnm use {node_version}")
            except FileNotFoundError:
                print(f"⚠️ fnm 命令未找到，请确保已安装 fnm")
            except Exception as e:
                print(f"⚠️ fnm use 执行失败: {e}")
            
            print(f"✅ 项目 {project_dir.name} 转换完成")
            successful_conversions += 1
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON 解析失败: {e}")
            failed_conversions += 1
        except Exception as e:
            print(f"❌ 处理项目失败: {e}")
            failed_conversions += 1
    
    # 输出转换结果统计
    print("\n" + "=" * 60)
    print(f"🎉 转换完成!")
    print(f"✅ 成功转换: {successful_conversions} 个项目")
    if failed_conversions > 0:
        print(f"❌ 转换失败: {failed_conversions} 个项目")
    print(f"📊 总计处理: {total_projects} 个项目")
    
    if successful_conversions > 0:
        print("\n💡 提示:")
        print("- 每个项目的 volta 字段已被移除")
        print("- engines 字段已添加相应的 Node.js 版本")
        print("- 建议在每个项目目录下运行 'fnm use' 来确认版本切换")
        print("- 可以使用 'node -v' 检查当前 Node.js 版本")

def show_menu():
    """
    显示操作菜单
    """
    print("\n🚀 Volta 到 FNM 迁移工具")
    print("=" * 50)
    print("请选择操作:")
    print("1. 扫描 volta 项目 (checker)")
    print("2. 转换 volta 到 fnm (convert)")
    print("3. 完整流程 (扫描 + 转换)")
    print("0. 退出")
    print("=" * 50)

def main():
    """
    主函数 - 提供交互式菜单选择功能
    """
    while True:
        show_menu()
        
        try:
            choice = input("请输入选项 (0-3): ").strip()
            
            if choice == "0":
                print("👋 再见!")
                sys.exit(0)
                
            elif choice == "1":
                print("\n📊 开始扫描 volta 项目...")
                print("-" * 30)
                workspace_path = get_workspace_path()
                if workspace_path:
                    volta_project_checker(workspace_path)
                
            elif choice == "2":
                print("\n🔄 开始转换 volta 配置...")
                print("-" * 30)
                volta_json_file = get_volta_json_path()
                convert_volta_to_fnm(volta_json_file)
                
            elif choice == "3":
                print("\n🔄 开始完整流程...")
                print("-" * 30)
                
                # 第一步：扫描项目
                print("第1步: 扫描 volta 项目")
                workspace_path = get_workspace_path()
                if not workspace_path:
                    continue
                    
                volta_projects = volta_project_checker(workspace_path)
                if not volta_projects:
                    print("❌ 没有找到 volta 项目，流程结束")
                    continue
                
                # 询问是否继续转换
                print(f"\n找到 {len(volta_projects)} 个 volta 项目")
                continue_convert = input("是否继续执行转换？ (y/N): ").strip().lower()
                
                if continue_convert in ['y', 'yes']:
                    print("\n第2步: 转换 volta 配置")
                    # 使用刚生成的JSON文件
                    current_dir = Path(__file__).parent
                    volta_json_file = current_dir / "volta_projects.json"
                    convert_volta_to_fnm(volta_json_file)
                else:
                    print("⏸️ 用户选择跳过转换步骤")
                    
            else:
                print("❌ 无效选项，请重新输入")
                
        except KeyboardInterrupt:
            print("\n\n👋 用户中断，再见!")
            sys.exit(0)
        except Exception as e:
            print(f"❌ 发生错误: {e}")
            
        # 询问是否继续
        if choice in ["1", "2", "3"]:
            continue_choice = input("\n是否继续使用工具？ (Y/n): ").strip().lower()
            if continue_choice in ['n', 'no']:
                print("👋 再见!")
                break

def parse_args():
    """
    解析命令行参数
    """
    
    parser = argparse.ArgumentParser(
        description="Volta 到 FNM 迁移工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python index.py                          # 交互式菜单模式
  python index.py --checker               # 仅扫描 volta 项目
  python index.py --convert               # 仅转换 volta 配置
  python index.py --full                  # 完整流程（扫描+转换）
  python index.py --checker --path /path  # 扫描指定路径
  python index.py --convert --json /file  # 使用指定JSON文件转换
        """
    )
    
    # 操作选项（互斥）
    action_group = parser.add_mutually_exclusive_group()
    action_group.add_argument(
        "--checker", "-c", 
        action="store_true", 
        help="扫描 volta 项目"
    )
    action_group.add_argument(
        "--convert", "-v", 
        action="store_true", 
        help="转换 volta 到 fnm"
    )
    action_group.add_argument(
        "--full", "-f", 
        action="store_true", 
        help="完整流程（扫描 + 转换）"
    )
    
    # 路径选项
    parser.add_argument(
        "--path", "-p", 
        type=str, 
        help="指定要扫描的工作区路径"
    )
    parser.add_argument(
        "--json", "-j", 
        type=str, 
        help="指定 volta_projects.json 文件路径"
    )
    
    return parser.parse_args()

def run_with_args():
    """
    根据命令行参数运行相应功能
    """
 
    args = parse_args()
    
    # 如果没有指定任何操作，进入交互模式
    if not (args.checker or args.convert or args.full):
        main()
        return
    
    try:
        if args.checker:
            print("📊 扫描 volta 项目...")
            if args.path:
                workspace_path = Path(args.path).expanduser().resolve()
                if not workspace_path.exists():
                    print(f"❌ 路径不存在: {workspace_path}")
                    sys.exit(1)
                print(f"✅ 使用指定路径: {workspace_path}")
            else:
                workspace_path = get_workspace_path()
                if not workspace_path:
                    sys.exit(1)
            
            volta_project_checker(workspace_path)
            
        elif args.convert:
            print("🔄 转换 volta 配置...")
            if args.json:
                volta_json_file = Path(args.json).expanduser().resolve()
                if not volta_json_file.exists():
                    print(f"❌ JSON文件不存在: {volta_json_file}")
                    sys.exit(1)
                print(f"✅ 使用指定JSON文件: {volta_json_file}")
            else:
                volta_json_file = get_volta_json_path()
            
            convert_volta_to_fnm(volta_json_file)
            
        elif args.full:
            print("🔄 完整流程...")
            
            # 第一步：扫描
            if args.path:
                workspace_path = Path(args.path).expanduser().resolve()
                if not workspace_path.exists():
                    print(f"❌ 路径不存在: {workspace_path}")
                    sys.exit(1)
            else:
                workspace_path = get_workspace_path()
                if not workspace_path:
                    sys.exit(1)
            
            print("第1步: 扫描 volta 项目")
            volta_projects = volta_project_checker(workspace_path)
            if not volta_projects:
                print("❌ 没有找到 volta 项目，流程结束")
                sys.exit(1)
            
            # 第二步：转换
            continue_convert = input(f"\n找到 {len(volta_projects)} 个 volta 项目，是否继续执行转换？ (y/N): ").strip().lower() in ['y', 'yes']
            
            if continue_convert:
                print("第2步: 转换 volta 配置")
                current_dir = Path(__file__).parent
                volta_json_file = current_dir / "volta_projects.json"
                convert_volta_to_fnm(volta_json_file)
            else:
                print("⏸️ 用户选择跳过转换步骤")
                
    except KeyboardInterrupt:
        print("\n\n👋 用户中断，再见!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_with_args()
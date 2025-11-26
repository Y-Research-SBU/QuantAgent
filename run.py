#!/usr/bin/env python3
"""
ElonQuantAgent 启动脚本
支持多厂商API和数据源
"""

import argparse
import os
import sys
from pathlib import Path
try:
    from dotenv import load_dotenv
    load_dotenv()  # 加载.env文件中的环境变量
except ImportError:
    print("ℹ️  提示: 未安装python-dotenv，将使用系统环境变量")

def check_requirements():
    """检查必要的环境变量"""
    print("🔍 检查环境变量...")
    
    required_vars = []
    
    # 检查至少一个LLM API密钥
    llm_keys = [
        os.environ.get("OPENAI_API_KEY"),
        os.environ.get("DEEPSEEK_API_KEY")
    ]
    
    if not any(key and key != f"your-{provider}-api-key-here" 
               for provider, key in zip(['openai', 'deepseek'], llm_keys)):
        print("⚠️  警告: 未设置LLM API密钥")
        print("   请设置以下环境变量之一:")
        print("   - OPENAI_API_KEY (OpenAI API密钥)")
        print("   - DEEPSEEK_API_KEY (DeepSeek API密钥)")
        required_vars.append("LLM_API_KEY")
    
    # 检查数据源API密钥（可选）
    finnhub_key = os.environ.get("FINNHUB_API_KEY")
    if not finnhub_key or finnhub_key == "your-finnhub-api-key-here":
        print("ℹ️  提示: 未设置Finnhub API密钥，将仅使用akshare数据源")
    
    return len(required_vars) == 0

def install_requirements():
    """安装依赖"""
    print("📦 安装依赖包...")
    try:
        import subprocess
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ 依赖安装失败: {result.stderr}")
            return False
        print("✅ 依赖安装成功")
        return True
    except Exception as e:
        print(f"❌ 安装依赖时出错: {e}")
        return False

def setup_data_directories():
    """设置数据目录"""
    print("📁 创建数据目录...")
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    # 创建自定义资产文件（如果不存在）
    custom_assets = data_dir / "custom_assets.json"
    if not custom_assets.exists():
        with open(custom_assets, 'w', encoding='utf-8') as f:
            f.write('[]')
    
    print("✅ 数据目录设置完成")

def start_web_interface(port=5001):
    """启动Web界面"""
    print(f"🚀 启动Web交易分析界面...")
    print(f"   访问地址: http://127.0.0.1:{port}")
    print("   按 Ctrl+C 停止服务")
    print("\n" + "="*50)
    
    try:
        from web_interface_new import app
        app.run(debug=True, host='127.0.0.1', port=port)
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("请确保已安装所有依赖")
        return False
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        return False
    return True

def main():
    """主函数"""
    print("🤖 ElonQuantAgent - 多厂商API量化交易分析系统")
    print("="*50)
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='ElonQuantAgent')
    parser.add_argument('--port', type=int, default=5001, help='Server port (default: 5001)')
    args = parser.parse_args()
    
    # 检查环境变量
    if not check_requirements():
        print("\n❌ 请先设置必要的环境变量")
        sys.exit(1)
    
    # 安装依赖
    if not install_requirements():
        print("\n❌ 依赖安装失败，请手动运行: pip install -r requirements.txt")
        sys.exit(1)
    
    # 设置数据目录
    setup_data_directories()
    
    print("\n✅ 准备就绪！")
    print("可用数据源:")
    
    
    # 启动Web界面
    start_web_interface(args.port)

if __name__ == "__main__":
    main()
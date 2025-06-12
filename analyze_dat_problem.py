import re
import numpy as np

# 分析DAT文件中的问题
dat_file = '/Users/lihuazhen/Downloads/Diamond_Pipeline/Diamond_Pipeline/Data_link/DWF_Huazhen_c4/1e-3/1e-3_000010_des.dat'

print("=== 分析DAT文件中的权重势问题 ===")
print(f"文件: {dat_file}")

with open(dat_file, 'r') as f:
    content = f.read()

# 先查看文件结构
print("\n=== 文件结构预览 ===")
lines = content.split('\n')
for i, line in enumerate(lines[:50]):
    if 'ElectrostaticPotential' in line or 'validity' in line or 'Values' in line:
        print(f"行 {i+1}: {line.strip()}")

# 使用更宽松的正则表达式
print("\n=== 查找ElectrostaticPotential数据段 ===")
# 分步骤查找
dataset_pattern = r'Dataset \("ElectrostaticPotential"\)'
dataset_matches = re.finditer(dataset_pattern, content)

dataset_positions = []
for match in dataset_matches:
    dataset_positions.append(match.start())

print(f"找到 {len(dataset_positions)} 个ElectrostaticPotential数据段")

# 分析每个数据段
for i, start_pos in enumerate(dataset_positions):
    print(f"\n=== 数据段 {i+1} ===")
    
    # 找到这个数据段的结束位置
    if i < len(dataset_positions) - 1:
        end_pos = dataset_positions[i+1]
    else:
        end_pos = len(content)
    
    segment = content[start_pos:end_pos]
    
    # 查找validity信息
    validity_match = re.search(r'validity = \[ "([^"]+)" \]', segment)
    if validity_match:
        region = validity_match.group(1)
        print(f"区域: {region}")
    else:
        print("区域: 未知")
    
    # 查找Values数据
    values_match = re.search(r'Values \(([0-9]+)\) \{(.*?)\}', segment, re.DOTALL)
    if values_match:
        count = int(values_match.group(1))
        values_text = values_match.group(2)
        print(f"数值数量: {count:,}")
        
        # 提取前1000个数值进行分析
        values = []
        lines_processed = 0
        for line in values_text.strip().split('\n'):
            line = line.strip()
            if line and not line.startswith('}') and lines_processed < 100:  # 只处理前100行
                lines_processed += 1
                nums = line.split()
                for num in nums:
                    try:
                        val = float(num)
                        values.append(val)
                        if len(values) >= 1000:  # 最多1000个样本
                            break
                    except:
                        pass
                if len(values) >= 1000:
                    break
        
        if values:
            values = np.array(values)
            print(f"分析样本: {len(values):,}")
            print(f"数值范围: {np.min(values):.6e} 到 {np.max(values):.6e}")
            print(f"平均值: {np.mean(values):.6e}")
            
            # 分析数值分布
            close_to_zero = np.sum(np.abs(values) < 1e-10)
            close_to_one = np.sum((values > 0.9) & (values <= 1.1))
            in_zero_one = np.sum((values >= 0) & (values <= 1))
            negative_values = np.sum(values < 0)
            
            print(f"接近0的值 (±1e-10): {close_to_zero:,} ({100*close_to_zero/len(values):.1f}%)")
            print(f"接近1的值 (0.9-1.1): {close_to_one:,} ({100*close_to_one/len(values):.1f}%)")
            print(f"0-1范围内的值: {in_zero_one:,} ({100*in_zero_one/len(values):.1f}%)")
            print(f"负值: {negative_values:,} ({100*negative_values/len(values):.1f}%)")
            
            # 显示样本值
            print(f"前10个值: {values[:10]}")
            
            # 判断数据类型
            if close_to_zero > len(values) * 0.8:
                print("❌ 问题: 这主要是数值噪声数据！")
                if validity_match and 'BULK' in validity_match.group(1):
                    print("🚨 严重问题: BULK区域的权重势是数值噪声！")
            elif close_to_one > 10 and in_zero_one > len(values) * 0.8:
                print("✅ 正常: 这是正确的权重势数据")
            elif np.all(np.abs(values - values[0]) < 1e-10):
                print(f"📌 常数: 所有值都是 {values[0]}")
            else:
                print("❓ 未知: 数据分布不明确")

print("\n" + "="*80)
print("=== 对比分析：TDR vs DAT ===")
print()
print("🎯 TDR文件中的正确数据 (dataset_1):")
print("   - 116,197个元素")
print("   - 数值范围: 0.000 到 1.000")
print("   - 9,802个接近1.0的值")
print("   - 94.8%的值在0-1范围内")
print("   - 平均值: 0.479 (合理的权重势分布)")
print()
print("❌ DAT文件中的问题:")
print("   - BULK区域主要是数值噪声 (~2.6e-16)")
print("   - 缺少正确的0-1权重势分布")
print("   - Garfield++读取这些噪声数据，导致权重势几乎为0")
print("   - 结果：载流子漂移时感应信号 ≈ 0")
print()
print("💡 解决方案:")
print("   1. 重新使用tdx转换TDR文件")
print("   2. 确保转换时提取dataset_1的数据到BULK区域")
print("   3. 验证转换后BULK区域有正确的权重势分布") 
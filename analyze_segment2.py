import re
import numpy as np

# 专门分析数据段2的权重势数据
dat_file = '/Users/lihuazhen/Downloads/Diamond_Pipeline/Diamond_Pipeline/Data_link/DWF_Huazhen_c4/1e-3/1e-3_000010_des.dat'

print("=== 详细分析数据段2的权重势数据 ===")
print(f"文件: {dat_file}")

with open(dat_file, 'r') as f:
    content = f.read()

# 找到第2个ElectrostaticPotential数据段
dataset_pattern = r'Dataset \("ElectrostaticPotential"\) \{'
matches = list(re.finditer(dataset_pattern, content))

if len(matches) >= 2:
    # 获取第2个数据段
    start_pos = matches[1].start()
    if len(matches) >= 3:
        end_pos = matches[2].start()
    else:
        # 找下一个Dataset
        next_dataset = re.search(r'Dataset \("(?!ElectrostaticPotential)[^"]+"\) \{', content[start_pos:])
        if next_dataset:
            end_pos = start_pos + next_dataset.start()
        else:
            end_pos = len(content)
    
    segment = content[start_pos:end_pos]
    
    # 查找validity信息
    validity_match = re.search(r'validity = \[ "([^"]+)" \]', segment)
    region = validity_match.group(1) if validity_match else "未知"
    print(f"\n区域: {region}")
    
    # 查找Values数据
    values_match = re.search(r'Values \(([0-9]+)\) \{(.*?)\}', segment, re.DOTALL)
    if values_match:
        count = int(values_match.group(1))
        values_text = values_match.group(2)
        print(f"数值数量: {count:,}")
        
        # 提取更多数值进行详细分析
        values = []
        lines_processed = 0
        for line in values_text.strip().split('\n'):
            line = line.strip()
            if line and not line.startswith('}'):
                lines_processed += 1
                if lines_processed <= 500:  # 处理前500行，获得更多样本
                    nums = line.split()
                    for num in nums:
                        try:
                            val = float(num)
                            values.append(val)
                        except:
                            pass
        
        if values:
            values = np.array(values)
            print(f"\n=== 详细统计分析 ===")
            print(f"分析样本: {len(values):,}")
            print(f"数值范围: {np.min(values):.6e} 到 {np.max(values):.6e}")
            print(f"平均值: {np.mean(values):.6f}")
            print(f"中位数: {np.median(values):.6f}")
            print(f"标准差: {np.std(values):.6f}")
            
            # 详细的数值分布分析
            print(f"\n=== 数值分布分析 ===")
            
            # 不同范围的值统计
            noise_values = np.sum(np.abs(values) < 1e-10)
            very_small = np.sum((np.abs(values) >= 1e-10) & (np.abs(values) < 1e-6))
            small_values = np.sum((values >= 1e-6) & (values < 0.1))
            mid_values = np.sum((values >= 0.1) & (values < 0.9))
            close_to_one = np.sum((values >= 0.9) & (values <= 1.1))
            above_one = np.sum(values > 1.1)
            negative_values = np.sum(values < 0)
            
            print(f"数值噪声 (<1e-10): {noise_values:,} ({100*noise_values/len(values):.1f}%)")
            print(f"极小值 (1e-10 to 1e-6): {very_small:,} ({100*very_small/len(values):.1f}%)")
            print(f"小值 (1e-6 to 0.1): {small_values:,} ({100*small_values/len(values):.1f}%)")
            print(f"中间值 (0.1 to 0.9): {mid_values:,} ({100*mid_values/len(values):.1f}%)")
            print(f"接近1 (0.9 to 1.1): {close_to_one:,} ({100*close_to_one/len(values):.1f}%)")
            print(f"大于1 (>1.1): {above_one:,} ({100*above_one/len(values):.1f}%)")
            print(f"负值: {negative_values:,} ({100*negative_values/len(values):.1f}%)")
            
            # 权重势质量评估
            print(f"\n=== 权重势质量评估 ===")
            
            # 0-1范围内的值
            in_zero_one = np.sum((values >= 0) & (values <= 1))
            print(f"0-1范围内的值: {in_zero_one:,} ({100*in_zero_one/len(values):.1f}%)")
            
            # 检查是否有合理的梯度分布
            if mid_values > len(values) * 0.1:  # 至少10%的中间值
                print("✅ 有合理的中间值分布，表明存在权重势梯度")
            else:
                print("⚠️  中间值较少，可能缺少平滑的权重势梯度")
            
            if close_to_one > len(values) * 0.1:  # 至少10%接近1
                print("✅ 有足够的接近1的值，表明电极区域正确")
            else:
                print("⚠️  接近1的值较少，电极区域可能有问题")
            
            if noise_values < len(values) * 0.5:  # 噪声少于50%
                print("✅ 数值噪声在可接受范围内")
            else:
                print("❌ 数值噪声过多，影响权重势质量")
            
            # 显示数值分布的样本
            print(f"\n=== 数值样本 ===")
            print(f"前20个值: {values[:20]}")
            print(f"中间20个值: {values[len(values)//2:len(values)//2+20]}")
            print(f"后20个值: {values[-20:]}")
            
            # 统计不同数值区间的分布
            print(f"\n=== 数值区间分布 ===")
            bins = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
            hist, _ = np.histogram(values[values >= 0], bins=bins)
            for i in range(len(bins)-1):
                print(f"{bins[i]:.1f}-{bins[i+1]:.1f}: {hist[i]:,} 个值")
            
            # 最终评估
            print(f"\n=== 最终评估 ===")
            if (in_zero_one > len(values) * 0.8 and 
                mid_values > len(values) * 0.1 and 
                close_to_one > len(values) * 0.1 and
                noise_values < len(values) * 0.5):
                print("🎯 这是正确的权重势数据！")
                print("   - 大部分值在0-1范围内")
                print("   - 有合理的梯度分布")
                print("   - 有足够的电极区域值")
                print("   - 数值噪声在可接受范围内")
            else:
                print("❓ 权重势数据质量需要进一步检查")
                
        else:
            print("无法提取数值数据")
    else:
        print("未找到Values数据")
else:
    print("未找到第2个ElectrostaticPotential数据段") 